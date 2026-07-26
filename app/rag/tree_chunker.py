import uuid
from typing import List, Dict, Any
from pydantic import BaseModel
from app.core.config import settings
from app.core.logging import logger

class ChunkNode(BaseModel):
    id: str
    lesson_id: str
    level: str  # "parent" or "child"
    parent_id: str = ""
    text: str
    char_count: int
    metadata: Dict[str, Any] = {}

class TreeChunker:
    """Parent-Child Tree Chunking Engine for Arabic Educational Text."""

    def __init__(
        self,
        parent_size: int = settings.PARENT_CHUNK_SIZE,
        parent_overlap: int = settings.PARENT_CHUNK_OVERLAP,
        child_size: int = settings.CHILD_CHUNK_SIZE,
        child_overlap: int = settings.CHILD_CHUNK_OVERLAP,
    ):
        self.parent_size = parent_size
        self.parent_overlap = parent_overlap
        self.child_size = child_size
        self.child_overlap = child_overlap

    def _split_text_by_delimiter(self, text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        paragraphs = text.split('\n')
        chunks = []
        current_chunk = []
        current_length = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            if current_length + len(para) + 1 <= chunk_size:
                current_chunk.append(para)
                current_length += len(para) + 1
            else:
                if current_chunk:
                    chunks.append("\n".join(current_chunk))
                # Handle oversized single paragraphs
                if len(para) > chunk_size:
                    for i in range(0, len(para), chunk_size - chunk_overlap):
                        chunks.append(para[i : i + chunk_size])
                    current_chunk = []
                    current_length = 0
                else:
                    current_chunk = [para]
                    current_length = len(para)

        if current_chunk:
            chunks.append("\n".join(current_chunk))
        
        return chunks if chunks else [text]

    def build_tree(self, text: str, lesson_id: str, lesson_title: str = "الدرس") -> Dict[str, Any]:
        """Builds a 2-level Parent-Child hierarchy tree from cleaned text."""
        logger.info("Building Tree-Based Chunks", lesson_id=lesson_id, text_length=len(text))

        parent_texts = self._split_text_by_delimiter(text, self.parent_size, self.parent_overlap)
        
        parent_map: Dict[str, ChunkNode] = {}
        child_list: List[ChunkNode] = []

        for p_idx, p_text in enumerate(parent_texts):
            p_id = f"parent_{lesson_id}_{p_idx}_{uuid.uuid4().hex[:6]}"
            parent_node = ChunkNode(
                id=p_id,
                lesson_id=lesson_id,
                level="parent",
                text=p_text,
                char_count=len(p_text),
                metadata={
                    "chapter_title": lesson_title,
                    "parent_index": p_idx
                }
            )
            parent_map[p_id] = parent_node

            # Split Parent into Children
            child_texts = self._split_text_by_delimiter(p_text, self.child_size, self.child_overlap)
            for c_idx, c_text in enumerate(child_texts):
                c_id = f"child_{p_id}_{c_idx}"
                child_node = ChunkNode(
                    id=c_id,
                    lesson_id=lesson_id,
                    level="child",
                    parent_id=p_id,
                    text=c_text,
                    char_count=len(c_text),
                    metadata={
                        "chapter_title": lesson_title,
                        "parent_id": p_id,
                        "parent_index": p_idx,
                        "child_index": c_idx
                    }
                )
                child_list.append(child_node)

        logger.info("Tree Chunking completed", parents_count=len(parent_map), children_count=len(child_list))
        return {
            "parents": parent_map,
            "children": child_list
        }

tree_chunker = TreeChunker()
