import pytest
from urdu_g2p import UrduG2P

def test_inline_phoneme_preservation():
    """Test that inline phoneme notation [/.../] is preserved even if it contains symbols."""
    g2p = UrduG2P()
    # "paːkɪsˈt̪aːn" contains ː and ˈ which might serve as symbols
    text = "پاکستان[/paːkɪsˈt̪aːn/] ایک ملک ہے"
    result = g2p(text)
    
    # Expected: First token should be the exact IPA provided
    assert result[0] == "paːkɪsˈt̪aːn"
    # Full check
    # ایک -> eːk
    # ملک -> mɪlək
    # ہے -> hɛ
    assert result == ["paːkɪsˈt̪aːn", "eːk", "mɪlək", "hɛ"]

def test_vowel_length_normalization():
    """Test collapsing of 2+ consecutive identical vowels into vowel + length mark."""
    g2p = UrduG2P()
    
    # Test normalization method directly
    # 'ii' -> 'iː'
    # 'a' is normalized to 'ə' by default in consonant aliasing
    assert g2p._normalize_ipa("gariii") == "gəriː" # 'iii' -> 'i' + length
    
    # 'aa' -> 'aː'
    assert g2p._normalize_ipa("haaaaii") == "haːiː" # 'aaaa' -> 'aː', 'ii' -> 'iː'

def test_punctuation_mapping_default():
    """Test default punctuation mapping."""
    g2p = UrduG2P()
    text = "ہیلو۔ کیسے ہو،"
    # Default map: '۔': '|', '،': '~'
    result = g2p(text)
    
    assert "|" in result
    assert "~" in result
    
    # Check order
    # heːˈloː | kɛseː hoː ~
    assert result == ["heːˈloː", "|", "kɛseː", "hoː", "~"]

def test_punctuation_mapping_custom():
    """Test custom punctuation mapping via init."""
    g2p = UrduG2P(map_punct={'۔': 'STOP', '،': 'COMMA'})
    text = "ہیلو۔ کیسے ہو،"
    result = g2p(text)
    
    assert "STOP" in result
    assert "COMMA" in result
    assert result == ["heːˈloː", "STOP", "kɛseː", "hoː", "COMMA"]

def test_punctuation_mapping_validation():
    """Test validation of bad punctuation maps."""
    # Mapping to a reserved IPA char should fail
    with pytest.raises(ValueError):
        UrduG2P(map_punct={'۔': 'a'}) # 'a' is a vowel
        
    # Mapping to >32 chars should fail
    with pytest.raises(ValueError):
         UrduG2P(map_punct={'۔': 'A'*33})
         
    # Mapping with space should fail
    with pytest.raises(ValueError):
         UrduG2P(map_punct={'۔': 'TOKEN WITH SPACE'})
