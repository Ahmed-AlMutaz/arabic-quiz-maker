import os
import json
import httpx
from typing import Dict, Any, Optional
from app.core.config import settings
from app.core.logging import logger

# Simplified prompt that small models can handle
OLLAMA_SIMPLE_SYSTEM = """You are an Arabic exam generator. Output ONLY valid JSON. No explanations."""

OLLAMA_SIMPLE_USER = """Generate an Arabic exam from this text. Output valid JSON only.

Text: {context}

Title: {title}

Generate exactly {num_q} questions as JSON:
{{"exam_id":"exam_1","lesson_id":"lesson_1","title":"{title}","questions":[{{"id":"q1","question_type":"mcq","difficulty":"easy","question_text":"السؤال بالعربي","options":[{{"key":"أ","text":"خيار1"}},{{"key":"ب","text":"خيار2"}},{{"key":"ج","text":"خيار3"}},{{"key":"د","text":"خيار4"}}],"correct_answer":"الإجابة","explanation":"التفسير","marks":2,"context_chunk_id":"p1"}}]}}

Output ONLY the JSON object:"""

class OllamaLLM:
    """Ollama Local LLM Provider with simplified prompts for small models."""

    def __init__(self):
        self.base_url = os.environ.get("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
        # Try multiple models in order of capability
        self.models = ["qwen2.5:1.5b", "phi3:mini", "gemma3:1b"]

    def is_available(self) -> bool:
        """Checks if local Ollama instance is online."""
        for url in [self.base_url]:
            try:
                r = httpx.get(f"{url}/api/tags", timeout=3.0)
                if r.status_code == 200:
                    available = [m.get("name") for m in r.json().get("models", [])]
                    for model in self.models:
                        if any(model in m for m in available):
                            return True
            except Exception:
                pass
        return False

    def _get_available_model(self, url: str) -> Optional[str]:
        """Get first available model from our preference list."""
        try:
            r = httpx.get(f"{url}/api/tags", timeout=3.0)
            if r.status_code == 200:
                available = [m.get("name") for m in r.json().get("models", [])]
                for model in self.models:
                    if any(model in m for m in available):
                        return model
        except Exception:
            pass
        return None

    def generate_json(self, prompt: str, system_prompt: str = "") -> Dict[str, Any]:
        """Generates structured JSON using a simplified prompt for small models."""
        url = self.base_url
        model = self._get_available_model(url)
        if not model:
            raise RuntimeError("No compatible Ollama model found.")

        # Pass full prompt or constructed system+user prompt so question counts match user selection
        full_prompt_str = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

        payload = {
            "model": model,
            "prompt": full_prompt_str,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.1,
                "num_predict": 2048,
                "num_ctx": 4096
            }
        }

        try:
            logger.info("Calling local Ollama LLM", url=url, model=model)
            response = httpx.post(f"{url}/api/generate", json=payload, timeout=180.0)
            if response.status_code == 200:
                raw_text = response.json().get("response", "").strip()
                logger.info("Raw Ollama response received", length=len(raw_text))
                parsed = json.loads(raw_text)
                # Ensure required fields
                if "questions" not in parsed:
                    if isinstance(parsed, list):
                        parsed = {"exam_id": "exam_1", "lesson_id": "lesson_1", "title": "اختبار شامل", "questions": parsed}
                    else:
                        raise ValueError("Response missing 'questions' field")
                logger.info("Successfully parsed JSON from Ollama", question_count=len(parsed.get("questions", [])))
                return parsed
            else:
                raise RuntimeError(f"Ollama returned status {response.status_code}")
        except json.JSONDecodeError as je:
            logger.error("Ollama returned invalid JSON", error=str(je), raw=raw_text[:200])
            raise RuntimeError(f"Ollama returned invalid JSON: {str(je)}")
        except Exception as e:
            logger.error("Ollama call failed", url=url, error=str(e))
            raise RuntimeError(f"Could not connect to Ollama: {str(e)}")

ollama_llm = OllamaLLM()

