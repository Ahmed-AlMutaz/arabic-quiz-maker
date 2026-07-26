from typing import List, Optional
from pydantic import BaseModel, Field

class OCRResponse(BaseModel):
    lesson_id: str = Field(..., description="Unique generated lesson ID")
    extracted_text: str = Field(..., description="Raw extracted Arabic text from OCR")
    cleaned_text: str = Field(..., description="Cleaned and normalized Arabic text")
    parent_chunks_count: int = Field(..., description="Total parent chunks generated")
    child_chunks_count: int = Field(..., description="Total child chunks indexed in Qdrant")
    indexed: bool = Field(default=True, description="Whether indexing succeeded")

class EvaluationMetricsResponse(BaseModel):
    exam_id: str
    faithfulness: float = Field(..., ge=0.0, le=1.0)
    context_recall: float = Field(..., ge=0.0, le=1.0)
    context_precision: float = Field(..., ge=0.0, le=1.0)
    answer_relevancy: float = Field(..., ge=0.0, le=1.0)
    answer_correctness: float = Field(..., ge=0.0, le=1.0)
    overall_score: float = Field(..., ge=0.0, le=1.0)
    report_summary: str
