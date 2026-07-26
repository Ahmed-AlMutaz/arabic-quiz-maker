from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.exam import QuestionDistribution, DifficultyDistribution, ExamMetadata

class ExamGenerationRequest(BaseModel):
    lesson_id: str = Field(..., description="ID of previously OCR-indexed lesson")
    exam_title: str = Field(default="اختبار شامل", description="Title of generated exam")
    easy_count: Optional[int] = Field(default=10, ge=0, description="Number of easy questions requested")
    medium_count: Optional[int] = Field(default=5, ge=0, description="Number of medium questions requested")
    hard_count: Optional[int] = Field(default=5, ge=0, description="Number of hard questions requested")
    num_mcq: Optional[int] = Field(default=10, ge=0, description="Number of MCQ questions requested")
    num_true_false: Optional[int] = Field(default=5, ge=0, description="Number of True/False questions requested")
    num_short_answer: Optional[int] = Field(default=5, ge=0, description="Number of Short Answer questions requested")
    num_fill_blank: Optional[int] = Field(default=0, ge=0, description="Number of Fill-in-the-blank questions requested")
    distribution: QuestionDistribution = Field(default_factory=QuestionDistribution)
    difficulty: DifficultyDistribution = Field(default_factory=DifficultyDistribution)
    metadata: ExamMetadata = Field(default_factory=ExamMetadata)


class RawTextIndexRequest(BaseModel):
    lesson_title: str = Field(..., description="Lesson title")
    text_content: str = Field(..., description="Full Arabic raw text content")
    subject: Optional[str] = Field(default="General Arabic")
