import sys
import os
import random
import string

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from urdu_g2p import UrduG2P

def test_g2p():
    print("Beginning Tests...")
    g2p_default = UrduG2P(fallback=False)
    g2p_espeak = UrduG2P(fallback=True)
    
    # 1. Known OOV
    # "Google" in Urdu script usually "گوگل" (likely in dict)
    # Let's try a nonsense word: "گگگلوو"
    oov_word = "گگگلوو" 
    
    print(f"\nTesting OOV Word: {oov_word}")
    
    res_default = g2p_default(oov_word)
    print(f"Default (False): {res_default}")
    
    res_espeak = g2p_espeak(oov_word)
    print(f"Espeak (True):   {res_espeak}")
    
    # Logic: Default returns word itself ['گگگلوو']
    # Espeak returns phonemes ( IPA characters )
    if res_default == [oov_word] and res_espeak != [oov_word]:
        print("  [PASS] Espeak fallback worked (returned different output than input).")
        # Check if output looks like IPA? (contains latin chars)
        if any(c.isascii() for c in res_espeak[0]):
             print("  [PASS] Output contains ASCII/IPA characters.")
    else:
        print("  [WARN] Comparison failed. Is the word in the dictionary?")

if __name__ == "__main__":
    test_g2p()
