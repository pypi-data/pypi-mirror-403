"""
OMNIMIND Evaluator
Automated evaluation metrics for language models

Metrics:
- Perplexity (PPL): Fluency
- Accuracy: For MCQA
- BLEU/ROUGE: For translation/summarization
- Generation Speed: Tokens/sec
"""
import time
import math
import torch
import torch.nn as nn
from typing import List, Dict, Any, Union, Optional
from tqdm import tqdm


class Evaluator:
    """Model evaluator"""
    
    def __init__(self, model: nn.Module, tokenizer, device: str = None):
        self.model = model
        self.tokenizer = tokenizer
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model.eval()
    
    def compute_perplexity(self, text_list: List[str], stride: int = 512) -> float:
        """Compute perplexity on a list of texts"""
        nlls = []
        total_len = 0
        
        print(f"📊 Computing Perplexity on {len(text_list)} texts...")
        
        for text in tqdm(text_list):
            encodings = self.tokenizer.encode(text)
            input_ids = torch.tensor(encodings).unsqueeze(0).to(self.device)
            
            target_ids = input_ids.clone()
            
            with torch.no_grad():
                outputs = self.model(input_ids)
                logits = outputs.logits if hasattr(outputs, 'logits') else outputs
                
                # Shift for causal LM
                shift_logits = logits[..., :-1, :].contiguous()
                shift_labels = target_ids[..., 1:].contiguous()
                
                loss_fct = nn.CrossEntropyLoss(reduction="sum")
                loss = loss_fct(
                    shift_logits.view(-1, shift_logits.size(-1)),
                    shift_labels.view(-1)
                )
                
                nlls.append(loss)
                total_len += shift_labels.size(1)
        
        if total_len == 0:
            return 0.0
            
        ppl = math.exp(torch.stack(nlls).sum() / total_len)
        return ppl

    def evaluate_generation(
        self, 
        prompts: List[str], 
        references: Optional[List[str]] = None,
        max_new_tokens: int = 100
    ) -> Dict[str, float]:
        """Evaluate generation quality and speed"""
        
        start_time = time.time()
        total_tokens = 0
        generated_texts = []
        
        print(f"📊 Evaluating generation on {len(prompts)} prompts...")
        
        for prompt in tqdm(prompts):
            input_ids = self.tokenizer.encode(prompt)
            input_tensor = torch.tensor([input_ids]).to(self.device)
            
            # Count prompt tokens
            prompt_len = len(input_ids)
            
            with torch.no_grad():
                output = self.model.generate(
                    input_tensor, 
                    max_new_tokens=max_new_tokens
                )
                
            # Count generated tokens
            gen_len = output.shape[1] - prompt_len
            total_tokens += gen_len
            
            decoded = self.tokenizer.decode(output[0].tolist())
            generated_texts.append(decoded)
            
        elapsed = time.time() - start_time
        speed = total_tokens / elapsed
        
        results = {
            "tokens_per_sec": speed,
            "latency_per_req": elapsed / len(prompts),
            "total_tokens": total_tokens
        }
        
        # If references provided (simple partial match)
        if references:
            matches = 0
            for gen, ref in zip(generated_texts, references):
                if ref.lower() in gen.lower():
                    matches += 1
            results["exact_match_ratio"] = matches / len(references)
            
        return results


def evaluate_model(
    model: nn.Module, 
    tokenizer, 
    dataset: List[str], 
    metric: str = "perplexity"
) -> float:
    """Quick evaluation helper"""
    evaluator = Evaluator(model, tokenizer)
    
    if metric == "perplexity":
        return evaluator.compute_perplexity(dataset)
    else:
        raise ValueError(f"Unknown metric: {metric}")
