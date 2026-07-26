from app.rag.text_cleaner import ArabicTextCleaner

def test_strip_tashkeel():
    text_with_harakat = "الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ"
    cleaned = ArabicTextCleaner.strip_tashkeel(text_with_harakat)
    assert cleaned == "الحمد لله رب العالمين"

def test_strip_tatweel():
    text_with_tatweel = "العــــلم والـــمعرفة"
    cleaned = ArabicTextCleaner.strip_tatweel(text_with_tatweel)
    assert cleaned == "العلم والمعرفة"

def test_normalize_digits():
    eastern_digits = "١٢٣٤٥٦٧٨٩٠"
    western_digits = ArabicTextCleaner.normalize_digits(eastern_digits)
    assert western_digits == "1234567890"

def test_full_clean():
    raw_text = "الْعِلْمُ ــ يَرْفَعُ   بَيْتًا لَا عِمَادَ لَهُ ٠١٢"
    cleaned = ArabicTextCleaner.clean(raw_text, remove_tashkeel=True)
    assert "العلم يرفع بيتا لا عماد له 012" in cleaned
