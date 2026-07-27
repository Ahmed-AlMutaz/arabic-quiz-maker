import io
from typing import List, Optional, Dict, Any
from PIL import Image
import google.generativeai as genai
from app.core.config import settings
from app.core.logging import logger
from app.ocr.preprocessor import preprocessor

class OCREngine:
    """Robust Arabic OCR Engine using local Pytesseract / EasyOCR with LLM text correction."""

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

    def _correct_extracted_text(self, raw_text: str) -> str:
        """Correct spelling mistakes and OCR typos in Arabic text using a cheap LLM."""
        if not raw_text or len(raw_text.strip()) < 10:
            return raw_text

        logger.info("Executing LLM correction pass on raw OCR text...", length=len(raw_text))

        system_prompt = (
            "أنت خبير تصحيح وتدقيق لغوي لملفات النصوص العربية المستخرجة عبر الـ OCR.\n"
            "مهمتك هي إصلاح الأخطاء الإملائية والطباعية والخلط بين الحروف المتشابهة (مثل ف/ق/ع/غ، ب/ت/ث/ن/ي/س) الناتجة عن القراءة الآلية للنص.\n"
            "قوانين صارمة:\n"
            "1. أصلح الكلمات المشوهة فقط (مثال: تحويل 'أبو حنيعة' إلى 'أبو حنيفة'، 'أحمد بن حسل' إلى 'أحمد بن حنبل'، 'اللعمان بن ثاب' إلى 'النعمان بن ثابت'، 'خبر النخارق' إلى 'خبر البخاري').\n"
            "2. حافظ على هيكل النص، الفقرات، العناوين، والنص الأصلي كاملاً كما هو.\n"
            "3. لا تضف أي تعليقات توضيحية أو مقدمات أو خاتمة خارج النص الأصلي.\n"
            "4. أرجع النص المصحح فقط."
        )

        # 1. Try Groq (llama-3.1-8b-instant is extremely fast, accurate for text, and free)
        try:
            import os
            import httpx
            groq_api_key = os.getenv("GROQ_API_KEY")
            payload = {
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": raw_text}
                ],
                "temperature": 0.1,
                "max_tokens": 2048
            }
            headers = {
                "Authorization": f"Bearer {groq_api_key}",
                "Content-Type": "application/json"
            }
            res = httpx.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers, timeout=20.0)
            if res.status_code == 200:
                corrected = res.json()["choices"][0]["message"]["content"].strip()
                if corrected and len(corrected) > 10:
                    logger.info("Groq LLM text correction completed", original_len=len(raw_text), corrected_len=len(corrected))
                    return corrected
            else:
                logger.warning(f"Groq text correction API error: {res.status_code}", body=res.text)
        except Exception as e:
            logger.warning("Groq text correction failed, trying Gemini fallback", error=str(e))

        # 2. Try Gemini (using default/custom key)
        try:
            response = self.vision_model.generate_content([system_prompt, raw_text])
            corrected = response.text.strip()
            if corrected and len(corrected) > 10:
                logger.info("Gemini LLM text correction completed")
                return corrected
        except Exception as ge:
            logger.warning("Gemini text correction failed, trying OpenRouter fallback", error=str(ge))

        # 3. Try OpenRouter (qwen/qwen-2.5-7b-instruct:free)
        try:
            import os
            import httpx
            or_api_key = os.getenv("OPENROUTER_API_KEY")
            payload = {
                "model": "qwen/qwen-2.5-7b-instruct:free",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": raw_text}
                ],
                "temperature": 0.1,
                "max_tokens": 2048
            }
            headers = {
                "Authorization": f"Bearer {or_api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://ahmed792-arabic-quiz-maker.hf.space/",
                "X-Title": "Arabic Quiz Maker"
            }
            res = httpx.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers, timeout=20.0)
            if res.status_code == 200:
                corrected = res.json()["choices"][0]["message"]["content"].strip()
                if corrected and len(corrected) > 10:
                    logger.info("OpenRouter text correction completed")
                    return corrected
        except Exception as oe:
            logger.warning("OpenRouter text correction failed", error=str(oe))

        # Return original raw text if all correction attempts fail
        logger.warning("All LLM text correction attempts failed, returning raw OCR text")
        return raw_text

    def extract_text_from_bytes(self, file_bytes: bytes) -> str:
        """Extracts Arabic text from PDF or Image bytes using Pytesseract and fixes typos using cheap LLM."""
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
                    return self._correct_extracted_text(full_pdf_text)
            except Exception as pe:
                logger.warning("pypdf extraction failed, attempting OCR fallback", error=str(pe))

        processed_img = preprocessor.preprocess_image(file_bytes)
        raw_text = ""

        # 1. Local Pytesseract Arabic (Primary - free, offline, no limits)
        try:
            logger.info("Executing local Pytesseract Arabic OCR pass...")
            import pytesseract
            text = pytesseract.image_to_string(processed_img, lang='ara')
            if text and len(text.strip()) > 15:
                logger.info("Arabic Pytesseract OCR completed", length=len(text))
                raw_text = text.strip()
        except Exception as pe:
            logger.warning("Pytesseract OCR failed, attempting EasyOCR fallback", error=str(pe))

        # 2. Local EasyOCR Fallback (Secondary - Cached Singleton)
        if not raw_text:
            try:
                logger.info("Executing local EasyOCR fallback pass...")
                reader = self._get_easyocr_reader()
                if reader:
                    import numpy as np
                    img_np = np.array(processed_img)
                    results = reader.readtext(img_np, detail=0)
                    text = " ".join(results).strip()
                    if text and len(text) > 15:
                        logger.info("Arabic EasyOCR OCR completed", length=len(text))
                        raw_text = text
            except Exception as ee:
                logger.warning("EasyOCR fallback failed", error=str(ee))

        if not raw_text:
            raise ValueError("فشلت قراءة النص العربي من الصورة المرفوعة. يرجى رفع صورة أكثر وضوحاً.")

        # Run LLM-based spelling and layout correction on the raw text
        return self._correct_extracted_text(raw_text)

    def extract_text_from_multiple_images(self, image_bytes_list: List[bytes]) -> str:
        full_texts = []
        for idx, img_bytes in enumerate(image_bytes_list):
            logger.info(f"Extracting text from image {idx+1}/{len(image_bytes_list)}")
            text = self.extract_text_from_bytes(img_bytes)
            full_texts.append(f"\n--- الصفحة {idx+1} ---\n{text}")
        return "\n".join(full_texts)

ocr_engine = OCREngine()
