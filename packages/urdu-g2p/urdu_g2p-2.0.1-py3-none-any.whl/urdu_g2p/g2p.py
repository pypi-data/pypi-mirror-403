"""
Urdu Grapheme-to-Phoneme (G2P) Converter
==========================================
Author: Humair Munir Awan
Version: 2.0.0
Last Updated: January 2026

Enhanced with smart diacritic handling and inline phoneme notation

Features:
- Dictionary-based lookup with espeak-ng fallback
- Smart diacritic handling (auto/ignore/strict modes)
- Inline phoneme notation: word[/phoneme/]
- Custom phoneme support
- Greedy tokenization for compound words
- Priority-based lookup system

Usage:
    from urdu_g2p import UrduG2P
    
    g2p = UrduG2P()
    text = "پاکستان[/paːkɪsˈt̪aːn/] ایک خوبصورت ملک ہے۔"
    phonemes = g2p(text)
"""

import subprocess
"""
Urdu G2P - A High-Performance Grapheme-to-Phoneme Converter for Urdu.
Author: Humair Munir Awan (<humairmunirawan@gmail.com>)
"""

import os
import json
import re
import unicodedata
from functools import lru_cache
from typing import List, Dict, Set, Union, Optional, Tuple

from .vocab import clean_input, normalize_output, LEGAL_INPUT, get_legal_output_chars
from .g2p_tokenizer import G2PTokenizer

