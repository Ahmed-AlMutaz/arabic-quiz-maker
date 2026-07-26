import re
from app.core.logging import logger

class ArabicTextCleaner:
    """Enterprise Arabic Text Cleaner & Normalizer."""
    
    # Tashkeel regex (Harakat / Diacritics)
    TASHKEEL_PATTERN = re.compile(r'[\u0617-\u061A\u064B-\u0652]')
    # Tatweel (Kashida)
    TATWEEL_PATTERN = re.compile(r'\u0640')
    # Arabic to Western digits map
    EASTERN_TO_WESTERN_DIGITS = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')

    @classmethod
    def strip_tashkeel(cls, text: str) -> str:
        """Removes diacritics from Arabic text."""
        return cls.TASHKEEL_PATTERN.sub('', text)

    @classmethod
    def strip_tatweel(cls, text: str) -> str:
        """Removes kashida elongation lines."""
        return cls.TATWEEL_PATTERN.sub('', text)

    @classmethod
    def normalize_alef(cls, text: str) -> str:
        """Normalizes Alef variants (أ, إ, آ -> ا)."""
        text = re.sub(r'[أإآ]', 'ا', text)
        return text

    @classmethod
    def normalize_ya_and_ta(cls, text: str) -> str:
        """Normalizes Ya (ى -> ي) and Ta Marbuta (ة -> ه)."""
        text = re.sub(r'ى', 'ي', text)
        text = re.sub(r'ة', 'ه', text)
        return text

    @classmethod
    def normalize_digits(cls, text: str) -> str:
        """Converts Eastern Arabic numerals to Western Arabic digits."""
        return text.translate(cls.EASTERN_TO_WESTERN_DIGITS)

    @classmethod
    def clean(cls, text: str, remove_tashkeel: bool = True, normalize_letters: bool = False) -> str:
        if not text:
            return ""

        cleaned = text.strip()
        cleaned = cls.normalize_digits(cleaned)
        cleaned = cls.strip_tatweel(cleaned)

        if remove_tashkeel:
            cleaned = cls.strip_tashkeel(cleaned)

        if normalize_letters:
            cleaned = cls.normalize_alef(cleaned)
            cleaned = cls.normalize_ya_and_ta(cleaned)

        # Normalize spaces and multi-newlines
        cleaned = re.sub(r'[ \t]+', ' ', cleaned)
        cleaned = re.sub(r'\n+', '\n', cleaned)

        return cleaned.strip()

text_cleaner = ArabicTextCleaner()
