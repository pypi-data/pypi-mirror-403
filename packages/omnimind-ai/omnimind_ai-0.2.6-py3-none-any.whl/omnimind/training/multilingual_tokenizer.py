"""
OMNIMIND Multilingual Tokenizer
Production-grade tokenizer with full Unicode support

Supports:
- Thai
- English
- Chinese/Japanese/Korean (CJK)
- European Languages (Latin Extended)
- Arabic, Hebrew, Cyrillic
- Emoji
"""
import os
import json
from typing import List, Dict, Any, Optional, Union
import torch
from jinja2 import Template

# Import OMNIMIND template
try:
    from omnimind.utils.chat_template import OMNIMIND_CHAT_TEMPLATE
except ImportError:
    OMNIMIND_CHAT_TEMPLATE = ""


class MultilingualTokenizer:
    """
    Production-ready Multilingual Character Tokenizer
    
    Covers:
    - Special tokens (system)
    - ASCII (basic Latin)
    - Latin Extended (European languages)
    - Thai
    - CJK (Chinese, Japanese Hiragana/Katakana, Korean Hangul basic)
    - Cyrillic (Russian, etc.)
    - Arabic
    - Hebrew
    - Common Punctuation & Symbols
    - Emoji (basic set)
    
    Note: For truly production-scale, consider SentencePiece or HF Tokenizers.
    This tokenizer is a good fallback for character-level modeling.
    """
    
    def __init__(self, vocab_size: int = 65536):
        self.vocab_size = vocab_size
        self.pad_token_id = 0
        self.bos_token_id = 1
        self.eos_token_id = 2
        self.unk_token_id = 3
        
        # Chat Template
        self.chat_template = OMNIMIND_CHAT_TEMPLATE
        
        # Special tokens
        self.special_tokens = {
            "<pad>": 0,
            "<bos>": 1,
            "<eos>": 2,
            "<unk>": 3,
            "<|im_start|>": 4,
            "<|im_end|>": 5,
            "<think>": 6,
            "</think>": 7,
            "<tool_call>": 8,
            "</tool_call>": 9,
            "<tool_response>": 10,
            "</tool_response>": 11,
            "<memory>": 12,
            "</memory>": 13,
        }
        
        # Build vocabulary
        self.token_to_id: Dict[str, int] = dict(self.special_tokens)
        self.id_to_token: Dict[int, str] = {v: k for k, v in self.special_tokens.items()}
        
        idx = len(self.special_tokens)
        
        # === Unicode Ranges ===
        unicode_ranges = [
            # Basic Latin (ASCII printable)
            (0x0020, 0x007E),  # Space to ~
            
            # Latin Extended (European languages: French, German, Spanish, etc.)
            (0x00A0, 0x00FF),  # Latin-1 Supplement
            (0x0100, 0x017F),  # Latin Extended-A
            (0x0180, 0x024F),  # Latin Extended-B
            
            # Thai
            (0x0E00, 0x0E7F),  # Thai
            
            # Arabic
            (0x0600, 0x06FF),  # Arabic
            
            # Hebrew
            (0x0590, 0x05FF),  # Hebrew
            
            # Cyrillic (Russian, Ukrainian, etc.)
            (0x0400, 0x04FF),  # Cyrillic
            
            # Greek
            (0x0370, 0x03FF),  # Greek and Coptic
            
            # CJK
            (0x4E00, 0x9FFF),  # CJK Unified Ideographs (Chinese)
            (0x3040, 0x309F),  # Hiragana
            (0x30A0, 0x30FF),  # Katakana
            (0xAC00, 0xD7AF),  # Hangul Syllables (Korean)
            (0x3000, 0x303F),  # CJK Symbols and Punctuation (、。「」etc.)
            (0xFF00, 0xFFEF),  # Halfwidth and Fullwidth Forms
            
            # General Punctuation
            (0x2000, 0x206F),  # General Punctuation
            (0x2070, 0x209F),  # Superscripts and Subscripts
            (0x20A0, 0x20CF),  # Currency Symbols
            
            # Mathematical Operators
            (0x2200, 0x22FF),  # Mathematical Operators
            
            # Miscellaneous Symbols
            (0x2600, 0x26FF),  # Miscellaneous Symbols (★☆♠♥ etc.)
            (0x2700, 0x27BF),  # Dingbats
            
            # Emoji (expanded subset)
            (0x1F300, 0x1F3FF),  # Misc Symbols and Pictographs
            (0x1F400, 0x1F4FF),  # Emoticons & Animals
            (0x1F500, 0x1F5FF),  # More Symbols
            (0x1F600, 0x1F64F),  # Emoticons (faces)
            (0x1F680, 0x1F6FF),  # Transport and Map Symbols
            (0x1F900, 0x1F9FF),  # Supplemental Symbols
            (0x2300, 0x23FF),   # Misc Technical (✨ is here)
        ]
        
        for start, end in unicode_ranges:
            for codepoint in range(start, end + 1):
                if idx >= vocab_size:
                    break
                try:
                    char = chr(codepoint)
                    if char not in self.token_to_id:
                        self.token_to_id[char] = idx
                        self.id_to_token[idx] = char
                        idx += 1
                except:
                    pass
            if idx >= vocab_size:
                break
        
        self._actual_vocab_size = idx
        print(f"📚 MultilingualTokenizer initialized with {idx:,} tokens")
    
    def encode(self, text: str, add_special_tokens: bool = True) -> List[int]:
        """Encode text to token IDs"""
        ids = []
        
        if add_special_tokens:
            ids.append(self.bos_token_id)
        
        for char in text:
            token_id = self.token_to_id.get(char, self.unk_token_id)
            ids.append(token_id)
        
        if add_special_tokens:
            ids.append(self.eos_token_id)
        
        return ids
    
    def decode(self, ids: List[int], skip_special_tokens: bool = True) -> str:
        """Decode token IDs to text"""
        chars = []
        for token_id in ids:
            if isinstance(token_id, torch.Tensor):
                token_id = token_id.item()
            
            if skip_special_tokens and token_id in self.special_tokens.values():
                continue
            char = self.id_to_token.get(token_id, "")
            chars.append(char)
        return "".join(chars)
    
    def apply_chat_template(
        self, 
        conversation: List[Dict[str, str]], 
        tokenize: bool = True, 
        add_generation_prompt: bool = False,
        tools: Optional[List[Dict]] = None,
        **kwargs
    ) -> Union[str, List[int]]:
        """Apply OMNIMIND chat template"""
        template = Template(self.chat_template)
        text = template.render(
            messages=conversation, 
            add_generation_prompt=add_generation_prompt,
            tools=tools,
            **kwargs
        )
        
        if tokenize:
            return self.encode(text, add_special_tokens=False)
        return text

    def __len__(self) -> int:
        return self._actual_vocab_size

    def save_pretrained(self, save_directory: str):
        """
        Save tokenizer configuration and vocabulary.
        """
        os.makedirs(save_directory, exist_ok=True)
        
        # 1. vocab.json
        vocab_path = os.path.join(save_directory, "vocab.json")
        with open(vocab_path, "w", encoding="utf-8") as f:
            json.dump(self.token_to_id, f, indent=2, ensure_ascii=False)
            
        # 2. tokenizer_config.json
        config = {
            "tokenizer_class": "MultilingualTokenizer",
            "do_lower_case": False,
            "unk_token": "<unk>",
            "pad_token": "<pad>",
            "bos_token": "<bos>",
            "eos_token": "<eos>",
            "chat_template": self.chat_template,
            "model_max_length": 8192,
            "vocab_size": self._actual_vocab_size
        }
        with open(os.path.join(save_directory, "tokenizer_config.json"), "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
            
        # 3. special_tokens_map.json
        special_tokens_map = {
            "unk_token": "<unk>",
            "pad_token": "<pad>",
            "bos_token": "<bos>",
            "eos_token": "<eos>",
            "additional_special_tokens": list(self.special_tokens.keys())[4:]  # Skip first 4
        }
        with open(os.path.join(save_directory, "special_tokens_map.json"), "w", encoding="utf-8") as f:
            json.dump(special_tokens_map, f, indent=2)
            
        # 4. chat_template.jinja
        with open(os.path.join(save_directory, "chat_template.jinja"), "w", encoding="utf-8") as f:
            f.write(self.chat_template)

        # 5. merges.txt (dummy)
        with open(os.path.join(save_directory, "merges.txt"), "w", encoding="utf-8") as f:
            f.write("# Character-level tokenizer - no merges\n")

        # 6. tokenizer.json
        tokenizer_json = {
            "version": "1.0",
            "model": {
                "type": "CharacterLevel",
                "vocab": [[k, 0.0] for k in self.token_to_id.keys()],
                "unk_id": self.unk_token_id
            },
            "added_tokens": [
                {"id": v, "content": k, "special": True} 
                for k, v in self.special_tokens.items()
            ]
        }
        with open(os.path.join(save_directory, "tokenizer.json"), "w", encoding="utf-8") as f:
            json.dump(tokenizer_json, f, indent=2, ensure_ascii=False)
            
        print(f"✅ MultilingualTokenizer saved to {save_directory}")

    @classmethod
    def from_pretrained(cls, load_directory: str) -> "MultilingualTokenizer":
        """Load tokenizer from directory"""
        vocab_path = os.path.join(load_directory, "vocab.json")
        config_path = os.path.join(load_directory, "tokenizer_config.json")
        
        if not os.path.exists(vocab_path):
            raise FileNotFoundError(f"vocab.json not found in {load_directory}")
        
        with open(vocab_path, "r", encoding="utf-8") as f:
            token_to_id = json.load(f)
        
        # Create instance with matched vocab size
        instance = cls(vocab_size=len(token_to_id))
        instance.token_to_id = token_to_id
        instance.id_to_token = {v: k for k, v in token_to_id.items()}
        instance._actual_vocab_size = len(token_to_id)
        
        # Load chat template if exists
        template_path = os.path.join(load_directory, "chat_template.jinja")
        if os.path.exists(template_path):
            with open(template_path, "r", encoding="utf-8") as f:
                instance.chat_template = f.read()
        
        return instance
