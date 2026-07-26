import uuid
from typing import List, Dict, Any
from qdrant_client.models import PointStruct
from app.ocr.engine import ocr_engine
from app.rag.text_cleaner import text_cleaner
from app.rag.tree_chunker import tree_chunker
from app.rag.embeddings import embedding_generator
from app.db.qdrant_client import qdrant_manager
from app.db.mongo_client import mongo_manager
from app.rag.bm25_indexer import bm25_indexer
from app.schemas.ocr import OCRResponse
from app.core.logging import logger

class OCRService:
    """Service handling OCR extraction, cleaning, tree chunking, and dual vector/sparse indexing."""

    async def process_images_and_index(self, image_bytes_list: List[bytes], lesson_title: str = "درس عربي") -> OCRResponse:
        lesson_id = f"lesson_{uuid.uuid4().hex[:8]}"
        logger.info("Processing OCR image upload for lesson", lesson_id=lesson_id, images_count=len(image_bytes_list))

        # 1. OCR Extraction
        raw_text = ocr_engine.extract_text_from_multiple_images(image_bytes_list)

        # 2. Arabic Text Cleaning & Normalization
        cleaned_text = text_cleaner.clean(raw_text, remove_tashkeel=False)
        clean_text_for_search = text_cleaner.clean(raw_text, remove_tashkeel=True)

        # 3. Tree-Based (Parent-Child) Chunking
        tree_res = tree_chunker.build_tree(cleaned_text, lesson_id=lesson_id, lesson_title=lesson_title)
        parents = tree_res["parents"]
        children = tree_res["children"]

        # 4. Dense Embeddings & Vector DB Indexing (Qdrant)
        child_dicts = []
        points = []
        for idx, child_node in enumerate(children):
            c_dict = child_node.model_dump()
            child_dicts.append(c_dict)

            vec = embedding_generator.embed_text(child_node.text)
            point = PointStruct(
                id=idx + 1000,
                vector=vec,
                payload={
                    "child_id": child_node.id,
                    "parent_id": child_node.parent_id,
                    "lesson_id": lesson_id,
                    "text": child_node.text,
                    "chapter_title": lesson_title
                }
            )
            points.append(point)

        qdrant_manager.upsert_vectors(points)

        # 5. Sparse Keyword BM25 Indexing
        bm25_indexer.fit(child_dicts)

        # 6. MongoDB Document Persistence
        lesson_data = {
            "lesson_id": lesson_id,
            "title": lesson_title,
            "raw_text": raw_text,
            "cleaned_text": cleaned_text,
            "parents": {k: v.model_dump() for k, v in parents.items()},
            "children": child_dicts,
            "created_at": str(uuid.uuid4())
        }
        await mongo_manager.save_lesson(lesson_id, lesson_data)

        return OCRResponse(
            lesson_id=lesson_id,
            extracted_text=raw_text,
            cleaned_text=cleaned_text,
            parent_chunks_count=len(parents),
            child_chunks_count=len(children),
            indexed=True
        )

    async def process_raw_text_and_index(self, raw_text: str, lesson_title: str = "درس عربي") -> OCRResponse:
        lesson_id = f"lesson_{uuid.uuid4().hex[:8]}"
        logger.info("Processing raw text indexing", lesson_id=lesson_id, length=len(raw_text))

        cleaned_text = text_cleaner.clean(raw_text, remove_tashkeel=False)
        tree_res = tree_chunker.build_tree(cleaned_text, lesson_id=lesson_id, lesson_title=lesson_title)
        parents = tree_res["parents"]
        children = tree_res["children"]

        child_dicts = []
        points = []
        for idx, child_node in enumerate(children):
            c_dict = child_node.model_dump()
            child_dicts.append(c_dict)

            vec = embedding_generator.embed_text(child_node.text)
            point = PointStruct(
                id=idx + 5000,
                vector=vec,
                payload={
                    "child_id": child_node.id,
                    "parent_id": child_node.parent_id,
                    "lesson_id": lesson_id,
                    "text": child_node.text,
                    "chapter_title": lesson_title
                }
            )
            points.append(point)

        qdrant_manager.upsert_vectors(points)
        bm25_indexer.fit(child_dicts)

        lesson_data = {
            "lesson_id": lesson_id,
            "title": lesson_title,
            "raw_text": raw_text,
            "cleaned_text": cleaned_text,
            "parents": {k: v.model_dump() for k, v in parents.items()},
            "children": child_dicts
        }
        await mongo_manager.save_lesson(lesson_id, lesson_data)

        return OCRResponse(
            lesson_id=lesson_id,
            extracted_text=raw_text,
            cleaned_text=cleaned_text,
            parent_chunks_count=len(parents),
            child_chunks_count=len(children),
            indexed=True
        )

ocr_service = OCRService()
