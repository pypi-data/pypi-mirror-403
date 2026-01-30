"""
OMNIMIND Core Layer - State Processor
Layer 1: ประมวลผลหลักด้วย State-Space concept
"""
from typing import Optional, List, Generator, Dict, Any
from dataclasses import dataclass
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, TextIteratorStreamer
from threading import Thread
import sys
import os

# Import from root config (AppConfig) - for application-level configuration
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import AppConfig, ModelConfig


@dataclass
class ProcessorState:
    """Internal state of the processor (fixed size regardless of input length)"""
    hidden_state: Optional[torch.Tensor] = None
    attention_cache: Optional[tuple] = None
    token_count: int = 0
    
    def reset(self):
        """Reset state"""
        self.hidden_state = None
        self.attention_cache = None
        self.token_count = 0


class StateProcessor:
    """
    State Processor - Core processing unit
    
    แนวคิด State-Space:
    - ประมวลผลแบบ O(n) ไม่ใช่ O(n²)
    - State มีขนาดคงที่ ไม่ว่า input จะยาวแค่ไหน
    - สามารถ stream ได้ ไม่ต้องรอ input ทั้งหมด
    """
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.model_config = config.get_model_config()
        self.state = ProcessorState()
        
        # Device selection
        if config.device == "auto":
            if torch.cuda.is_available():
                self.device = "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                self.device = "mps"
            else:
                self.device = "cpu"
        else:
            self.device = config.device
        
        self._model = None
        self._tokenizer = None
        self._loaded = False
    
    def load(self):
        """Load model and tokenizer"""
        if self._loaded:
            return
        
        print(f"🔄 Loading model: {self.model_config.hf_model}")
        print(f"   Device: {self.device}")
        
        self._tokenizer = AutoTokenizer.from_pretrained(
            self.model_config.hf_model,
            trust_remote_code=True
        )
        
        # Set pad token if not set
        if self._tokenizer.pad_token is None:
            self._tokenizer.pad_token = self._tokenizer.eos_token
        
        # Load model with appropriate settings
        load_kwargs = {
            "trust_remote_code": True,
            "low_cpu_mem_usage": True,
        }
        
        if self.device == "cuda":
            load_kwargs["torch_dtype"] = torch.float16
            load_kwargs["device_map"] = "auto"
        elif self.device == "mps":
            load_kwargs["torch_dtype"] = torch.float16
        
        self._model = AutoModelForCausalLM.from_pretrained(
            self.model_config.hf_model,
            **load_kwargs
        )
        
        if self.device == "mps":
            self._model = self._model.to(self.device)
        elif self.device == "cpu":
            self._model = self._model.to(self.device)
        
        self._model.eval()
        self._loaded = True
        print(f"✅ Model loaded successfully!")
    
    @property
    def tokenizer(self):
        if not self._loaded:
            self.load()
        return self._tokenizer
    
    @property
    def model(self):
        if not self._loaded:
            self.load()
        return self._model
    
    def encode(self, text: str) -> torch.Tensor:
        """Encode text to tokens"""
        return self.tokenizer.encode(text, return_tensors="pt").to(self.device)
    
    def decode(self, tokens: torch.Tensor) -> str:
        """Decode tokens to text"""
        return self.tokenizer.decode(tokens[0], skip_special_tokens=True)
    
    def process(
        self,
        input_text: str,
        max_new_tokens: int = 256,
        temperature: float = 0.7,
        top_p: float = 0.9,
        repetition_penalty: float = 1.1,
    ) -> str:
        """
        Process input and generate response
        
        Args:
            input_text: Input text to process
            max_new_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (0 = deterministic)
            top_p: Nucleus sampling threshold
            repetition_penalty: Penalty for repetition
            
        Returns:
            Generated response text
        """
        input_ids = self.encode(input_text)
        self.state.token_count += input_ids.shape[1]
        
        with torch.no_grad():
            outputs = self.model.generate(
                input_ids,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                repetition_penalty=repetition_penalty,
                do_sample=temperature > 0,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )
        
        # Extract only the generated part
        generated_ids = outputs[0, input_ids.shape[1]:]
        response = self.tokenizer.decode(generated_ids, skip_special_tokens=True)
        
        return response.strip()
    
    def process_stream(
        self,
        input_text: str,
        max_new_tokens: int = 256,
        temperature: float = 0.7,
        top_p: float = 0.9,
        repetition_penalty: float = 1.1,
    ) -> Generator[str, None, None]:
        """
        Process input and stream response tokens
        
        Args:
            input_text: Input text to process
            max_new_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling threshold
            repetition_penalty: Penalty for repetition
            
        Yields:
            Generated tokens one by one
        """
        input_ids = self.encode(input_text)
        self.state.token_count += input_ids.shape[1]
        
        # Setup streamer
        streamer = TextIteratorStreamer(
            self.tokenizer,
            skip_prompt=True,
            skip_special_tokens=True
        )
        
        # Generation kwargs
        gen_kwargs = {
            "input_ids": input_ids,
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "repetition_penalty": repetition_penalty,
            "do_sample": temperature > 0,
            "pad_token_id": self.tokenizer.pad_token_id,
            "eos_token_id": self.tokenizer.eos_token_id,
            "streamer": streamer,
        }
        
        # Run generation in thread
        thread = Thread(target=self.model.generate, kwargs=gen_kwargs)
        thread.start()
        
        # Yield tokens as they come
        for token in streamer:
            yield token
        
        thread.join()
    
    def get_state_info(self) -> Dict[str, Any]:
        """Get current processor state info"""
        return {
            "device": self.device,
            "model": self.model_config.name,
            "loaded": self._loaded,
            "tokens_processed": self.state.token_count,
            "state_size": self.model_config.state_size,
        }
    
    def reset_state(self):
        """Reset processor state"""
        self.state.reset()
