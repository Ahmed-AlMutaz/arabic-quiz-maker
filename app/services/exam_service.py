import os
import uuid
from typing import Dict, Any, Optional
from app.schemas.request import ExamGenerationRequest
from app.schemas.exam import GeneratedExam, ExamQuestion, QuestionType, DifficultyLevel
from app.rag.graph import langgraph_pipeline
from app.db.mongo_client import mongo_manager
from app.word_gen.student_doc import student_doc_generator
from app.word_gen.teacher_doc import teacher_doc_generator
from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import RAGPipelineError

class ExamService:
    """Service layer managing LangGraph RAG exam generation and Word document output."""

    async def generate_exam(self, request: ExamGenerationRequest) -> GeneratedExam:
        logger.info("Initiating Exam Generation Service", lesson_id=request.lesson_id)

        # 1. Fetch Lesson Data from DB
        lesson = await mongo_manager.get_lesson(request.lesson_id)
        if not lesson:
            raise RAGPipelineError(f"Lesson ID '{request.lesson_id}' not found in database. Please run OCR indexing first.")

        # Reconstruct Parent objects map
        raw_parents = lesson.get("parents", {})
        parents_map = {}
        for p_id, p_data in raw_parents.items():
            class DummyParent:
                pass
            dp = DummyParent()
            dp.id = p_data["id"]
            dp.text = p_data["text"]
            parents_map[p_id] = dp

        # 2. Run LangGraph RAG Pipeline
        dist_dump = request.distribution.model_dump()
        if request.num_mcq is not None:
            dist_dump["num_mcq"] = request.num_mcq
        if request.num_true_false is not None:
            dist_dump["num_true_false"] = request.num_true_false
        if request.num_short_answer is not None:
            dist_dump["num_short_answer"] = request.num_short_answer
        if request.num_fill_blank is not None:
            dist_dump["num_fill_blank"] = request.num_fill_blank

        initial_state = {
            "lesson_id": request.lesson_id,
            "lesson_parents": parents_map,
            "exam_title": request.exam_title,
            "easy_count": request.easy_count if request.easy_count is not None else 2,
            "medium_count": request.medium_count if request.medium_count is not None else 2,
            "hard_count": request.hard_count if request.hard_count is not None else 1,
            "num_mcq": request.num_mcq,
            "num_true_false": request.num_true_false,
            "num_short_answer": request.num_short_answer,
            "num_fill_blank": request.num_fill_blank,
            "distribution": dist_dump,
            "difficulty": request.difficulty.model_dump(),
            "retrieved_chunks": [],
            "reranked_chunks": [],
            "constructed_prompt": "",
            "generated_json": {},
            "generated_exam": None,
            "error": ""
        }

        final_state = langgraph_pipeline.run(initial_state)

        if final_state.get("error"):
            logger.error("LangGraph RAG pipeline failed to generate exam", error=final_state["error"])
            raise RAGPipelineError(f"فشلت معالجة توليد الامتحان من النص المستخرج: {final_state['error']}")

        exam = final_state.get("generated_exam")
        if not exam:
            raise RAGPipelineError("لم يتمكن الذكاء الاصطناعي من هيكلة الامتحان من الصورة المرفوعة. يرجى رفع صورة أكثر وضوحاً.")

        # Apply custom user metadata if provided
        exam.metadata = request.metadata
        exam.title = request.exam_title

        # 3. Generate Word Documents (Student.docx & Teacher.docx)
        exam_id = f"exam_{uuid.uuid4().hex[:8]}"
        exam.exam_id = exam_id

        student_path = os.path.join(settings.EXAMS_DIR, f"Student_{exam_id}.docx")
        teacher_path = os.path.join(settings.EXAMS_DIR, f"Teacher_{exam_id}.docx")

        student_doc_generator.generate(exam, student_path)
        teacher_doc_generator.generate(exam, teacher_path)

        exam.student_docx_url = f"/api/v1/download/student/{exam_id}"
        exam.teacher_docx_url = f"/api/v1/download/teacher/{exam_id}"

        # 4. Save Exam Record to Mongo DB
        await mongo_manager.save_exam(exam_id, exam.model_dump())

        logger.info("Exam Generation Service completed successfully", exam_id=exam_id)
        return exam



exam_service = ExamService()
