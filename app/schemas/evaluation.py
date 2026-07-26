from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class RAGASEvalRequest(BaseModel):
    exam_id: str = Field(..., description="Target exam ID to evaluate")
    sample_size: Optional[int] = Field(default=5, description="Number of question-context pairs to evaluate")

class RAGASEvalReport(BaseModel):
    exam_id: str
    faithfulness: float
    context_recall: float
    context_precision: float
    answer_relevancy: float
    answer_correctness: float
    overall_ragas_score: float
    details: Dict[str, Any]
