import sys
import os

# Fix path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from urdu_g2p import UrduG2P

def run_diverse_tests():
    print("Initializing UrduG2P...")
    g2p = UrduG2P()
    
    test_cases = [
        ("Formal News", "وزیراعظم نے قوم سے خطاب کرتے ہوئے کہا کہ معیشت بہتر ہو رہی ہے۔"),
        ("Poetry", "ستاروں سے آگے جہاں اور بھی ہیں | ابھی عشق کے امتحان اور بھی ہیں"),
        ("Loanwords (Default)", "آرٹیفیشل انٹیلیجنس کا دور ہے۔"),
        ("Mixed Script", "یہ Python لائبریری ہے۔"),
        ("Numbers", "سال 2024 میں 50 فیصد نمو۔"),
        ("base" , "پَھُوٹا")
    ]

    print("\n" + "="*80)
    print("DIVERSE INPUTS")
    print("="*80)
    
    for cat, text in test_cases:
        print(f"\n[{cat}]")
        print(f"Input: {text}")
        print(f"Output: {' '.join(g2p(text))}")

    print("\n" + "="*80)
    print("EDGE CASES")
    print("="*80)
    
    # Heavy Diacritics
    heavy_text = "اَلسَّلَامُ عَلَیْکُمْ"
    print(f"\n[Heavy Diacritics - Auto Mode] (Input: {heavy_text})")
    print(f"Output: {' '.join(g2p(heavy_text))}")
    
    print(f"\n[Heavy Diacritics - Ignore Mode]")
    g2p_ignore = UrduG2P(diacritic_mode='ignore')
    print(f"Output: {' '.join(g2p_ignore(heavy_text))}")
    
    # Custom Phoneme Fix
    print("\n[Custom Phoneme Fix]")
    print("Before fix (آرٹیفیشل):", ' '.join(g2p("آرٹیفیشل")))
    g2p_custom = UrduG2P(custom_phonemes={'آرٹیفیشل': 'aːrʈiːfɪʃəl'})
    print("After fix (آرٹیفیشل): ", ' '.join(g2p_custom("آرٹیفیشل")))

if __name__ == "__main__":
    run_diverse_tests()
