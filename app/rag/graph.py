import json
from typing import Dict, Any, List, TypedDict, Optional
import google.generativeai as genai
import httpx
from langgraph.graph import StateGraph, END
from app.core.config import settings
from app.core.logging import logger
from app.rag.hybrid_retriever import hybrid_retriever
from app.rag.reranker import reranker
from app.rag.prompts import EXAM_GENERATION_SYSTEM_PROMPT, EXAM_GENERATION_USER_PROMPT
from app.schemas.exam import GeneratedExam

def extract_and_parse_json(text: str) -> Dict[str, Any]:
    text = text.strip()
    # Remove markdown code blocks if present
    if text.startswith("```"):
        parts = text.split("```")
        for part in parts:
            part_clean = part.strip()
            if part_clean.startswith("json"):
                part_clean = part_clean[4:].strip()
            if part_clean.startswith("{") or part_clean.startswith("["):
                try:
                    return json.loads(part_clean)
                except Exception:
                    pass
    
    # Try finding the first '{' and last '}'
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        candidate = text[first_brace:last_brace+1]
        try:
            return json.loads(candidate)
        except Exception:
            pass
            
    # Try direct parse
    return json.loads(text)

class RAGState(TypedDict):
    lesson_id: str
    lesson_parents: Dict[str, Any]
    exam_title: str
    distribution: Dict[str, int]
    difficulty: Dict[str, int]
    retrieved_chunks: List[Dict[str, Any]]
    reranked_chunks: List[Dict[str, Any]]
    constructed_prompt: str
    generated_json: Dict[str, Any]
    generated_exam: Any
    gemini_api_key: Optional[str]
    error: str

