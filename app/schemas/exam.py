from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class QuestionType(str, Enum):
    MCQ = "mcq"                      # الاختيار من متعدد
    TRUE_FALSE = "true_false"        # صح أم خطأ
    FILL_IN_BLANK = "fill_in_blank"  # أكمل الفراغ
    SHORT_ANSWER = "short_answer"    # إجابة قصيرة
    ESSAY = "essay"                  # أسئلة مقالية

class DifficultyLevel(str, Enum):
    EASY = "easy"      # سهولة (تذكر وفهم)
    MEDIUM = "medium"  # متوسط (تطبيق وتحليل)
    HARD = "hard"      # صعوبة (تقييم وابتكار)

class QuestionOption(BaseModel):
    key: str = Field(..., description="Option label, e.g., 'أ', 'ب', 'ج', 'د'")
    text: str = Field(..., description="Option text content in Arabic")

class ExamQuestion(BaseModel):
    id: str = Field(..., description="Unique Question Identifier")
    question_type: QuestionType = Field(..., description="Type of question")
    difficulty: DifficultyLevel = Field(..., description="Difficulty level")
    question_text: str = Field(..., description="The Arabic text of the question")
    options: Optional[List[QuestionOption]] = Field(default=None, description="Options for MCQ questions")
    correct_answer: str = Field(..., description="Model answer for teacher answer key")
    explanation: str = Field(..., description="Pedagogical explanation / textbook reference")
    marks: int = Field(default=1, description="Marks allocated for this question")
    context_chunk_id: Optional[str] = Field(default=None, description="Reference parent chunk ID for zero-hallucination verification")

class QuestionDistribution(BaseModel):
    num_mcq: int = Field(default=10, ge=0, description="Number of MCQ questions")
    num_true_false: int = Field(default=5, ge=0, description="Number of True/False questions")
    num_fill_blank: int = Field(default=0, ge=0, description="Number of Fill-in-the-blank questions")
    num_short_answer: int = Field(default=5, ge=0, description="Number of Short Answer questions")
    num_essay: int = Field(default=0, ge=0, description="Number of Essay questions")

class DifficultyDistribution(BaseModel):
    easy_percentage: int = Field(default=40, ge=0, le=100, description="Percentage of easy questions")
    medium_percentage: int = Field(default=40, ge=0, le=100, description="Percentage of medium questions")
    hard_percentage: int = Field(default=20, ge=0, le=100, description="Percentage of hard questions")

class ExamMetadata(BaseModel):
    school_name: str = Field(default="", description="School / Institute Name")
    teacher_name: str = Field(default="", description="Teacher Name")
    subject_name: str = Field(default="اختبار شامل", description="Subject Name")
    grade_level: str = Field(default="", description="Grade Level")
    term_name: str = Field(default="", description="Academic Term")
    time_allowed: str = Field(default="", description="Exam Duration")
    total_marks: int = Field(default=30, description="Total Exam Marks")

class GeneratedExam(BaseModel):
    exam_id: str = Field(..., description="Unique Exam Identifier")
    lesson_id: str = Field(..., description="Source Lesson Identifier")
    title: str = Field(..., description="Exam Title in Arabic")
    metadata: ExamMetadata = Field(default_factory=ExamMetadata)
    questions: List[ExamQuestion] = Field(..., description="List of generated exam questions")
    student_docx_url: Optional[str] = None
    teacher_docx_url: Optional[str] = None
    created_at: Optional[str] = None
