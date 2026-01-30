import re

# ==========================================
# 1. LEGAL INPUT DEFINITIONS
# ==========================================

# Urdu specific characters
_URDU_ALPHABET = "آأابپتٹثجچحخدڈذرڑزژسشصضطظعغفقکگلمنںوؤہۂۃئیےھ"
_URDU_DIACRITICS = "َُِّْٰٖٗ"
_URDU_DIGITS = "۰۱۲۳۴۵۶۷۸۹"

# English characters
_ENG_ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
_ENG_DIGITS = "0123456789"

# Shared Punctuation & Symbols
# Includes standard ASCII and Urdu-specific variants
_PUNCTUATION = ",.?"       # Standard: Comma, Period, Question
_URDU_PUNCTUATION = "،؟۔"   # Urdu: Comma, Question, Period

# Combined Legal Input Set (as a string of characters)
LEGAL_INPUT = (
    _URDU_ALPHABET + 
    _URDU_DIACRITICS + 
    _URDU_DIGITS + 
    _ENG_ALPHABET + 
    _ENG_DIGITS + 
    _PUNCTUATION + 
    _URDU_PUNCTUATION
)

def clean_input(text: str) -> str:
    """
    Filters the input text, keeping only characters defined in LEGAL_INPUT.
    All other characters are dropped.
    Spaces are strictly preserved.
    """
    # Create a set for O(1) lookup
    valid_chars = set(LEGAL_INPUT)
    # Always allow space
    valid_chars.add(' ')
    
    return "".join(c for c in text if c in valid_chars)


# ==========================================
# 2. OUTPUT PHONEME DEFINITIONS
# ==========================================

# Vowels
_VOWELS = [
    "a", "aː", "i", "iː", "u", "uː", "e", "o", "ə", "æ", "ɛ", "ɔ", 
    "ɪ", "ʊ", "ʌ", "ɜ", "ɚ", "ɑ", "ã", "ĩ", "ũ", "ẽ", "õ",
    "ɒ", "ɐ"
]

# Consonants (Stops)
_STOPS = [
    "p", "b", "t", "d", "ʈ", "ɖ", "k", "ɡ", "q"
]

# Aspirated / Breathy Stops
_ASPIRATED_STOPS = [
    "pʰ", "bʱ", "tʰ", "dʱ", "ʈʰ", "ɖʱ", "kʰ", "ɡʱ"
]

# Nasals
_NASALS = [
    "m", "n", "ɳ", "ɲ"
]

# Affricates
_AFFRICATES = [
    "ʧ", "ʤ"
]

# Fricatives
_FRICATIVES = [
    "s", "z", "ʃ", "ʒ", "f", "x", "xʰ", "ɣ", "ɣʱ", "h", "θ", "ð"
]

# Liquids / Glides
_LIQUIDS_GLIDES = [
    "l", "r", "ɽ", "ɾ", "j", "w", "ʋ", "v"
]

# Others
_OTHERS = [
    "ŋ", "ɦ", "ʔ", "ʕ", "ħ",
    "ˈ", "ˌ", "̪", "̃"  # Stress and combining marks
]

# Valid output set excluding punctuation for now
# (Flatten the list)
LEGAL_OUTPUT_PHONEMES = (
    _VOWELS + _STOPS + _ASPIRATED_STOPS + _AFFRICATES + 
    _FRICATIVES + _LIQUIDS_GLIDES + _OTHERS + _NASALS
)

def normalize_output(text: str) -> str:
    """Applies normalization rules to phoneme string."""
    # 1. Map Affricates (handle various tie-bar forms and non-tied forms)
    # Tie bars: \u0361 (Top), \u035c (Bottom)
    text = re.sub(r't[\u0361\u035c]?ʃ', 'ʧ', text)
    text = re.sub(r'd[\u0361\u035c]?ʒ', 'ʤ', text)
    
    # Also handle 'c' and 'ɟ' if they somehow reached here
    text = text.replace("c", "ʧ")
    text = text.replace("ɟ", "ʤ")
    
    # 2. Map English approximant ɹ to standard r if desired
    # The user asked: ɹ -> r
    text = text.replace("ɹ", "r")
    
    # 3. Explicit Aspiration/Length Merging 
    text = text.replace(":", "ː") 
    
    return text

def get_legal_output_chars() -> str:
    """Returns a string of all unique characters found in legal phonemes"""
    unique_chars = set()
    for p in LEGAL_OUTPUT_PHONEMES:
        unique_chars.update(p)
    return "".join(sorted(unique_chars))
