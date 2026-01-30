import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from urdu_g2p import UrduG2P

def test_api():
    print("Testing API Fallback Defaults...")
    
    # 1. Default (should be 'auto' -> True)
    g2p_auto = UrduG2P() 
    oov = "گگگلوو"
    res = g2p_auto(oov)
    print(f"Default (Auto) for {oov}: {res}")
    
    # Check if we got IPA (fallback worked)
    is_ipa = any(c.isascii() for c in res[0])
    if is_ipa:
        print("  [PASS] Default is Auto (Fallback Enabled).")
    else:
        print("  [FAIL] Default did not use Fallback.")

    # 2. Explicit False
    g2p_false = UrduG2P(fallback=False)
    res2 = g2p_false(oov)
    print(f"Fallback=False for {oov}: {res2}")
    
    if res2[0] == oov:
        print("  [PASS] Fallback=False returned original word.")
    else:
        print("  [FAIL] Fallback=False still returned IPA?")

if __name__ == "__main__":
    test_api()
