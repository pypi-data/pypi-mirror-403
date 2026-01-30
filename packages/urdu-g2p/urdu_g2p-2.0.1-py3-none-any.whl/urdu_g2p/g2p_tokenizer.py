from typing import List, Dict, Optional, Union
from abc import ABC, abstractmethod
import logging
import re
import os

# Base Tokenizer
class Tokenizer(ABC):
    """Abstract base class for tokenizers, defining common interface."""

    @abstractmethod
    def texts_to_token_ids(self, texts: List[str]) -> List[List[int]]:
        """Convert list of texts to list of token id sequences."""
        raise NotImplementedError

    @abstractmethod
    def texts_to_tokens(self, texts: List[str]) -> List[List[str]]:
        """Convert list of texts to list of token sequences."""
        raise NotImplementedError

    @abstractmethod
    def tokens_to_token_ids(self, tokens: List[List[str]]) -> List[List[int]]:
        """Convert list of token sequences to list of token id sequences."""
        raise NotImplementedError

# ----------------------------------------------------------------------
# G2PTokenizer (Existing/Internal) - Adapted to match Interface?
# The user said "G2PTokenizer[already]". 
# I will output the *original* G2PTokenizer class as I implemented it, 
# but maybe add the interface methods if needed. 
# Or just leave it as standalone since it's used by g2p.py internally.
# I will keep it standalone to avoid breaking g2p.py.
# ----------------------------------------------------------------------

from .vocab import LEGAL_OUTPUT_PHONEMES, normalize_output

class G2PTokenizer:
    """
    Tokenizer for mapping Urdu G2P phonemes to integer IDs and back.
    Based on the strict LEGAL_OUTPUT_PHONEMES set.
    """
    
    def __init__(self, special_tokens: Optional[List[str]] = None):
        self.phonemes = sorted(list(LEGAL_OUTPUT_PHONEMES))
        
        # Dynamic Special Tokens
        self.special_tokens = special_tokens if special_tokens is not None else []
        
        # Build Vocabulary
        self.vocab: Dict[str, int] = {}
        self.id_to_token: Dict[int, str] = {}
        
        idx = 0
        for token in self.special_tokens:
            self.vocab[token] = idx
            self.id_to_token[idx] = token
            idx += 1
            
        # Ensure space is in vocab
        if " " not in self.vocab:
            self.vocab[" "] = idx
            self.id_to_token[idx] = " "
            idx += 1
            
        for p in self.phonemes:
            if p not in self.vocab:
                self.vocab[p] = idx
                self.id_to_token[idx] = p
                idx += 1
                
        self.vocab_size = len(self.vocab)
        
        # Helpers
        self.pad_id = self.vocab.get("<pad>")
        self.unk_id = self.vocab.get("<unk>")
        self.bos_id = self.vocab.get("<bos>")
        self.eos_id = self.vocab.get("<eos>")

    def tokenize(self, text: str) -> List[str]:
        text = normalize_output(text)
        import re
        sorted_phonemes = sorted(self.vocab.keys(), key=len, reverse=True)
        valid_tokens = [re.escape(p) for p in sorted_phonemes if p not in self.special_tokens]
        if not valid_tokens:
             valid_tokens = ['.']

        pattern = '|'.join(valid_tokens)
        tokens = []
        full_pattern = re.compile(f"({pattern}|.)")
        for match in full_pattern.finditer(text):
             tokens.append(match.group())
        return tokens

    def encode(self, text: str, special_tokens: Union[List[str], Dict[str, str]] = None) -> List[int]:
        ids = []
        if special_tokens:
            tokens_to_add = []
            if isinstance(special_tokens, dict):
                tokens_to_add = list(special_tokens.values())
            elif isinstance(special_tokens, list):
                tokens_to_add = special_tokens
            
            for t in tokens_to_add:
                if t in self.vocab:
                    ids.append(self.vocab[t])
                # else ignore

        tokens = self.tokenize(text)
        for token in tokens:
            if token in self.vocab:
                ids.append(self.vocab[token])
            else:
                if self.unk_id is not None:
                    ids.append(self.unk_id)
        return ids

    def decode(self, ids: List[int], skip_special_tokens: bool = True) -> str:
        tokens = []
        for i in ids:
            if i in self.id_to_token:
                token = self.id_to_token[i]
                if skip_special_tokens and token in self.special_tokens:
                    continue
                tokens.append(token)
        return "".join(tokens)

    def save(self, path: str):
        import json
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({
                'vocab': self.vocab,
                'special_tokens': self.special_tokens
            }, f, ensure_ascii=False, indent=2)
            
    @classmethod
    def load(cls, path: str):
        import json
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        instance = cls(special_tokens=data.get('special_tokens', []))
        instance.vocab = data['vocab']
        instance.id_to_token = {int(k) if k.isdigit() else k: v for v, k in instance.vocab.items()}
        instance.id_to_token = {v: k for k, v in instance.vocab.items()}
        instance.vocab_size = len(instance.vocab)
        return instance


# ----------------------------------------------------------------------
# NEW TOKENIZER FRAMEWORK
# ----------------------------------------------------------------------

