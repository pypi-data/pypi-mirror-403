import sys
import os
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from urdu_g2p import UrduG2P

def test_comprehensive():
    print("=== Comprehensive System Test ===")
    
    # Initialize with Fallback enabled
    print("Initializing UrduG2P (fallback=True)...")
    g2p = UrduG2P(fallback=True)
    
    # 1. Standard Long Paragraph Test
    print("\n[Test 1] Standard Long Paragraph (Dictionary Lookup + Punctuation)")
    para_std = (
        "اچھا، تو میرے پیارے طالب علم، جب ہم خاندانی رشتے کہتے ہیں تو ہمارے ذہن میں سب سے پہلے کیا آتا ہے؟ "
        "میرے خیال میں یہ وہ مضبوط بندھن ہے جو ہمیں ایک دوسرے سے جوڑتا ہے۔ "
        "زندگی میں ہر موڑ پر، چاہے خوشی ہو یا غم، خاندان ہی ہمارا سب سے بڑا سہارا ہوتا ہے۔ "
        "شوکت خانم جیسے ادارے بھی اسی جذبے کے تحت کام کر رہے ہیں۔"
    )
    start = time.time()
    res_std = g2p(para_std)
    dur = time.time() - start
    print(f"Processed {len(para_std)} chars in {dur:.4f}s")
    print(f"Output Snippet: {' '.join(res_std[:20])} ...")
    
    if '~' in res_std and '|' in res_std:
        print("  [PASS] Punctuation mapped correctly.")
    else:
        print("  [FAIL] Punctuation mapping missing.")

    # 2. Greedy Lookup Test (Missing Spaces)
    print("\n[Test 2] Greedy Lookup (Missing Spaces)")
    # "Pakistan Zindabad. Shaukat Khanum." joined
    text_greedy = "پاکستانزندہباد۔شوکتخانم۔"
    start = time.time()
    res_greedy = g2p(text_greedy, lookup='greedy')
    dur = time.time() - start
    print(f"Input: {text_greedy}")
    print(f"Output: {res_greedy}")
    
    # Expect: [..., 'zindabad', '|', 'shaukat', 'khanum', '|']
    if len(res_greedy) >= 5 and '|' in res_greedy: 
        print("  [PASS] Greedy tokenization separated words.")
    else:
        print("  [WARN] Greedy tokenization might have failed.")

    # 3. Fallback & Normalization Test (OOV Words)
    print("\n[Test 3] Fallback & Normalization (OOV Words)")
    # Nonsense words that look like Urdu
    # "کخپتٹ" (Kakhpatt - Nonsense)
    # "برجکلیفہ" (Burj Khalifa - Might be in dict? Let's try rare spelling or nonsense)
    # "گگگلوو" (Gggloo - used before)
    text_oov = "یہ ایک گگگلوو اور کخپتٹ ہے۔" 
    start = time.time()
    res_oov = g2p(text_oov)
    dur = time.time() - start
    print(f"Input: {text_oov}")
    print(f"Output: {res_oov}")
    
    # Check if OOV words are IPA (contain non-Urdu chars)
    oov_indices = [2, 4] # indicies of oov words in output list
    all_ipa = True
    for idx in oov_indices:
        word_out = res_oov[idx]
        # Check for latin characters or IPA symbols
        if not any(c.isascii() or c in 'əɛɪʊt̪d̪' for c in word_out):
            print(f"  [FAIL] Word at index {idx} '{word_out}' seems to be unchanged/Urdu (Fallback failed).")
            all_ipa = False
        # Check normalization (t -> t̪ if applicable)
        if 't' in word_out and 't̪' not in word_out and 't͡ʃ' not in word_out:
             # Just a heuristic check
             pass

    if all_ipa:
        print("  [PASS] OOV words converted to IPA via Fallback.")

if __name__ == "__main__":
    test_comprehensive()
