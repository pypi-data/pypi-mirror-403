"""
OMNIMIND Data Preparation Utilities
Tools for loading, chunking, and preparing raw text for training.
"""

import re
import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Generator
from dataclasses import dataclass

__all__ = [
    "RawTextDataLoader",
    "TextPreprocessor",
    "create_training_dataset",
]

SUPPORTED_FORMATS = {
    ".txt": "plain_text",
    ".md": "markdown",
    ".json": "json_lines",
    ".jsonl": "json_lines",
    ".csv": "csv_text_column",
}

@dataclass
class TextChunk:
    """A chunk of text with metadata"""
    text: str
    source: str
    chunk_id: int
    start_pos: int
    end_pos: int

class RawTextDataLoader:
    """
    Load and chunk raw text files for language model training.
    
    Supports multiple formats: .txt, .md, .json, .jsonl, .csv
    
    Usage:
        loader = RawTextDataLoader(tokenizer, chunk_size=2048)
        dataset = loader.load_from_file("book.txt")
    """
    
    def __init__(
        self,
        tokenizer = None,
        chunk_size: int = 2048,
        stride: int = 512,
        return_tokenized: bool = True,
    ):
        if chunk_size <= 0:
            raise ValueError(f"chunk_size must be positive, got {chunk_size}")
        if stride <= 0 or stride > chunk_size:
            raise ValueError(f"stride must be in (0, {chunk_size}], got {stride}")
        
        self.tokenizer = tokenizer
        self.chunk_size = chunk_size
        self.stride = stride
        self.return_tokenized = return_tokenized
    
    def detect_format(self, file_path: str) -> str:
        """Auto-detect file format"""
        suffix = Path(file_path).suffix.lower()
        return SUPPORTED_FORMATS.get(suffix, "plain_text")
    
    def load_from_file(self, file_path: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Load and chunk a single file.
        
        Returns list of chunks with input_ids and labels.
        """
        file_format = self.detect_format(file_path)
        text = self._read_file(file_path, file_format)
        
        print(f"📄 Loaded {file_path}: {len(text)} characters")
        
        chunks = self.smart_chunk_text(text, source=file_path)
        return self.create_dataset(chunks)
    
    def load_from_files(self, file_paths: List[str], **kwargs) -> List[Dict[str, Any]]:
        """Load and chunk multiple files"""
        all_chunks = []
        
        for path in file_paths:
            chunks = self.load_from_file(path, **kwargs)
            all_chunks.extend(chunks)
        
        print(f"📚 Total: {len(all_chunks)} chunks from {len(file_paths)} files")
        return all_chunks
    
    def load_from_directory(
        self, 
        directory: str, 
        extensions: List[str] = None,
        recursive: bool = True,
    ) -> List[Dict[str, Any]]:
        """Load all text files from a directory"""
        extensions = extensions or list(SUPPORTED_FORMATS.keys())
        directory = Path(directory)
        
        if recursive:
            files = [f for ext in extensions for f in directory.rglob(f"*{ext}")]
        else:
            files = [f for ext in extensions for f in directory.glob(f"*{ext}")]
        
        return self.load_from_files([str(f) for f in files])
    
    def smart_chunk_text(
        self, 
        text: str, 
        source: str = "unknown",
    ) -> List[TextChunk]:
        """
        Intelligent chunking that respects sentence boundaries.
        
        Uses stride for overlap to maintain context.
        """
        # Clean text
        text = text.strip()
        if not text:
            return []
        
        chunks = []
        
        if self.tokenizer:
            # Token-based chunking (more accurate)
            tokens = self.tokenizer.encode(text, add_special_tokens=False)
            
            chunk_id = 0
            start = 0
            
            while start < len(tokens):
                end = min(start + self.chunk_size, len(tokens))
                chunk_tokens = tokens[start:end]
                
                # Decode back to text for metadata
                chunk_text = self.tokenizer.decode(chunk_tokens)
                
                chunks.append(TextChunk(
                    text=chunk_text,
                    source=source,
                    chunk_id=chunk_id,
                    start_pos=start,
                    end_pos=end,
                ))
                
                chunk_id += 1
                start += self.chunk_size - self.stride
        else:
            # Character-based chunking (fallback)
            chunk_id = 0
            start = 0
            char_chunk_size = self.chunk_size * 4  # Rough estimate
            char_stride = self.stride * 4
            
            while start < len(text):
                end = min(start + char_chunk_size, len(text))
                
                # Try to break at sentence boundary
                if end < len(text):
                    last_period = text.rfind('.', start, end)
                    if last_period > start + char_chunk_size // 2:
                        end = last_period + 1
                
                chunks.append(TextChunk(
                    text=text[start:end],
                    source=source,
                    chunk_id=chunk_id,
                    start_pos=start,
                    end_pos=end,
                ))
                
                chunk_id += 1
                start += char_chunk_size - char_stride
        
        return chunks
    
    def create_dataset(self, chunks: List[TextChunk]) -> List[Dict[str, Any]]:
        """Convert chunks to training dataset format"""
        dataset = []
        
        for chunk in chunks:
            if self.tokenizer and self.return_tokenized:
                tokens = self.tokenizer.encode(
                    chunk.text, 
                    add_special_tokens=True,
                    truncation=True,
                    max_length=self.chunk_size,
                )
                dataset.append({
                    "input_ids": tokens,
                    "labels": tokens.copy(),
                    "attention_mask": [1] * len(tokens),
                })
            else:
                dataset.append({
                    "text": chunk.text,
                    "source": chunk.source,
                    "chunk_id": chunk.chunk_id,
                })
        
        return dataset
    
    def _read_file(self, file_path: str, file_format: str) -> str:
        """Read file content based on format"""
        path = Path(file_path)
        
        if file_format == "plain_text" or file_format == "markdown":
            return path.read_text(encoding="utf-8", errors="ignore")
        
        elif file_format == "json_lines":
            texts = []
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            text = self._extract_text_from_json(data)
                            if text:
                                texts.append(text)
                        except json.JSONDecodeError:
                            continue
            return "\n\n".join(texts)
        
        elif file_format == "csv_text_column":
            texts = []
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    text = self._extract_text_from_row(row)
                    if text:
                        texts.append(text)
            return "\n\n".join(texts)
        
        return path.read_text(encoding="utf-8", errors="ignore")
    
    def _extract_text_from_json(self, data: Dict) -> Optional[str]:
        """Extract text from JSON using common field names"""
        for key in ["text", "content", "body", "message", "document"]:
            if key in data:
                return str(data[key])
        return None
    
    def _extract_text_from_row(self, row: Dict) -> Optional[str]:
        """Extract text from CSV row using common column names"""
        for key in ["text", "content", "body", "message", "document"]:
            if key in row and row[key]:
                return str(row[key])
        return None


class TextPreprocessor:
    """
    Text preprocessing utilities for training data.
    """
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text"""
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove control characters
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        # Normalize quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        return text.strip()
    
    @staticmethod
    def remove_duplicates(texts: List[str], threshold: float = 0.9) -> List[str]:
        """Remove near-duplicate texts"""
        unique = []
        seen_hashes = set()
        
        for text in texts:
            # Simple hash-based dedup
            text_hash = hash(text[:500]) if len(text) > 500 else hash(text)
            if text_hash not in seen_hashes:
                unique.append(text)
                seen_hashes.add(text_hash)
        
        return unique
    
    @staticmethod
    def filter_by_length(
        texts: List[str], 
        min_length: int = 50, 
        max_length: int = 100000,
    ) -> List[str]:
        """Filter texts by character length"""
        return [t for t in texts if min_length <= len(t) <= max_length]
    
    @staticmethod
    def extract_code_blocks(text: str) -> List[str]:
        """Extract code blocks from markdown"""
        pattern = r'```[\w]*\n(.*?)```'
        return re.findall(pattern, text, re.DOTALL)
    
    @staticmethod
    def add_structure_tokens(text: str) -> str:
        """Add special tokens for document structure"""
        # Mark chapters
        text = re.sub(
            r'^(Chapter \d+[:\.]?\s*.*)$',
            r'<chapter>\1</chapter>',
            text,
            flags=re.MULTILINE | re.IGNORECASE
        )
        
        # Mark sections
        text = re.sub(
            r'^(#{1,6}\s+.*)$',
            r'<section>\1</section>',
            text,
            flags=re.MULTILINE
        )
        
        return text


def create_training_dataset(
    sources: Union[str, List[str]],
    tokenizer,
    chunk_size: int = 2048,
    stride: int = 512,
    preprocess: bool = True,
) -> List[Dict[str, Any]]:
    """
    Convenience function to create a training dataset from text sources.
    
    Args:
        sources: File path, directory, or list of paths
        tokenizer: Tokenizer for encoding
        chunk_size: Maximum chunk size in tokens
        stride: Overlap between chunks
        preprocess: Apply text preprocessing
        
    Returns:
        List of training examples with input_ids and labels
    """
    loader = RawTextDataLoader(
        tokenizer=tokenizer,
        chunk_size=chunk_size,
        stride=stride,
    )
    
    if isinstance(sources, str):
        path = Path(sources)
        if path.is_dir():
            return loader.load_from_directory(sources)
        else:
            return loader.load_from_file(sources)
    else:
        return loader.load_from_files(sources)
