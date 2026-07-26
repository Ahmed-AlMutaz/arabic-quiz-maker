import os
import pytest
from app.schemas.exam import GeneratedExam, ExamQuestion, QuestionType, DifficultyLevel, ExamMetadata
from app.word_gen.student_doc import student_doc_generator
from app.word_gen.teacher_doc import teacher_doc_generator

@pytest.fixture
def dummy_exam():
    return GeneratedExam(
        exam_id="test_exam_123",
        lesson_id="lesson_123",
        title="اختبار تجريبي في اللغة العربية",
        metadata=ExamMetadata(school_name="مدرسة الاختبارات النموذجية"),
        questions=[
            ExamQuestion(
                id="q1",
                question_type=QuestionType.MCQ,
                difficulty=DifficultyLevel.EASY,
                question_text="ما هي عاصمة جمهورية مصر العربية؟",
                options=[
                    {"key": "أ", "text": "القاهرة"},
                    {"key": "ب", "text": "الإسكندرية"},
                    {"key": "ج", "text": "الجيزة"},
                    {"key": "د", "text": "أسوان"}
                ],
                correct_answer="القاهرة",
                explanation="القاهرة هي عاصمة مصر الإدارية والتاريخية.",
                marks=2
            )
        ]
    )

def test_student_and_teacher_docx_generation(dummy_exam, tmp_path):
    student_path = str(tmp_path / "Student_test.docx")
    teacher_path = str(tmp_path / "Teacher_test.docx")

    student_doc_generator.generate(dummy_exam, student_path)
    teacher_doc_generator.generate(dummy_exam, teacher_path)

    assert os.path.exists(student_path)
    assert os.path.getsize(student_path) > 0

    assert os.path.exists(teacher_path)
    assert os.path.getsize(teacher_path) > 0
