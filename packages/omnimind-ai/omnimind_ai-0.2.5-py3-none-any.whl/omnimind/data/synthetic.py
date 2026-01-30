"""
OMNIMIND Synthetic Data Generation
Generate training data using LLMs (QA pairs, instructions, etc.)
"""

import json
import time
import random
from pathlib import Path
from typing import List, Dict, Any, Optional, Generator
from dataclasses import dataclass

__all__ = [
    "SyntheticDataGenerator",
    "QAPairGenerator",
    "InstructionGenerator",
    "generate_qa_pairs",
]

# Default system prompts for different generation tasks
SYNTHETIC_PROMPTS = {
    "qa_generation": """You are a helpful assistant that generates high-quality question-answer pairs from the given text.
Generate diverse questions that test understanding of the content.
Output JSON format: {"question": "...", "answer": "..."}""",
    
    "instruction_generation": """You are a helpful assistant that creates instruction-following examples.
Given a topic or context, generate a clear instruction and a helpful response.
Output JSON format: {"instruction": "...", "response": "..."}""",
    
    "summarization": """You are a helpful assistant that creates summarization examples.
Given a text, generate a concise summary.
Output JSON format: {"text": "...", "summary": "..."}""",
}

@dataclass
class SyntheticConfig:
    """Configuration for synthetic data generation"""
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.95
    num_samples: int = 10
    batch_size: int = 4
    output_format: str = "jsonl"

