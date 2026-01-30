import pytest
from urdu_g2p import UrduG2P

def test_nonsense_and_symbols():
    g2p = UrduG2P()
    
    # Test 1: Emojis mixed with Urdu
    text_emoji = "پاکستان 🇵🇰 زندہ باد ❤️"
    # Expectation: Emojis should be ignored or treated as punctuation/space, not crash
    phonemes = g2p(text_emoji)
    print(f"Input: {text_emoji}")
    print(f"Output: {phonemes}")
    # Ideally, 🇵🇰 and ❤️ should be stripped or ignored if they are not in the map
    # The current regex for punctuation might not catch emojis, so they might be passed through or treated as OOV
    
    # Test 2: Random symbols
    text_symbols = "@@##!! اردو $$%%"
    phonemes_symbols = g2p(text_symbols)
    print(f"Input: {text_symbols}")
    print(f"Output: {phonemes_symbols}")
    
    # Test 3: Dirty text
    text_dirty = "F&%^$k this s#*t... مجھے ٹیسٹ کرو"
    phonemes_dirty = g2p(text_dirty)
    print(f"Input: {text_dirty}")
    print(f"Output: {phonemes_dirty}")

    # Test 4: Dot removal check
    # Manually check _normalize_ipa since it's hard to force espeak to produce a dot deterministically without specific context
    normalized = g2p._normalize_ipa("ʈeː.st̪")
    assert "." not in normalized
    assert normalized == "ʈeːst̪"
    print(f"Dot removal test: ʈeː.st̪ -> {normalized}")

    # Test 5: Stress removal (init param)
    g2p_stress = UrduG2P(ignore_stress=True)
    text_stress = "مجھے"
    # mʊˈd͡ʒeː -> mʊd͡ʒeː
    phoneme_stress = g2p_stress(text_stress)[0]
    print(f"Stress removal test: {text_stress} -> {phoneme_stress}")
    assert "ˈ" not in phoneme_stress
    
    # Assertions - basically ensuring it doesn't crash and output helps diagnosis
    assert isinstance(phonemes, list)
    assert isinstance(phonemes_symbols, list)
    assert isinstance(phonemes_dirty, list)