class LangGraphRAGPipeline:
    """LangGraph State Graph Orchestration for Arabic Exam Generation."""

    def __init__(self):
        self._llm = None
        self.graph = self._build_graph()

    @property
    def llm(self):
        if self._llm is None:
            self.api_key = settings.get_gemini_api_key()
            genai.configure(api_key=self.api_key)
            self._llm = genai.GenerativeModel(settings.LLM_MODEL)
        return self._llm

    def _retrieve_node(self, state: RAGState) -> Dict[str, Any]:
        logger.info("Executing LangGraph Node: Hybrid Retrieval", lesson_id=state["lesson_id"])
        query = f"أهم مفاهيم ومعارف {state['exam_title']} والتمارين والأسئلة المفصلة"
        retrieved = hybrid_retriever.retrieve(
            query=query,
            lesson_parents=state["lesson_parents"],
            top_k=settings.HYBRID_SEARCH_TOP_K
        )
        return {"retrieved_chunks": retrieved}

    def _rerank_node(self, state: RAGState) -> Dict[str, Any]:
        logger.info("Executing LangGraph Node: Re-ranking", candidate_count=len(state["retrieved_chunks"]))
        query = f"الدرس {state['exam_title']}"
        top_reranked = reranker.rerank(query, state["retrieved_chunks"])
        return {"reranked_chunks": top_reranked}

    def _prompt_builder_node(self, state: RAGState) -> Dict[str, Any]:
        logger.info("Executing LangGraph Node: Prompt Construction")
        # Build comprehensive context from both reranked_chunks and complete lesson_parents
        chunks = state.get("reranked_chunks", [])
        retrieved_texts = [chunk["text"] for chunk in chunks if chunk.get("text")]
        
        # Include all lesson_parents if available to ensure zero-loss coverage of uploaded lesson images
        if state.get("lesson_parents"):
            parent_texts = [p.text for p in state["lesson_parents"].values() if hasattr(p, "text") and p.text]
            # Union of retrieved texts and parent texts
            all_texts = list(dict.fromkeys(parent_texts + retrieved_texts))
        else:
            all_texts = retrieved_texts

        context_str = "\n\n---\n\n".join(all_texts)
        
        # Extract user requested difficulty counts
        easy_cnt = state.get("easy_count", 2)
        medium_cnt = state.get("medium_count", 2)
        hard_cnt = state.get("hard_count", 1)

        # Extract question type counts
        dist = state.get("distribution") or {}
        num_mcq = state.get("num_mcq") if state.get("num_mcq") is not None else dist.get("num_mcq", 2)
        num_true_false = state.get("num_true_false") if state.get("num_true_false") is not None else dist.get("num_true_false", 2)
        num_short_answer = state.get("num_short_answer") if state.get("num_short_answer") is not None else dist.get("num_short_answer", 1)
        num_fill_blank = state.get("num_fill_blank") if state.get("num_fill_blank") is not None else dist.get("num_fill_blank", 0)
        num_essay = dist.get("num_essay", 0)

        # Total questions requested by user
        total_questions = num_mcq + num_true_false + num_short_answer + num_fill_blank + num_essay

        # Ensure difficulty counts sum EXACTLY to total_questions to prevent prompt conflict
        # 50% easy ("النص كويس"), 25% medium ("ربعه متوسط"), 25% hard ("ربعه صعب")
        easy_cnt = round(total_questions * 0.5)
        medium_cnt = round(total_questions * 0.25)
        hard_cnt = max(0, total_questions - (easy_cnt + medium_cnt))
        diff_total = max(1, total_questions)

        user_prompt = EXAM_GENERATION_USER_PROMPT.format(
            context=context_str,
            exam_title=state["exam_title"],
            total_questions=total_questions,
            num_mcq=num_mcq,
            num_true_false=num_true_false,
            num_fill_blank=num_fill_blank,
            num_short_answer=num_short_answer,
            num_essay=num_essay,
            easy_cnt=easy_cnt,
            medium_cnt=medium_cnt,
            hard_cnt=hard_cnt,
            easy_pct=int((easy_cnt / diff_total) * 100),
            medium_pct=int((medium_cnt / diff_total) * 100),
            hard_pct=int((hard_cnt / diff_total) * 100)
        )
        return {"constructed_prompt": user_prompt}

    def _llm_generate_node(self, state: RAGState) -> Dict[str, Any]:
        logger.info("Executing LangGraph Node: LLM Generation")
        from app.rag.ollama_llm import ollama_llm
        full_prompt = f"{EXAM_GENERATION_SYSTEM_PROMPT}\n\n{state['constructed_prompt']}"

        # 1. PRIMARY: Local Ollama (free, no quota, no rate limits)
        if ollama_llm.is_available():
            try:
                logger.info("Generating Arabic Exam using Local Ollama (Primary - No Quota Limits)")
                parsed_json = ollama_llm.generate_json(state['constructed_prompt'], EXAM_GENERATION_SYSTEM_PROMPT)
                return {"generated_json": parsed_json}
            except Exception as oe:
                logger.warning("Local Ollama generation failed, falling back to Gemini", error=str(oe))

        # 2. FALLBACK 1: Gemini Cloud (with rich model fallback list)
        custom_key = state.get("gemini_api_key")
        gemini_api_key = custom_key if (custom_key and custom_key.strip()) else None
        
        if not gemini_api_key:
            try:
                gemini_api_key = settings.get_gemini_api_key()
            except Exception:
                pass
                
        def is_valid_gemini_key(key: Optional[str]) -> bool:
            if not key:
                return False
            key_strip = key.strip()
            if not key_strip or "your-gemini-api-key" in key_strip.lower() or len(key_strip) < 10:
                return False
            return True

        if is_valid_gemini_key(gemini_api_key):
            import time
            gemini_models = [
                "gemini-2.5-flash-lite",
                "gemini-2.5-flash",
                "gemini-flash-latest",
                "gemini-2.0-flash-lite",
                "gemini-3.1-flash-lite"
            ]
            
            try:
                genai.configure(api_key=gemini_api_key.strip())
            except Exception as ge:
                logger.warning("Failed to configure genai globally", error=str(ge))

            for g_model in gemini_models:
                for attempt in range(2):
                    try:
                        logger.info("Generating Arabic Exam using Gemini Cloud Fallback", model=g_model, attempt=attempt+1)
                        model_instance = genai.GenerativeModel(
                            g_model,
                            system_instruction=EXAM_GENERATION_SYSTEM_PROMPT
                        )
                        response = model_instance.generate_content(
                            state['constructed_prompt'],
                            generation_config={"response_mime_type": "application/json"}
                        )
                        parsed_json = extract_and_parse_json(response.text)
                        return {"generated_json": parsed_json}
                    except Exception as e:
                        err_str = str(e)
                        logger.warning(f"Gemini {g_model} fallback failed (attempt {attempt+1})", error=err_str)
                        if "429" in err_str or "quota" in err_str.lower():
                            time.sleep(2)
                            continue
                        else:
                            break

        # 3. FALLBACK 2: Groq Cloud
        import os
        groq_api_key = os.getenv("GROQ_API_KEY")
        groq_url = "https://api.groq.com/openai/v1/chat/completions"
        groq_models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
        
        for g_model in groq_models:
            try:
                logger.info("Generating Arabic Exam using Groq Fallback", model=g_model)
                payload = {
                    "model": g_model,
                    "messages": [
                        {"role": "system", "content": EXAM_GENERATION_SYSTEM_PROMPT},
                        {"role": "user", "content": state['constructed_prompt']}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 4000,
                    "response_format": {"type": "json_object"}
                }
                headers = {
                    "Authorization": f"Bearer {groq_api_key}" if groq_api_key else "",
                    "Content-Type": "application/json"
                }
                res = httpx.post(groq_url, json=payload, headers=headers, timeout=45.0)
                if res.status_code == 200:
                    resp_json = res.json()
                    content = resp_json["choices"][0]["message"]["content"]
                    parsed = extract_and_parse_json(content)
                    return {"generated_json": parsed}
                else:
                    logger.warning(f"Groq API returned error status {res.status_code}", body=res.text)
            except Exception as e:
                logger.warning(f"Groq fallback failed for model {g_model}", error=str(e))

        # 4. FALLBACK 3: OpenRouter Cloud
        or_api_key = os.getenv("OPENROUTER_API_KEY")
        or_url = "https://openrouter.ai/api/v1/chat/completions"
        or_models = [
            "google/gemini-2.5-flash",
            "meta-llama/llama-3.3-70b-instruct",
            "meta-llama/llama-3.1-8b-instruct:free",
            "qwen/qwen-2.5-7b-instruct:free",
            "google/gemma-2-9b-it:free"
        ]
        
        for or_model in or_models:
            try:
                logger.info("Generating Arabic Exam using OpenRouter Fallback", model=or_model)
                payload = {
                    "model": or_model,
                    "messages": [
                        {"role": "system", "content": EXAM_GENERATION_SYSTEM_PROMPT},
                        {"role": "user", "content": state['constructed_prompt']}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 4000,
                    "response_format": {"type": "json_object"}
                }
                headers = {
                    "Authorization": f"Bearer {or_api_key}" if or_api_key else "",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://ahmed792-arabic-quiz-maker.hf.space/",
                    "X-Title": "Arabic Quiz Maker"
                }
                res = httpx.post(or_url, json=payload, headers=headers, timeout=45.0)
                if res.status_code == 200:
                    resp_json = res.json()
                    content = resp_json["choices"][0]["message"]["content"]
                    parsed = extract_and_parse_json(content)
                    return {"generated_json": parsed}
                else:
                    logger.warning(f"OpenRouter API returned error status {res.status_code}", body=res.text)
            except Exception as e:
                logger.warning(f"OpenRouter fallback failed for model {or_model}", error=str(e))

        # 5. FALLBACK 4: Mistral Cloud
        mistral_api_key = os.getenv("MISTRAL_API_KEY")
        mistral_url = "https://api.mistral.ai/v1/chat/completions"
        mistral_models = ["mistral-large-latest", "mistral-small-latest"]
        
        for m_model in mistral_models:
            try:
                logger.info("Generating Arabic Exam using Mistral Fallback", model=m_model)
                payload = {
                    "model": m_model,
                    "messages": [
                        {"role": "system", "content": EXAM_GENERATION_SYSTEM_PROMPT},
                        {"role": "user", "content": state['constructed_prompt']}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 4000,
                    "response_format": {"type": "json_object"}
                }
                headers = {
                    "Authorization": f"Bearer {mistral_api_key}" if mistral_api_key else "",
                    "Content-Type": "application/json"
                }
                res = httpx.post(mistral_url, json=payload, headers=headers, timeout=45.0)
                if res.status_code == 200:
                    resp_json = res.json()
                    content = resp_json["choices"][0]["message"]["content"]
                    parsed = extract_and_parse_json(content)
                    return {"generated_json": parsed}
                else:
                    logger.warning(f"Mistral API returned error status {res.status_code}", body=res.text)
            except Exception as e:
                logger.warning(f"Mistral fallback failed for model {m_model}", error=str(e))

        # 6. FALLBACK 5: Cohere Cloud
        cohere_api_key = os.getenv("COHERE_API_KEY")
        cohere_url = "https://api.cohere.com/v2/chat"
        cohere_models = ["command-r-plus-08-2024", "command-r-plus"]
        
        for c_model in cohere_models:
            try:
                logger.info("Generating Arabic Exam using Cohere Fallback", model=c_model)
                payload = {
                    "model": c_model,
                    "messages": [
                        {"role": "system", "content": EXAM_GENERATION_SYSTEM_PROMPT},
                        {"role": "user", "content": state['constructed_prompt']}
                    ],
                    "max_tokens": 4000,
                    "response_format": {"type": "json_object"}
                }
                headers = {
                    "Authorization": f"Bearer {cohere_api_key}" if cohere_api_key else "",
                    "Content-Type": "application/json"
                }
                res = httpx.post(cohere_url, json=payload, headers=headers, timeout=45.0)
                if res.status_code == 200:
                    resp_json = res.json()
                    content = resp_json["message"]["content"]
                    raw_text = ""
                    if isinstance(content, list):
                        raw_text = content[0].get("text", "")
                    elif isinstance(content, dict):
                        raw_text = content.get("text", "")
                    else:
                        raw_text = str(content)
                    parsed = extract_and_parse_json(raw_text)
                    return {"generated_json": parsed}
                else:
                    logger.warning(f"Cohere API returned error status {res.status_code}", body=res.text)
            except Exception as e:
                logger.warning(f"Cohere fallback failed for model {c_model}", error=str(e))

        return {"error": "LLM Exam generation failed across all providers."}

    def _validate_node(self, state: RAGState) -> Dict[str, Any]:
        logger.info("Executing LangGraph Node: Pydantic Schema Validation")
        if "error" in state and state["error"]:
            return {}
        try:
            raw_data = state["generated_json"]
            raw_data["exam_id"] = raw_data.get("exam_id") or f"exam_{state['lesson_id']}"
            raw_data["lesson_id"] = state["lesson_id"]
            
            valid_types = {"mcq", "true_false", "fill_in_blank", "short_answer", "essay"}
            valid_diffs = {"easy", "medium", "hard"}
            
            questions = raw_data.get("questions", [])
            
            # Strict enforcement of requested total count
            num_mcq = state.get("num_mcq") if state.get("num_mcq") is not None else 10
            num_tf = state.get("num_true_false") if state.get("num_true_false") is not None else 5
            num_sa = state.get("num_short_answer") if state.get("num_short_answer") is not None else 5
            num_fb = state.get("num_fill_blank") if state.get("num_fill_blank") is not None else 0

            easy_cnt = state.get("easy_count") if state.get("easy_count") is not None else 10
            medium_cnt = state.get("medium_count") if state.get("medium_count") is not None else 5
            hard_cnt = state.get("hard_count") if state.get("hard_count") is not None else 5

            target_total = num_mcq + num_tf + num_sa + num_fb
            if target_total <= 0:
                target_total = max(1, easy_cnt + medium_cnt + hard_cnt)

            # Programmatic deduplication based on normalized question text
            seen_questions = set()
            unique_questions = []
            for q in questions:
                q_text = str(q.get("question_text") or q.get("stem") or "").strip()
                if not q_text:
                    continue
                import re
                norm = q_text.lower()
                norm = re.sub(r'[\u064B-\u0652]', '', norm)  # Remove diacritics
                norm = re.sub(r'[أإآ]', 'ا', norm)
                norm = re.sub(r'ة', 'ه', norm)
                norm = re.sub(r'ى', 'ي', norm)
                norm = re.sub(r'[^\w\s]', '', norm)
                norm = re.sub(r'\s+', '', norm)  # Collapse spaces
                
                if norm not in seen_questions:
                    seen_questions.add(norm)
                    unique_questions.append(q)
                else:
                    logger.info("Removed duplicate question generated by LLM", question=q_text)
            
            questions = unique_questions
            raw_data["questions"] = questions

            if len(questions) > target_total:
                logger.info(f"Truncating LLM questions from {len(questions)} to requested {target_total}")
                questions = questions[:target_total]
                raw_data["questions"] = questions
            
            for q in questions:
                # Force clean sequential IDs
                q["id"] = f"q_{questions.index(q) + 1}"

                # Normalize question_type
                q_type = str(q.get("question_type", "")).lower().strip()
                for vt in valid_types:
                    if vt in q_type:
                        q["question_type"] = vt
                        break
                if q.get("question_type") not in valid_types:
                    q["question_type"] = "mcq"

                # Normalize difficulty
                diff = str(q.get("difficulty", "")).lower().strip()
                for vd in valid_diffs:
                    if vd in diff:
                        q["difficulty"] = vd
                        break
                if q.get("difficulty") not in valid_diffs:
                    q["difficulty"] = "easy"

                # Normalize question_text
                q["question_text"] = str(q.get("question_text") or q.get("stem") or "")

                # Normalize correct_answer (convert bool/numbers/etc. to string)
                correct = q.get("correct_answer") or q.get("model_answer")
                if correct is not None:
                    if isinstance(correct, bool):
                        q["correct_answer"] = "صح" if correct else "خطأ"
                    else:
                        correct_str = str(correct).strip()
                        if q["question_type"] == "true_false":
                            if correct_str.lower() in ("true", "yes", "correct", "t", "y", "1"):
                                q["correct_answer"] = "صح"
                            elif correct_str.lower() in ("false", "no", "incorrect", "f", "n", "0"):
                                q["correct_answer"] = "خطأ"
                            else:
                                q["correct_answer"] = correct_str
                        else:
                            q["correct_answer"] = correct_str
                else:
                    q["correct_answer"] = ""

                # Normalize explanation
                q["explanation"] = str(q.get("explanation") or "")

                # Normalize marks to int
                try:
                    q["marks"] = int(q.get("marks", 2))
                except Exception:
                    q["marks"] = 2

                # Normalize options for MCQ
                if q["question_type"] == "mcq":
                    options = q.get("options") or q.get("choices") or []
                    norm_opts = []
                    if isinstance(options, list):
                        for opt in options:
                            if isinstance(opt, dict):
                                opt_key = str(opt.get("key") or opt.get("id") or "").strip()
                                opt_text = str(opt.get("text") or opt.get("value") or "").strip()
                                if opt_key and opt_text:
                                    norm_opts.append({"key": opt_key, "text": opt_text})
                            elif isinstance(opt, str):
                                keys = ["أ", "ب", "ج", "د"]
                                idx = len(norm_opts)
                                key = keys[idx] if idx < len(keys) else str(idx + 1)
                                norm_opts.append({"key": key, "text": opt})
                    q["options"] = norm_opts
                else:
                    q["options"] = None
            
            validated_exam = GeneratedExam(**raw_data)
            return {"generated_exam": validated_exam}
        except Exception as e:
            logger.error("Pydantic exam validation error", error=str(e))
            return {"error": f"Validation failed: {str(e)}"}

    def _build_graph(self):
        builder = StateGraph(RAGState)

        builder.add_node("retrieve", self._retrieve_node)
        builder.add_node("rerank", self._rerank_node)
        builder.add_node("build_prompt", self._prompt_builder_node)
        builder.add_node("generate", self._llm_generate_node)
        builder.add_node("validate", self._validate_node)

        builder.set_entry_point("retrieve")
        builder.add_edge("retrieve", "rerank")
        builder.add_edge("rerank", "build_prompt")
        builder.add_edge("build_prompt", "generate")
        builder.add_edge("generate", "validate")
        builder.add_edge("validate", END)

        return builder.compile()

    def run(self, initial_state: RAGState) -> RAGState:
        logger.info("Starting LangGraph RAG Workflow Execution", lesson_id=initial_state["lesson_id"])
        final_state = self.graph.invoke(initial_state)
        return final_state

langgraph_pipeline = LangGraphRAGPipeline()