class SimpleTokenizer(Tokenizer):
    """The simplest tokenizer, treat every character as a token."""

    def __init__(self, token_file: Optional[str] = None):
        self.has_tokens = False
        if token_file is None:
            logging.debug("Initialize Tokenizer without tokens file.")
            return
        self.token2id: Dict[str, int] = {}
        with open(token_file, "r", encoding="utf-8") as f:
            for line in f.readlines():
                info = line.rstrip().split("\t")
                if len(info) >= 2:
                    token, id = info[0], int(info[1])
                    if token not in self.token2id:
                        self.token2id[token] = id
        
        self.pad_id = self.token2id.get("_")  # padding
        self.vocab_size = len(self.token2id)
        self.has_tokens = True

    def texts_to_token_ids(self, texts: List[str]) -> List[List[int]]:
        return self.tokens_to_token_ids(self.texts_to_tokens(texts))

    def texts_to_tokens(self, texts: List[str]) -> List[List[str]]:
        tokens_list = [list(texts[i]) for i in range(len(texts))]
        return tokens_list

    def tokens_to_token_ids(self, tokens_list: List[List[str]]) -> List[List[int]]:
        assert self.has_tokens, "Please initialize Tokenizer with a tokens file."
        token_ids_list = []
        for tokens in tokens_list:
            token_ids = []
            for t in tokens:
                if t not in self.token2id:
                    logging.debug(f"Skip OOV {t}")
                    continue
                token_ids.append(self.token2id[t])
            token_ids_list.append(token_ids)
        return token_ids_list


class EmiliaTokenizer(Tokenizer):
    """
    Emilia Tokenizer adapted for Urdu G2P.
    Connects to UrduG2P for phonemization.
    """
    def __init__(self, token_file: Optional[str] = None, token_type="phone", g2p_kwargs: dict = None):
        assert token_type == "phone", f"Only support phone tokenizer for Emilia, but get {token_type}."

        # Delayed import to avoid circular dependency
        from .g2p import UrduG2P
        self.g2p = UrduG2P(**(g2p_kwargs or {}))

        self.has_tokens = False
        if token_file is None:
            return
            
        self.token2id: Dict[str, int] = {}
        with open(token_file, "r", encoding="utf-8") as f:
            for line in f.readlines():
                info = line.rstrip().split("\t")
                if len(info) >= 2:
                    token, id = info[0], int(info[1])
                    if token not in self.token2id:
                        self.token2id[token] = id
                        
        self.pad_id = self.token2id.get("_")
        self.vocab_size = len(self.token2id)
        self.has_tokens = True

    def texts_to_token_ids(self, texts: List[str]) -> List[List[int]]:
        return self.tokens_to_token_ids(self.texts_to_tokens(texts))

    def preprocess_text(self, text: str) -> str:
        return self.map_punctuations(text)
        
    def map_punctuations(self, text):
        # Basic mapping
        text = text.replace("，", ",").replace("。", ".").replace("！", "!")
        text = text.replace("？", "?").replace("；", ";").replace("：", ":")
        return text

    def texts_to_tokens(self, texts: List[str]) -> List[List[str]]:
        """Convert texts to phonemes using UrduG2P."""
        # Preprocess
        texts = [self.preprocess_text(t) for t in texts]
        
        phoneme_list = []
        for text in texts:
            # Call UrduG2P
            # Note: g2p returns List[str] (phonemes)
            phones = self.g2p(text)
            phoneme_list.append(phones)
        return phoneme_list

    def tokens_to_token_ids(self, tokens_list: List[List[str]]) -> List[List[int]]:
        assert self.has_tokens, "Please initialize Tokenizer with a tokens file."
        token_ids_list = []
        for tokens in tokens_list:
            token_ids = []
            for t in tokens:
                if t not in self.token2id:
                    # fallback check or skip
                    continue
                token_ids.append(self.token2id[t])
            token_ids_list.append(token_ids)
        return token_ids_list


class DialogTokenizer(EmiliaTokenizer):
    def __init__(self, token_file: Optional[str] = None, token_type="phone", g2p_kwargs: dict = None):
        super().__init__(token_file=token_file, token_type=token_type, g2p_kwargs=g2p_kwargs)
        if token_file and "[S1]" in self.token2id:
            self.spk_a_id = self.token2id["[S1]"]
            self.spk_b_id = self.token2id.get("[S2]")

    def preprocess_text(self, text: str) -> str:
        # User defined logic for dialogues
        text = re.sub(r"\s*(\[S[12]\])\s*", r"\1", text)
        text = self.map_punctuations(text)
        return text

def add_tokens(cut_set, tokenizer_name: str, token_file: str = None):
    """Helper to apply tokenization to a CutSet (lhotse-like structure)."""
    tokenizer = None
    if tokenizer_name == "emilia":
        tokenizer = EmiliaTokenizer(token_file=token_file)
    elif tokenizer_name == "dialog":
        tokenizer = DialogTokenizer(token_file=token_file)
    elif tokenizer_name == "simple":
        tokenizer = SimpleTokenizer(token_file=token_file)
    else:
        raise ValueError(f"Unsupported tokenizer: {tokenizer_name}.")

    def _prepare_cut(cut):
        if hasattr(cut, 'supervisions') and len(cut.supervisions) >= 1:
            text = cut.supervisions[0].text
            tokens = tokenizer.texts_to_tokens([text])[0]
            # Assuming cut.supervisions[0] is mutable
            cut.supervisions[0].tokens = tokens
        return cut

    if hasattr(cut_set, 'map'):
         return cut_set.map(_prepare_cut)
    return cut_set

