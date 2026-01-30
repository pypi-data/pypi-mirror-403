# Urdu G2P - Grapheme-to-Phoneme Converter

![Urdu G2P Banner](assets/banner.png)

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: Non-Commercial](https://img.shields.io/badge/License-Non--Commercial-red.svg)](#license)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)]()
[![PyPI version](https://img.shields.io/pypi/v/urdu-g2p)](https://pypi.org/project/urdu-g2p/)

> **Author:** Humair Munir Awan (<humairmunirawan@gmail.com>)

A high-performance, production-ready **Grapheme-to-Phoneme (G2P)** library for Urdu. Converts Urdu text to IPA (International Phonetic Alphabet) phonemes using a massive dictionary with intelligent fallback mechanisms.

---

## ✨ Features

![Features](assets/features.png)

- **Refined Dictionary**: 323,000+ single-word entries (634k+ total data points managed)
- **Streaming & Memory Efficiency**: Process multi-GB files line-by-line with constant low RAM usage
- **Smart Fallback**: Automatic `espeak-ng` fallback for out-of-vocabulary (OOV) words
- **Robust Input Handling**: Automatically filters emojis, symbols, and nonsense characters
- **Quote Normalization**: Unifies all quote variants (`"`, `“`, `”`, `‘`, `’`) to a single `'`
- **Punctuation Mapping**: Maps Urdu punctuation (`۔`, `،`, `؟`) to custom symbols (default: `|`, `~`, `?`)
- **Vowel Length Normalization**: Collapses repeated vowels (e.g., `iii` -> `iː`, `aa` -> `aː`)
- **Configurable Output**: Remove stress markers, language tags, and syllable dots
- **Diverse Output Formats**: Support for JSON, Dot-separated, and detailed token analytics
- **High Performance**: 168,000+ chars/sec throughput with LRU caching
- **Type-Safe API**: Full Python type hints with comprehensive docstrings

---

## 🔄 How It Works

![Workflow](assets/workflow.png)

1. **Input**: Urdu text (with optional mixed English, numbers, emojis)
2. **Text Cleaning**: Filters out symbols, emojis, and non-linguistic characters
3. **Dictionary Lookup**: Searches 478K+ word dictionary with smart diacritic handling
4. **Fallback**: Uses `espeak-ng` for OOV words with IPA normalization
5. **Output**: Clean IPA phonemes ready for TTS or linguistic analysis

---

## 📦 Installation

### From PyPI (Recommended)

```bash
pip install urdu-g2p
```

### From Source

```bash
# Clone the repository
git clone https://github.com/humair-m/urdu-g2p.git
cd urdu-g2p

# Install the package
pip install .
```

### Dependencies

- **Python 3.8+**
- **espeak-ng** (Required for OOV fallback)

```bash
# Ubuntu/Debian
sudo apt-get install espeak-ng

# macOS
brew install espeak-ng

# Windows
# Download from: https://github.com/espeak-ng/espeak-ng/releases
```

---

## 🎯 Quick Start

### Python API

```python
from urdu_g2p import UrduG2P

# Initialize with default settings
g2p = UrduG2P()

# Basic conversion
text = "پاکستان زندہ باد"
phonemes = g2p(text)
print(' '.join(phonemes))
# Output: paːkɪsˈt̪aːn zɪnˈd̪ə baːd̪

# With stress removal
g2p_clean = UrduG2P(ignore_stress=True)
phonemes = g2p_clean("مجھے پاکستان پسند ہے")
print(' '.join(phonemes))
# Output: mʊd͡ʒeː paːkɪst̪aːn pəsənd̪ ɦɛ
```

### Command Line Interface (CLI)

```bash
# Basic usage
python inference.py "اسلام آباد"
# Output: ɪslaːm aːbaːd̪

# JSON output with details
python inference.py "ٹیسٹ" --format json --pretty

# Dot-separated (TTS style)
python inference.py "ہیلو" --format dot
# Output: heː.loː

# Remove stress markers
python inference.py "مجھے" --strip-stress
# Output: mʊd͡ʒeː
```

---

## 🔧 Advanced Usage

### Configuration Options

```python
g2p = UrduG2P(
    fallback='auto',           # 'auto', True, or False
    diacritic_mode='auto',     # 'auto', 'ignore', 'strict'
    ignore_tag=True,           # Remove (en)/(ur) language tags
    ignore_stress=False,       # Remove stress markers (ˈ)
    save_oov_path=None         # Path to save OOV words
)
```

### OOV Tracking & Saving

Track words not found in the dictionary to improve your dataset:

```python
g2p = UrduG2P(save_oov_path="oov_words.json")
g2p("یہ ایک ٹیسٹ ورڈ ہے۔")
g2p.save_oov()  # Saves OOV words to JSON
print(g2p.get_oov())  # View OOV words
```

### Diacritic Modes

Handle text with or without vowel marks (Zer/Zabar/Pesh):

```python
# Mode: 'ignore' (Best for heavily diacritized text)
g2p = UrduG2P(diacritic_mode='ignore')
print(g2p("اَلسَّلَامُ"))  # -> æs.səˈlaːm

# Mode: 'strict' (Exact match only)
g2p = UrduG2P(diacritic_mode='strict')
```

### Detailed Inference (JSON)

Get rich information about each token:

```python
from inference import UrduG2PInference

inference = UrduG2PInference()
result = inference.predict("گوگل", format='json')
print(result['tokens'][0])
# {
#   'word': 'گوگل',
#   'phoneme': 'ɡuːɡəl',
#   'source': 'dict',
#   'exact_match': True
# }
```

### Custom Phonemes

Override dictionary or fallback results:

```python
g2p = UrduG2P()
g2p.add_custom_phoneme("آرٹیفیشل", "ɑːrʈiːfɪʃəl")
```

---

## 📁 Project Structure

```
urdu-g2p/
├── urdu_g2p/                   # Main package
│   ├── data/                   # Phoneme dictionary (30MB+)
│   │   └── phoneme_map.json    # 478K+ word mappings
│   └── g2p.py                  # Core G2P logic
├── tests/                      # Test suite
│   ├── test_basic.py
│   ├── test_comprehensive.py
│   ├── test_robustness.py      # Emoji/symbol filtering tests
│   └── benchmark.py            # Performance tests
├── examples/
│   └── demo.py                 # Usage examples
├── assets/                     # Images for documentation
├── inference.py                # CLI tool
├── pyproject.toml              # Build configuration
└── README.md                   # This file
```

---

## 📊 Performance

| Metric | Value |
|--------|-------|
| Clean Dictionary | 323,000+ single words |
| Unique IPA Characters | 92 (Optimized) |
| Throughput | 168,000+ chars/sec |
| Memory Usage | Streaming (Files) / ~150MB (Dict) |

---

## 📚 Citation

If you use this library in your research, please cite:

```bibtex
@software{urdu_g2p_2026,
  author       = {Awan, Humair Munir},
  title        = {Urdu G2P: A High-Performance Grapheme-to-Phoneme Converter for Urdu},
  year         = {2026},
  publisher    = {GitHub},
  url          = {https://github.com/humair-m/urdu-g2p},
  version      = {2.0.0},
  note         = {478,000+ word dictionary with espeak-ng fallback. Non-commercial use only.}
}
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`pytest tests/`)
4. Commit your changes
5. Push to the branch
6. Open a Pull Request

---

## 📄 License

**⚠️ NON-COMMERCIAL USE ONLY**

This project (both code and data) is licensed for **non-commercial use only**.

- ✅ Academic research
- ✅ Personal projects  
- ✅ Educational purposes
- ❌ Commercial products/services
- ❌ Monetization of any kind

**For commercial licensing, please contact:**  
📧 [humairmunirawan@gmail.com](mailto:humairmunirawan@gmail.com)

See the [LICENSE](LICENSE) file for full details.

---

<p align="center">
  Made with ❤️ for the Urdu language
</p>
