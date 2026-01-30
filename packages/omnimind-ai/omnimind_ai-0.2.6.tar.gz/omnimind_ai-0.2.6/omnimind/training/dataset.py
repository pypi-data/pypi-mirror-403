"""
OMNIMIND Training Dataset
Data loading, tokenization, and preprocessing

Supports:
- SimpleTokenizer (Prototype)
- HuggingFace AutoTokenizer (Production)
"""
import os
import json
from typing import List, Dict, Any, Optional, Iterator, Union
from dataclasses import dataclass
import torch
from torch.utils.data import Dataset, DataLoader, IterableDataset
from transformers import PreTrainedTokenizer
from jinja2 import Template

# Import OMNIMIND template
try:
    from omnimind.utils.chat_template import OMNIMIND_CHAT_TEMPLATE
except ImportError:
    # Fallback if relative import fails
    OMNIMIND_CHAT_TEMPLATE = "" 

@dataclass
class DataConfig:
    """Dataset configuration"""
    max_seq_len: int = 2048
    vocab_size: int = 32000
    pad_token_id: int = 0
    bos_token_id: int = 1
    eos_token_id: int = 2


class SimpleTokenizer:
    """
    Simple character/word tokenizer for prototyping
    
    Real implementation should use SentencePiece or similar
    """
    
    def __init__(self, vocab_size: int = 32000):
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
        }
        
        # Build vocabulary
        self.token_to_id: Dict[str, int] = dict(self.special_tokens)
        self.id_to_token: Dict[int, str] = {v: k for k, v in self.special_tokens.items()}
        
        # Add Thai consonants, vowels, numbers, etc.
        thai_chars = "กขฃคฅฆงจฉชซฌญฎฏฐฑฒณดตถทธนบปผฝพฟภมยรลวศษสหฬอฮ"
        thai_vowels = "ะาิีึืุูเแโใไๅำ็่้๊๋์ํ"
        
        idx = len(self.special_tokens)
        for char in thai_chars + thai_vowels:
            if idx < vocab_size:
                self.token_to_id[char] = idx
                self.id_to_token[idx] = char
                idx += 1
        
        # Add ASCII
        for i in range(32, 127):
            char = chr(i)
            if idx < vocab_size and char not in self.token_to_id:
                self.token_to_id[char] = idx
                self.id_to_token[idx] = char
                idx += 1
    
    def encode(self, text: str, add_special_tokens: bool = True) -> List[int]:
        """Encode text to token IDs"""
        ids = []
        
        if add_special_tokens:
            ids.append(self.bos_token_id)
        
        # Simple character-level encoding for prototype
        # Handle special tokens roughly (not perfect in simple tokenizer)
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
        """
        Apply OMNIMIND chat template
        """
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
        return len(self.token_to_id)

    def save_pretrained(self, save_directory: str):
        """
        Save tokenizer configuration and vocabulary.
        
        Saves:
        - tokenizer_config.json
        - special_tokens_map.json
        - vocab.json
        - chat_template.jinja
        - added_tokens.json
        """
        import os
        import json
        
        os.makedirs(save_directory, exist_ok=True)
        
        # 1. vocab.json
        vocab_path = os.path.join(save_directory, "vocab.json")
        with open(vocab_path, "w", encoding="utf-8") as f:
            json.dump(self.token_to_id, f, indent=2, ensure_ascii=False)
            
        # 2. tokenizer_config.json
        config = {
            "do_lower_case": False,
            "unk_token": "<unk>",
            "pad_token": "<pad>",
            "bos_token": "<bos>",
            "eos_token": "<eos>",
            "chat_template": self.chat_template,
            "model_max_length": 2048
        }
        with open(os.path.join(save_directory, "tokenizer_config.json"), "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
            
        # 3. special_tokens_map.json
        special_tokens_map = {
            "unk_token": "<unk>",
            "pad_token": "<pad>",
            "bos_token": "<bos>",
            "eos_token": "<eos>",
            "additional_special_tokens": ["<|im_start|>", "<|im_end|>", "<think>", "</think>"]
        }
        with open(os.path.join(save_directory, "special_tokens_map.json"), "w", encoding="utf-8") as f:
            json.dump(special_tokens_map, f, indent=2)
            
        # 4. separate chat_template file (optional but good practice)
        with open(os.path.join(save_directory, "chat_template.jinja"), "w", encoding="utf-8") as f:
            f.write(self.chat_template)

        # 5. Model files (dummy for compatibility)
        # merges.txt (not used for this simple tokenizer but file expected)
        with open(os.path.join(save_directory, "merges.txt"), "w", encoding="utf-8") as f:
            f.write("# Dummy merges file for SimpleTokenizer\n")

        # 6. tokenizer.json (Simulate HuggingFace Tokenizer JSON structure)
        tokenizer_json = {
            "version": "1.0",
            "model": {
                "type": "Unigram", # Pretend to be unigram or BPE
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
            
        print(f"✅ Tokenizer saved to {save_directory}")


class TextDataset(Dataset):
    """
    Simple text dataset for training
    
    Loads text files and creates fixed-length sequences
    """
    
    def __init__(
        self,
        data_path: str,
        tokenizer: Union[SimpleTokenizer, PreTrainedTokenizer],
        max_seq_len: int = 2048,
    ):
        self.tokenizer = tokenizer
        self.max_seq_len = max_seq_len
        
        # Load and tokenize data
        self.tokens = []
        
        if os.path.isfile(data_path):
            self._load_file(data_path)
        elif os.path.isdir(data_path):
            for filename in os.listdir(data_path):
                if filename.endswith(('.txt', '.json', '.jsonl')):
                    self._load_file(os.path.join(data_path, filename))
        
        # Create chunks
        self.chunks = self._create_chunks()
    
    def _load_file(self, path: str):
        """Load and tokenize a single file"""
        if path.endswith('.txt'):
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read()
                self._add_text(text)
        
        elif path.endswith('.json'):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        text = item.get('text', str(item))
                        self._add_text(text)
        
        elif path.endswith('.jsonl'):
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        item = json.loads(line)
                        text = item.get('text', str(item))
                        self._add_text(text)
                    except:
                        pass

    def _add_text(self, text: str):
        """Helper to tokenize and add text"""
        if hasattr(self.tokenizer, 'encode'):
             # Handle both SimpleTokenizer and HuggingFace Tokenizer
             if isinstance(self.tokenizer, SimpleTokenizer):
                 self.tokens.extend(self.tokenizer.encode(text, add_special_tokens=True))
             else:
                 # HuggingFace tokenizer
                 self.tokens.extend(self.tokenizer.encode(text, add_special_tokens=True))

    def _create_chunks(self) -> List[List[int]]:
        """Split tokens into fixed-length chunks"""
        chunks = []
        if len(self.tokens) <= 1:
            return []
            
        for i in range(0, len(self.tokens) - self.max_seq_len, self.max_seq_len):
            chunk = self.tokens[i:i + self.max_seq_len + 1]  # +1 for labels
            if len(chunk) < 2: 
                continue
            chunks.append(chunk)
        return chunks
    
    def __len__(self) -> int:
        return len(self.chunks)
    
    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        chunk = self.chunks[idx]
        
        # Input: all except last token
        input_ids = torch.tensor(chunk[:-1], dtype=torch.long)
        
        # Labels: all except first token (shifted)
        labels = torch.tensor(chunk[1:], dtype=torch.long)
        
        return {
            "input_ids": input_ids,
            "labels": labels,
        }


class StreamingDataset(IterableDataset):
    """
    Streaming dataset for large files
    
    Memory efficient - doesn't load entire file
    """
    
    def __init__(
        self,
        data_path: str,
        tokenizer: Union[SimpleTokenizer, PreTrainedTokenizer],
        max_seq_len: int = 2048,
    ):
        self.data_path = data_path
        self.tokenizer = tokenizer
        self.max_seq_len = max_seq_len
    
    def __iter__(self) -> Iterator[Dict[str, torch.Tensor]]:
        buffer = []
        
        if not os.path.exists(self.data_path):
            return
            
        with open(self.data_path, 'r', encoding='utf-8') as f:
            for line in f:
                # Tokenize line
                if isinstance(self.tokenizer, SimpleTokenizer):
                    tokens = self.tokenizer.encode(line.strip(), add_special_tokens=True)
                else:
                    tokens = self.tokenizer.encode(line.strip(), add_special_tokens=True)
                    
                buffer.extend(tokens)
                
                # Yield chunks when buffer is full
                while len(buffer) >= self.max_seq_len + 1:
                    chunk = buffer[:self.max_seq_len + 1]
                    buffer = buffer[self.max_seq_len:]
                    
                    input_ids = torch.tensor(chunk[:-1], dtype=torch.long)
                    labels = torch.tensor(chunk[1:], dtype=torch.long)
                    
                    yield {
                        "input_ids": input_ids,
                        "labels": labels,
                    }


def create_dataloader(
    dataset: Dataset,
    batch_size: int = 8,
    shuffle: bool = True,
    num_workers: int = 0,
) -> DataLoader:
    """Create DataLoader with collation"""
    
    def collate_fn(batch: List[Dict[str, torch.Tensor]]) -> Dict[str, torch.Tensor]:
        batch = [item for item in batch if item is not None and len(item['input_ids']) > 0]
        if not batch:
            return {}
            
        max_len = max(len(item["input_ids"]) for item in batch)
        
        padded_input_ids = []
        padded_labels = []
        
        for item in batch:
            input_ids = item["input_ids"]
            labels = item["labels"]
            
            pad_len = max_len - len(input_ids)
            if pad_len > 0:
                input_ids = torch.cat([input_ids, torch.zeros(pad_len, dtype=torch.long)])
                labels = torch.cat([labels, torch.zeros(pad_len, dtype=torch.long)])
                
            padded_input_ids.append(input_ids)
            padded_labels.append(labels)

        input_ids = torch.stack(padded_input_ids)
        labels = torch.stack(padded_labels)
        return {"input_ids": input_ids, "labels": labels}
    
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        collate_fn=collate_fn,
        pin_memory=True,
    )