class UrduG2P:
    # Pre-compiled regex patterns for performance
    # Includes standard punctuation plus Urdu specific (،؛؟۔) and quoting (""''`‘’“”)
    _RE_PUNCTUATION = re.compile(r'[.,!?;:()\[\]{}"\'`‘’“”،؛؟۔\-_*\|~]')
    _RE_INLINE_PHONEME = re.compile(r'(\S+)\[/([^\]]+)/\]')
    _RE_GEMINATE = re.compile(r'([ee|ii|oo|uu])\1')
    _RE_VOWEL_LENGTH = re.compile(r'([aeiouəɪʊAEIOU])\1+')  # 2+ identical vowels -> length mark
    _RE_DENTAL_T = re.compile(r't(?!͡)(?!̪)(?!ʈ)')
    _RE_DENTAL_D = re.compile(r'd(?!͡)(?!̪)(?!ɖ)')
    _RE_NASAL_ORDER1 = re.compile(r'([aeiouəɪʊ])ː̃')
    _RE_NASAL_ORDER2 = re.compile(r'([aeiouəɪʊ])̃ː')
    
    # Allowed punctuation set for filtering
    _ALLOWED_PUNCTUATION = set('.,!?;:()[]{}"\'`‘’“”،؛؟۔-_*|~ ')
    
    # Default punctuation mapping
    _DEFAULT_PUNCT_MAP = {'،': '~', '۔': '|', '؟': '?'}

    def __init__(self, data_path: Optional[str] = None, fallback: Union[str, bool] = 'auto', 
                 custom_phonemes: Optional[Dict[str, str]] = None, diacritic_mode: str = 'auto', 
                 save_oov_path: Optional[str] = None, ignore_tag: bool = True, ignore_stress: bool = False,
                 map_punct: Optional[Dict[str, str]] = None, warn_only: bool = False):
        """
        Args:
            data_path (str): Path to custom phoneme JSON.
            fallback (str/bool): 'auto' (or True) enables espeak fallback. False disables it.
            custom_phonemes (dict): Custom word->phoneme mappings that override dictionary.
            diacritic_mode (str): 'auto' (smart), 'ignore' (always strip), 'strict' (never strip)
            save_oov_path (str): Optional path to save OOV words (e.g., 'data/oov.json')
            ignore_tag (bool): If True, removes language tags like (en), (ur) from espeak output.
            ignore_stress (bool): If True, removes primary stress markers (ˈ) from output.
            map_punct (dict): Map of Urdu punctuation to output symbols. Default: {'،': '~', '۔': '|', '؟': '?'}
            warn_only (bool): If True, illegal input characters are ignored/stripped. If False (default), raises AssertionError.
        """
        if data_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            data_path = os.path.join(base_dir, 'data', 'phoneme_map.json')
        
        self.phoneme_map = {}
        self.phoneme_map_with_diacritics = {}  # For exact matches
        self.max_word_len = 0
        self.diacritic_mode = diacritic_mode  # 'auto', 'ignore', or 'strict'
        self.ignore_tag = ignore_tag
        self.ignore_stress = ignore_stress
        
        # Punctuation mapping with validation
        self.map_punct = map_punct if map_punct is not None else self._DEFAULT_PUNCT_MAP.copy()
        self._validate_punct_map()
        
        # Custom phonemes (highest priority)
        self.custom_phonemes = custom_phonemes or {}
        
        # Resolve fallback setting
        if fallback == 'auto' or fallback is True:
            self.fallback_enabled = True
        else:
            self.fallback_enabled = False
        
        # OOV tracking
        self.save_oov_path = save_oov_path
        self._oov_words = set()  # Track unique OOV words
            
        self.load_map(data_path)
        
        # Validation settings
        self.warn_only = warn_only
        
        # Initialize Tokenizer
        self.tokenizer = G2PTokenizer()
        
        # Cache valid sets for fast validation
        self._valid_input_chars = set(LEGAL_INPUT)
        self._valid_input_chars.add(' ') # Allow space explicitly
        self._valid_output_chars = set(get_legal_output_chars())
        self._valid_output_chars.add(' ')  # Allow space
        self._valid_output_chars.add('|')  # Allow punctuation mapped symbols
        self._valid_output_chars.add('~')
        self._valid_output_chars.add('?')
        # Also need to add punctuation map values if they are not standard phonemes:
        for val in self.map_punct.values():
             for c in val:
                 if c != ' ':
                      self._valid_output_chars.add(c)
        
    # Urdu diacritics as a SET for O(1) membership testing
    URDU_DIACRITICS = frozenset([
        '\u064B', '\u064C', '\u064D', '\u064E', '\u064F', '\u0650',
        '\u0651', '\u0652', '\u0653', '\u0654', '\u0655', '\u0656',
        '\u0657', '\u0658', '\u0670',
    ])
    
    # Translation table for fast diacritic stripping
    _DIACRITIC_TRANS = str.maketrans('', '', ''.join(URDU_DIACRITICS))
    
    def _validate_punct_map(self):
        """Validate punctuation map keys/values don't conflict with phoneme chars."""
        # IPA chars that should not be used as punct symbols
        reserved_ipa = set('aeiouəɪʊɛɔæɑːˈˌ̃ʰʱɦpbtdkgmnŋɳɲfvszʃʒxɣhʔlrɽɹwjt͡ʃd͡ʒ')
        
        for key, value in self.map_punct.items():
            # Value should not be a reserved IPA char
            if value in reserved_ipa:
                raise ValueError(f"map_punct value '{value}' conflicts with IPA phoneme characters")
            # Value should be a simple symbol or token
            if ' ' in value:
                 raise ValueError(f"map_punct value '{value}' cannot contain spaces")
            if len(value) > 32:
                raise ValueError(f"map_punct value '{value}' is too long (max 32 chars)")
    
    def _has_diacritics(self, text: str) -> bool:
        """Check if text contains any Urdu diacritics. O(n) with set lookup."""
        return any(c in self.URDU_DIACRITICS for c in text)
    
    def _strip_diacritics(self, text: str) -> str:
        """Remove Urdu diacritics from text using fast translate."""
        return text.translate(self._DIACRITIC_TRANS)
    
    def load_map(self, path: str):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Phoneme map not found at {path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            raw_map = json.load(f)
        
        # Build both maps
        for word, phoneme in raw_map.items():
            word_norm = unicodedata.normalize('NFC', word)
            
            # Store original (with diacritics if present)
            self.phoneme_map_with_diacritics[word_norm] = phoneme
            
            # Also store without diacritics
            word_no_diac = self._strip_diacritics(word_norm)
            if word_no_diac not in self.phoneme_map:
                self.phoneme_map[word_no_diac] = phoneme
        
        # Calculate max word length
        all_words = list(self.phoneme_map.keys()) + list(self.phoneme_map_with_diacritics.keys())
        if all_words:
            self.max_word_len = max(len(w) for w in all_words)
    
    def add_custom_phoneme(self, word: str, phoneme: str):
        """Add or update a custom phoneme mapping at runtime."""
        word_norm = unicodedata.normalize('NFC', word)
        self.custom_phonemes[word_norm] = phoneme
        
        # Also add without diacritics
        word_no_diac = self._strip_diacritics(word_norm)
        if word_no_diac != word_norm:
            self.custom_phonemes[word_no_diac] = phoneme
    
    def load_custom_phonemes(self, custom_path: str):
        """Load custom phonemes from a JSON file."""
        if not os.path.exists(custom_path):
            raise FileNotFoundError(f"Custom phoneme file not found at {custom_path}")
        
        with open(custom_path, 'r', encoding='utf-8') as f:
            custom_map = json.load(f)
        
        for word, phoneme in custom_map.items():
            self.add_custom_phoneme(word, phoneme)
    
    def _parse_inline_phonemes(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Parse inline phoneme notation: word[/phoneme/]
        Returns: (cleaned_text, inline_phoneme_map)
        
        Example: "پاکستان[/paːkɪsˈt̪aːn/] ہے" -> ("پاکستان ہے", {"پاکستان": "paːkɪsˈt̪aːn"})
        """
        inline_map = {}
        
        # Pattern: word[/phoneme/]
        # Captures the word and the phoneme inside [/...../]
        pattern = r'(\S+)\[/([^\]]+)/\]'
        
        def replacer(match):
            word = match.group(1)
            phoneme = match.group(2)
            word_norm = unicodedata.normalize('NFC', word)
            inline_map[word_norm] = phoneme
            return word  # Return just the word without the brackets
        
        cleaned_text = re.sub(pattern, replacer, text)
        return cleaned_text, inline_map
    
    def _lookup_phoneme(self, word: str, use_auto_diacritic: bool = True) -> Optional[str]:
        """
        Lookup phoneme with smart diacritic handling.
        
        Args:
            word: The word to lookup
            use_auto_diacritic: If True and diacritic_mode='auto', check if word has diacritics
        
        Returns phoneme or None if not found.
        """
        word_norm = unicodedata.normalize('NFC', word)
        
        # 1. Check custom phonemes first (highest priority)
        if word_norm in self.custom_phonemes:
            return self.custom_phonemes[word_norm]
        
        # 2. Determine whether to strip diacritics
        should_strip = False
        
        if self.diacritic_mode == 'ignore':
            should_strip = True
        elif self.diacritic_mode == 'strict':
            should_strip = False
        elif self.diacritic_mode == 'auto' and use_auto_diacritic:
            # Smart mode: only strip if word has NO diacritics
            should_strip = not self._has_diacritics(word_norm)
        
        # 3. Try exact match first (always)
        if word_norm in self.phoneme_map_with_diacritics:
            return self.phoneme_map_with_diacritics[word_norm]
        
        # 4. Try without diacritics if appropriate
        if should_strip:
            word_no_diac = self._strip_diacritics(word_norm)
            
            # Check custom without diacritics
            if word_no_diac in self.custom_phonemes:
                return self.custom_phonemes[word_no_diac]
            
            # Check main map without diacritics
            if word_no_diac in self.phoneme_map:
                return self.phoneme_map[word_no_diac]
        
        return None

    def _clean_text(self, text: str) -> str:
        """
        Filters text using the strict vocab.clean_input() definition.
        """
        return clean_input(text)

    def _tokenize_basic(self, text: str) -> List[str]:
        """Splits by space and punctuation."""
        text = text.replace('؟', ' ')
        text = self._RE_PUNCTUATION.sub(' ', text)
        tokens = text.split()
        return [t.strip() for t in tokens if t.strip()]

    def _greedy_split(self, text: str, inline_map: Optional[Dict[str, str]] = None) -> List[str]:
        """
        Splits text into dictionary words using MaxMatch.
        Now supports inline phoneme map.
        """
        if inline_map is None:
            inline_map = {}
            
        segments = []
        i = 0
        n = len(text)
        
        while i < n:
            if text[i].isspace():
                i += 1
                continue

            matched = False
            end_candidate = min(n, i + self.max_word_len + 20)  # +20 for potential diacritics
            
            for j in range(end_candidate, i, -1):
                chunk = text[i:j]
                chunk_norm = unicodedata.normalize('NFC', chunk)
                
                # Check inline map first
                if chunk_norm in inline_map:
                    segments.append(chunk_norm)
                    i = j
                    matched = True
                    break
                
                # Try lookup (handles custom, exact, and diacritic-stripped)
                phoneme = self._lookup_phoneme(chunk_norm)
                
                if phoneme is not None:
                    segments.append(chunk_norm)
                    i = j
                    matched = True
                    break
            
            if not matched:
                segments.append(text[i])
                i += 1
        
        return segments

    def _tokenize_greedy(self, text: str, inline_map: Optional[Dict[str, str]] = None) -> List[str]:
        """Forward Maximum Matching returns phonemes directly."""
        segments = self._greedy_split(text, inline_map)
        phonemes = []
        
        for s in segments:
            s_norm = unicodedata.normalize('NFC', s)
            
            # Check inline map first
            if inline_map and s_norm in inline_map:
                phonemes.append(inline_map[s_norm])
            else:
                phoneme = self._lookup_phoneme(s_norm)
                if phoneme is not None:
                    phonemes.append(phoneme)
                else:
                    phonemes.append(s)
        
        return phonemes

    def _normalize_ipa(self, ipa_text: str, strip_stress: bool = False) -> str:
        """Powerful IPA normalization (optimized with pre-compiled regex)."""
        # 0. Remove Language Tags if requested
        if self.ignore_tag:
             ipa_text = ipa_text.replace('(en)', '').replace('(ur)', '')

        # Remove dots (syllable boundaries)
        ipa_text = ipa_text.replace('.', '')

        # 1. Unicode Normalization
        ipa_text = unicodedata.normalize('NFC', ipa_text)
        
        # 2. Stress markers (using translate for speed)
        if strip_stress:
            ipa_text = ipa_text.replace('ˈ', '').replace('ˌ', '')
        else:
            ipa_text = ipa_text.replace('ˌ', '')
            
        # 3. Collapse consecutive identical vowels FIRST (before other normalizations)
        ipa_text = self._RE_VOWEL_LENGTH.sub(r'\1ː', ipa_text)
        
        # 4. Consonant Aliasing (chained replace is fast for small strings)
        ipa_text = (ipa_text
            .replace('ʐ', 'z').replace('ʂ', 's')
            .replace('c', 't͡ʃ').replace('ɟ', 'd͡ʒ')
            .replace('r.', 'ɽ')
            .replace('ɦ', 'h').replace('ʱ', 'ʰ')  # H-Unification
            .replace('ʌ', 'ə').replace('a', 'ə')  # Schwa unification
            .replace('əː', 'aː')  # Recover long 'a'
            .replace('ɛː', 'ɛ').replace('ɔː', 'ɔ')
            .replace('aa', 'aː').replace('ee', 'eː')
            .replace('ii', 'iː').replace('oo', 'oː').replace('uu', 'uː')
        )
        
        # 4. Word-level processing
        ipa = []
        for word in ipa_text.split():
            word = self._RE_GEMINATE.sub(r'\1ː', word)
            if word.endswith('i'): word += 'ː'
            if word.endswith('u'): word += 'ː'
            ipa.append(word)
        ipa_text = ' '.join(ipa)
        
        # 5. Dentalization & Nasalization (pre-compiled regex)
        
        # 5. Dentalization & Nasalization (pre-compiled regex)
        ipa_text = self._RE_DENTAL_T.sub('t̪', ipa_text)
        ipa_text = self._RE_DENTAL_D.sub('d̪', ipa_text)
        ipa_text = self._RE_NASAL_ORDER1.sub(r'\1̃ː', ipa_text)
        ipa_text = self._RE_NASAL_ORDER2.sub(r'\1̃ː', ipa_text)
        
        # 6. Final normalization via vocab rules (affricates, rhotics, etc.)
        return normalize_output(ipa_text.strip())

    @lru_cache(maxsize=4096)
    def _espeak_cached(self, word: str) -> str:
        """Cached espeak call for repeated OOV words."""
        try:
            result = subprocess.run(
                ['espeak-ng', '-q', '-v', 'ur', '--ipa', word],
                capture_output=True,
                text=True,
                check=False
            )
            return result.stdout.strip() or word
        except Exception:
            return word

    def _predict_espeak(self, word: str, strip_stress: bool = False) -> str:
        """Use espeak-ng for OOV words (with caching)."""
        # Track OOV word
        self._oov_words.add(word)
        
        phone = self._espeak_cached(word)
        if phone and phone != word:
            return self._normalize_ipa(phone, strip_stress=strip_stress)
        return word

    def __call__(self, text: str, lookup: str = 'basic', strip_stress: Optional[bool] = None, take_phonomes: bool = False) -> List[str]:
        return self.predict(text, lookup, strip_stress, take_phonomes)

    _RE_QUOTES_NORM = re.compile(r"['\"“”.‘`’]+") # Matches sequence of any quote chars

    def _normalize_quotes(self, text: str) -> str:
        """Normalize all quote variants to single straight quote."""
        return self._RE_QUOTES_NORM.sub("'", text)

    def predict(self, text: str, lookup: str = 'basic', strip_stress: Optional[bool] = None, take_phonomes: bool = False) -> Union[List[str], List[int]]:
        """
        Converts Urdu text to list of phonemes (or IDs).
        
        Args:
            take_phonomes (bool): If True, treats input 'text' as phoneme string and returns List[int] (IDs).
        """
        # Resolve stress option
        if strip_stress is None:
            strip_stress = self.ignore_stress
        
        if take_phonomes:
            # Passthrough mode -> Tokenize to IDs
            # If strip_stress requested, remove stress markers from text before encoding
            if strip_stress:
                text = text.replace('ˈ', '').replace('ˌ', '')
            
            return self.tokenizer.encode(text)
                
        # 1. Parse inline phonemes FIRST (before any cleaning)
        text_for_parsing = text
        text, inline_map = self._parse_inline_phonemes(text)
        
        # 2. Clean text (remove emojis/symbols)
        # We always clean input.
        text = self._clean_text(text)
        
        # 3. Normalize quotes (before punct mapping to ensure consistency)
        text = self._normalize_quotes(text)

        # 4. Apply punctuation mapping
        for punct_char, mapped_symbol in self.map_punct.items():
            text = text.replace(punct_char, f' {mapped_symbol} ')
        
        text = unicodedata.normalize('NFC', text)
        
        phonemes = []
        
        if lookup == 'greedy':
            segments = self._greedy_split(text, inline_map)
            for s in segments:
                s_norm = unicodedata.normalize('NFC', s)
                if s_norm in inline_map:
                    phonemes.append(inline_map[s_norm])
                else:
                    phoneme = self._lookup_phoneme(s_norm)
                    if phoneme is not None:
                        phonemes.append(self._normalize_ipa(phoneme, strip_stress=strip_stress))
                    else:
                        if self.fallback_enabled:
                            phonemes.append(self._predict_espeak(s_norm, strip_stress=strip_stress))
                        else:
                            phonemes.append(s_norm)
        else:
            # Basic with smart splitting
            raw_words = text.split()
            words = []
            
            for w in raw_words:
                norm_w = unicodedata.normalize('NFC', w)
                
                # Check inline map first
                if norm_w in inline_map:
                    words.append(norm_w)
                    continue
                
                # Check if known (custom, exact, or diacritic-stripped)
                phoneme = self._lookup_phoneme(norm_w)
                
                if phoneme is not None or norm_w in self.map_punct.values():
                    words.append(norm_w)
                else:
                    # OOV: Try greedy split
                    splits = self._greedy_split(norm_w, inline_map)
                    valid_splits = [s for s in splits if self._lookup_phoneme(s) is not None or s in inline_map]
                    
                    if len(splits) > 1 and len(valid_splits) > 0:
                        words.extend(splits)
                    else:
                        words.append(norm_w)

            phonemes = []
            for word in words:
                if word in inline_map:
                    phonemes.append(inline_map[word])
                elif word in self.map_punct.values():
                    phonemes.append(word)
                else:
                    phoneme = self._lookup_phoneme(word)
                    
                    if phoneme is not None:
                        phonemes.append(self._normalize_ipa(phoneme, strip_stress=strip_stress))
                    else:
                        if self.fallback_enabled:
                            phonemes.append(self._predict_espeak(word, strip_stress=strip_stress))
                        else:
                            phonemes.append(word)
                            
        # VALIDATE OUTPUT
        if not self.warn_only:
            for p in phonemes:
                for char in p:
                     if char not in self._valid_output_chars:
                          raise AssertionError(f"Illegal output character: '{char}' in phoneme: '{p}'")
        
        return phonemes
    
    def get_stats(self) -> Dict[str, Union[int, str, bool]]:
        """Return statistics about the phoneme maps."""
        return {
            'dictionary_words': len(self.phoneme_map),
            'words_with_diacritics': len(self.phoneme_map_with_diacritics),
            'custom_phonemes': len(self.custom_phonemes),
            'diacritic_mode': self.diacritic_mode,
            'fallback_enabled': self.fallback_enabled,
            'oov_count': len(self._oov_words)
        }
    
    def get_oov(self) -> Set[str]:
        """Return set of OOV words encountered."""
        return self._oov_words.copy()
    
    def clear_oov(self):
        """Clear the OOV word set."""
        self._oov_words.clear()
    
    def save_oov(self, path: Optional[str] = None) -> int:
        """
        Save OOV words to a JSON file.
        
        Args:
            path (str): Output path. Uses save_oov_path from init if not provided.
        """
        path = path or self.save_oov_path
        if not path:
            raise ValueError("No path provided. Set save_oov_path in __init__ or pass path argument.")
        
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
        
        oov_data = {
            'count': len(self._oov_words),
            'words': sorted(list(self._oov_words))
        }
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(oov_data, f, ensure_ascii=False, indent=2)
        
        return len(self._oov_words)
