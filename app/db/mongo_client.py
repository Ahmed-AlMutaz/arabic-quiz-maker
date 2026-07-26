from typing import Dict, Any, Optional, List
import motor.motor_asyncio
from app.core.config import settings
from app.core.logging import logger

class MongoManager:
    """Manages async MongoDB interactions for lesson text, trees, exam records, and evaluation logs."""
    
    def __init__(self):
        self.client = None
        self.db = None
        self._in_memory_store: Dict[str, Dict[str, Any]] = {
            "lessons": {},
            "exams": {},
            "evaluations": {}
        }
        self.use_mongo = False
        self._connect()

    def _connect(self):
        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(
                settings.MONGO_URI, serverSelectionTimeoutMS=2000
            )
            self.db = self.client[settings.MONGO_DB_NAME]
            self.use_mongo = True
            logger.info("Connected to MongoDB", uri=settings.MONGO_URI, db=settings.MONGO_DB_NAME)
        except Exception as e:
            logger.warning("MongoDB connection unavailable, using local in-memory document store", error=str(e))
            self.use_mongo = False

    async def save_lesson(self, lesson_id: str, lesson_data: Dict[str, Any]) -> bool:
        if self.use_mongo and self.db is not None:
            try:
                await self.db.lessons.update_one({"lesson_id": lesson_id}, {"$set": lesson_data}, upsert=True)
                return True
            except Exception as e:
                logger.error("Error saving lesson to MongoDB", error=str(e))
        # Fallback store
        self._in_memory_store["lessons"][lesson_id] = lesson_data
        return True

    async def get_lesson(self, lesson_id: str) -> Optional[Dict[str, Any]]:
        if self.use_mongo and self.db is not None:
            try:
                doc = await self.db.lessons.find_one({"lesson_id": lesson_id})
                if doc:
                    doc.pop("_id", None)
                    return doc
            except Exception as e:
                logger.error("Error retrieving lesson from MongoDB", error=str(e))
        return self._in_memory_store["lessons"].get(lesson_id)

    async def save_exam(self, exam_id: str, exam_data: Dict[str, Any]) -> bool:
        if self.use_mongo and self.db is not None:
            try:
                await self.db.exams.update_one({"exam_id": exam_id}, {"$set": exam_data}, upsert=True)
                return True
            except Exception as e:
                logger.error("Error saving exam to MongoDB", error=str(e))
        self._in_memory_store["exams"][exam_id] = exam_data
        return True

    async def get_exam(self, exam_id: str) -> Optional[Dict[str, Any]]:
        if self.use_mongo and self.db is not None:
            try:
                doc = await self.db.exams.find_one({"exam_id": exam_id})
                if doc:
                    doc.pop("_id", None)
                    return doc
            except Exception as e:
                logger.error("Error getting exam from MongoDB", error=str(e))
        return self._in_memory_store["exams"].get(exam_id)

mongo_manager = MongoManager()
