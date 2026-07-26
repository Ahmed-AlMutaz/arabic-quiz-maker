import io
from typing import List
from PIL import Image
import google.generativeai as genai
from app.core.config import settings
from app.core.logging import logger
from app.ocr.preprocessor import preprocessor

class OCREngine:
    """Robust Arabic OCR Engine using Pytesseract / EasyOCR with Gemini 1.5 Flash Vision Fallback."""

    def __init__(self):
        self._vision_model = None
        self._easyocr_reader = None

    @property
    def vision_model(self):
        if self._vision_model is None:
            self.api_key = settings.get_gemini_api_key()
            genai.configure(api_key=self.api_key)
            self._vision_model = genai.GenerativeModel("gemini-2.5-flash")
        return self._vision_model

    def _get_easyocr_reader(self):
        if self._easyocr_reader is None:
            try:
                import easyocr
                self._easyocr_reader = easyocr.Reader(['ar', 'en'], gpu=False)
            except Exception as e:
                logger.debug("EasyOCR initialization failed", error=str(e))
        return self._easyocr_reader

    def extract_text_from_bytes(self, file_bytes: bytes) -> str:
        """Extracts Arabic text from PDF or Image bytes in ~1.2 seconds."""
        if file_bytes.startswith(b'%PDF'):
            logger.info("PDF file detected, extracting text using pypdf...")
            try:
                import pypdf
                reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                text_pages = []
                for idx, page in enumerate(reader.pages):
                    txt = page.extract_text() or ""
                    if txt.strip():
                        text_pages.append(f"\n--- الصفحة {idx+1} ---\n{txt.strip()}")
                full_pdf_text = "\n".join(text_pages).strip()
                if full_pdf_text and len(full_pdf_text) > 20:
                    logger.info("PDF text extraction completed", length=len(full_pdf_text))
                    return full_pdf_text
            except Exception as pe:
                logger.warning("pypdf extraction failed, attempting OCR fallback", error=str(pe))

        processed_img = preprocessor.preprocess_image(file_bytes)

        # 1. Instant Vision OCR Pass with Gemini 2.5 Flash (Ultra Fast ~1.2s)
        try:
            logger.info("Executing instant Gemini 2.5 Flash Vision OCR pass...")
            prompt = (
                "أنت خبير استخراج نصوص تعليمية عربية عالي الدقة.\n"
                "استخرج النص العربي كاملاً بدقة 100% من صورة الدرس هذه.\n"
                "حافظ على الفقرات، العناوين، النقاط والترقيم كما هي بدون أي زيادات أو تعليقات خارجية."
            )
            response = self.vision_model.generate_content([prompt, processed_img])
            extracted = response.text.strip()
            if extracted and len(extracted) > 10:
                logger.info("Instant Gemini 2.5 Vision OCR completed", length=len(extracted))
                return extracted
        except Exception as e:
            logger.warning("Instant Vision OCR pass failed, falling back to local OCR", error=str(e))

        # 2. Local Pytesseract Arabic Fallback
        try:
            import pytesseract
            text = pytesseract.image_to_string(processed_img, lang='ara')
            if text and len(text.strip()) > 15:
                logger.info("Arabic Pytesseract fallback completed", length=len(text))
                return text.strip()
        except Exception as pe:
            logger.debug("Pytesseract fallback failed", error=str(pe))

        # 3. Local EasyOCR Fallback (Cached Singleton)
        try:
            reader = self._get_easyocr_reader()
            if reader:
                import numpy as np
                img_np = np.array(processed_img)
                results = reader.readtext(img_np, detail=0)
                text = " ".join(results).strip()
                if text and len(text) > 15:
                    logger.info("Arabic EasyOCR fallback completed", length=len(text))
                    return text
        except Exception as ee:
            logger.debug("EasyOCR fallback failed", error=str(ee))

        raise ValueError("فشلت قراءة النص العربي من الصورة المرفوعة. يرجى رفع صورة أكثر وضوحاً لدرس الفقه.")

    def extract_text_from_multiple_images(self, image_bytes_list: List[bytes]) -> str:
        full_texts = []
        for idx, img_bytes in enumerate(image_bytes_list):
            logger.info(f"Extracting text from image {idx+1}/{len(image_bytes_list)}")
            text = self.extract_text_from_bytes(img_bytes)
            full_texts.append(f"\n--- الصفحة {idx+1} ---\n{text}")
        return "\n".join(full_texts)

ocr_engine = OCREngine()