class SyntheticDataGenerator:
    """
    Generate synthetic training data using an LLM.
    
    Can use local models (via Omnimind) or API-based models.
    
    Usage:
        generator = SyntheticDataGenerator(model, tokenizer)
        qa_pairs = generator.generate_qa(source_texts, num_pairs=100)
    """
    
    def __init__(
        self,
        model = None,
        tokenizer = None,
        config: Optional[SyntheticConfig] = None,
        use_api: bool = False,
        api_key: Optional[str] = None,
    ):
        self.model = model
        self.tokenizer = tokenizer
        self.config = config or SyntheticConfig()
        self.use_api = use_api
        self.api_key = api_key
    
    def generate(
        self,
        prompts: List[str],
        system_prompt: str = "",
        **kwargs,
    ) -> List[str]:
        """Generate responses for a list of prompts"""
        responses = []
        
        for prompt in prompts:
            response = self._generate_single(prompt, system_prompt, **kwargs)
            responses.append(response)
        
        return responses
    
    def _generate_single(
        self,
        prompt: str,
        system_prompt: str = "",
        max_tokens: int = None,
        temperature: float = None,
    ) -> str:
        """Generate a single response"""
        max_tokens = max_tokens or self.config.max_tokens
        temperature = temperature or self.config.temperature
        
        if self.use_api:
            return self._generate_api(prompt, system_prompt, max_tokens, temperature)
        else:
            return self._generate_local(prompt, system_prompt, max_tokens, temperature)
    
    def _generate_local(
        self,
        prompt: str,
        system_prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> str:
        """Generate using local model"""
        if self.model is None or self.tokenizer is None:
            raise ValueError("Model and tokenizer required for local generation")
        
        # Format prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        else:
            full_prompt = prompt
        
        # Encode
        inputs = self.tokenizer(
            full_prompt,
            return_tensors="pt",
            truncation=True,
            max_length=2048,
        )
        
        if hasattr(self.model, "device"):
            inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
        
        # Generate
        import torch
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=temperature > 0,
                pad_token_id=self.tokenizer.pad_token_id,
            )
        
        # Decode
        response = self.tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1]:],
            skip_special_tokens=True,
        )
        
        return response.strip()
    
    def _generate_api(
        self,
        prompt: str,
        system_prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> str:
        """Generate using API (OpenAI compatible)"""
        try:
            import openai
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            client = openai.OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            
            return response.choices[0].message.content.strip()
            
        except ImportError:
            raise ImportError("openai package required for API generation")


class QAPairGenerator:
    """
    Generate Question-Answer pairs from source texts.
    
    Great for creating training data for instruction-following models.
    """
    
    def __init__(self, generator: SyntheticDataGenerator):
        self.generator = generator
    
    def generate_from_text(
        self,
        text: str,
        num_pairs: int = 5,
        difficulty: str = "medium",
    ) -> List[Dict[str, str]]:
        """Generate QA pairs from a text passage"""
        prompt = f"""Based on the following text, generate {num_pairs} question-answer pairs.
Make the questions {difficulty} difficulty level.
Format each pair as JSON on a new line.

Text:
{text[:2000]}

Generate {num_pairs} QA pairs:"""
        
        response = self.generator._generate_single(
            prompt,
            system_prompt=SYNTHETIC_PROMPTS["qa_generation"],
        )
        
        return self._parse_qa_response(response)
    
    def generate_from_file(
        self,
        file_path: str,
        num_pairs_per_chunk: int = 5,
        chunk_size: int = 1000,
    ) -> List[Dict[str, str]]:
        """Generate QA pairs from a file"""
        text = Path(file_path).read_text(encoding="utf-8")
        
        # Chunk the text
        chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
        
        all_pairs = []
        for i, chunk in enumerate(chunks):
            print(f"📝 Generating QA from chunk {i+1}/{len(chunks)}")
            pairs = self.generate_from_text(chunk, num_pairs_per_chunk)
            all_pairs.extend(pairs)
            time.sleep(0.5)  # Rate limiting
        
        return all_pairs
    
    def _parse_qa_response(self, response: str) -> List[Dict[str, str]]:
        """Parse QA pairs from model response"""
        pairs = []
        
        for line in response.split("\n"):
            line = line.strip()
            if line.startswith("{") and line.endswith("}"):
                try:
                    pair = json.loads(line)
                    if "question" in pair and "answer" in pair:
                        pairs.append(pair)
                except json.JSONDecodeError:
                    continue
        
        return pairs
    
    def save_to_file(
        self,
        pairs: List[Dict[str, str]],
        output_path: str,
        format: str = "jsonl",
    ):
        """Save QA pairs to file"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == "jsonl":
            with open(output_path, "w", encoding="utf-8") as f:
                for pair in pairs:
                    f.write(json.dumps(pair, ensure_ascii=False) + "\n")
        elif format == "json":
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(pairs, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Saved {len(pairs)} QA pairs to {output_path}")


class InstructionGenerator:
    """Generate instruction-response pairs for training"""
    
    def __init__(self, generator: SyntheticDataGenerator):
        self.generator = generator
    
    def generate_instructions(
        self,
        topics: List[str],
        num_per_topic: int = 5,
    ) -> List[Dict[str, str]]:
        """Generate instruction-response pairs for given topics"""
        all_instructions = []
        
        for topic in topics:
            prompt = f"""Generate {num_per_topic} diverse instruction-response pairs about: {topic}
Each pair should have a clear instruction and a helpful, detailed response.
Format each as JSON on a new line: {{"instruction": "...", "response": "..."}}"""
            
            response = self.generator._generate_single(
                prompt,
                system_prompt=SYNTHETIC_PROMPTS["instruction_generation"],
            )
            
            instructions = self._parse_instructions(response)
            all_instructions.extend(instructions)
        
        return all_instructions
    
    def _parse_instructions(self, response: str) -> List[Dict[str, str]]:
        """Parse instruction pairs from response"""
        pairs = []
        
        for line in response.split("\n"):
            line = line.strip()
            if line.startswith("{"):
                try:
                    pair = json.loads(line)
                    if "instruction" in pair and "response" in pair:
                        pairs.append(pair)
                except json.JSONDecodeError:
                    continue
        
        return pairs


def generate_qa_pairs(
    source: str,
    output_path: str,
    model = None,
    tokenizer = None,
    num_pairs: int = 100,
    **kwargs,
) -> str:
    """
    Convenience function to generate QA pairs from a source.
    
    Args:
        source: File path or text content
        output_path: Where to save the generated pairs
        model: Model for generation
        tokenizer: Tokenizer
        num_pairs: Target number of QA pairs
        
    Returns:
        Path to saved file
    """
    generator = SyntheticDataGenerator(model, tokenizer)
    qa_gen = QAPairGenerator(generator)
    
    if Path(source).exists():
        pairs = qa_gen.generate_from_file(source, num_pairs_per_chunk=10)
    else:
        pairs = qa_gen.generate_from_text(source, num_pairs=num_pairs)
    
    qa_gen.save_to_file(pairs, output_path)
    return output_path
