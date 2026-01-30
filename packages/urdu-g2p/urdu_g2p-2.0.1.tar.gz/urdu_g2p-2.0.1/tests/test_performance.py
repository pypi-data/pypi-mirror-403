import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from urdu_g2p import UrduG2P
import time

def test_long_para():
    g2p = UrduG2P()
    
    # Composing a long paragraph
    para = (
        "اچھا، تو میرے پیارے طالب علم، جب ہم خاندانی رشتے کہتے ہیں تو ہمارے ذہن میں سب سے پہلے کیا آتا ہے؟ "
        "میرے خیال میں یہ وہ مضبوط بندھن ہے جو ہمیں ایک دوسرے سے جوڑتا ہے۔ "
        "زندگی میں ہر موڑ پر، چاہے خوشی ہو یا غم، خاندان ہی ہمارا سب سے بڑا سہارا ہوتا ہے۔ "
        "آج کل کے دور میں جہاں ہر کوئی اپنی اپنی مصروفیات میں گم ہے، رشتوں کی اہمیت اور بھی بڑھ گئی ہے۔ "
        "شوکت خانم جیسے ادارے بھی اسی جذبے کے تحت کام کر رہے ہیں کہ دکھی انسانیت کی خدمت کی جائے۔ "
        "ہمیں چاہیے کہ ہم اپنے والدین، بہن بھائیوں اور دیگر عزیز و اقارب کے ساتھ حسن سلوک سے پیش آئیں اور ان کا خیال رکھیں۔"
    )
    
    print(f"Text Length: {len(para)} chars")
    print("Processing...")
    
    start_time = time.time()
    phonemes = g2p(para)
    end_time = time.time()
    
    print(f"Time taken: {end_time - start_time:.4f} seconds")
    print("\nOriginal Text:")
    print(para)
    print("\nPhonemes:")
    print(' '.join(phonemes))
    
    unknowns = [p for p in phonemes if any("\u0600" <= c <= "\u06FF" for c in p)]
    if unknowns:
        print(f"\nPotential OOV words (kept as Urdu): {unknowns}")

if __name__ == "__main__":
    test_long_para()
