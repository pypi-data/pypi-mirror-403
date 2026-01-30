"""
OMNIMIND Sequence Packing Utilities
Pack multiple sequences into single examples for efficient training.
"""

import torch
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

__all__ = [
    "pack_sequences",
    "create_packing_collator",
    "PackedDataset",
]

@dataclass
class PackedExample:
    """A packed example containing multiple sequences"""
    input_ids: torch.Tensor
    attention_mask: torch.Tensor
    labels: torch.Tensor
    position_ids: torch.Tensor
    sequence_lengths: List[int]

def pack_sequences(
    examples: List[Dict[str, List[int]]],
    max_length: int,
    pad_token_id: int = 0,
    label_pad_id: int = -100,
) -> List[Dict[str, Any]]:
    """
    Pack multiple sequences into single examples.
    
    This improves training efficiency by reducing padding waste.
    Each packed example contains multiple original sequences separated
    by appropriate attention masking.
    
    Args:
        examples: List of examples with 'input_ids' and optionally 'labels'
        max_length: Maximum sequence length
        pad_token_id: Token ID for padding
        label_pad_id: Label ID for ignored positions
        
    Returns:
        List of packed examples
    """
    packed = []
    current_input_ids = []
    current_labels = []
    current_positions = []
    current_lengths = []
    current_pos = 0
    
    for example in examples:
        input_ids = example["input_ids"]
        labels = example.get("labels", input_ids.copy())
        seq_len = len(input_ids)
        
        # Check if we can add this sequence
        if len(current_input_ids) + seq_len > max_length:
            # Save current packed example
            if current_input_ids:
                packed.append(_finalize_packed(
                    current_input_ids, current_labels, current_positions,
                    current_lengths, max_length, pad_token_id, label_pad_id
                ))
            
            # Start new packed example
            current_input_ids = []
            current_labels = []
            current_positions = []
            current_lengths = []
            current_pos = 0
        
        # Add sequence
        current_input_ids.extend(input_ids)
        current_labels.extend(labels)
        current_positions.extend(range(seq_len))  # Reset positions per sequence
        current_lengths.append(seq_len)
        current_pos += seq_len
    
    # Don't forget the last packed example
    if current_input_ids:
        packed.append(_finalize_packed(
            current_input_ids, current_labels, current_positions,
            current_lengths, max_length, pad_token_id, label_pad_id
        ))
    
    return packed

def _finalize_packed(
    input_ids: List[int],
    labels: List[int],
    positions: List[int],
    lengths: List[int],
    max_length: int,
    pad_token_id: int,
    label_pad_id: int,
) -> Dict[str, Any]:
    """Finalize a packed example with padding"""
    current_len = len(input_ids)
    pad_len = max_length - current_len
    
    # Pad sequences
    input_ids = input_ids + [pad_token_id] * pad_len
    labels = labels + [label_pad_id] * pad_len
    positions = positions + [0] * pad_len
    
    # Create attention mask (1 for real tokens, 0 for padding)
    attention_mask = [1] * current_len + [0] * pad_len
    
    return {
        "input_ids": input_ids,
        "attention_mask": attention_mask,
        "labels": labels,
        "position_ids": positions,
        "sequence_lengths": lengths,
    }

def create_packing_collator(
    max_length: int,
    pad_token_id: int = 0,
    label_pad_id: int = -100,
):
    """
    Create a collator function for DataLoader that packs sequences.
    
    Usage:
        collator = create_packing_collator(max_length=4096, pad_token_id=tokenizer.pad_token_id)
        dataloader = DataLoader(dataset, collate_fn=collator)
    """
    def collator(examples: List[Dict[str, Any]]) -> Dict[str, torch.Tensor]:
        packed = pack_sequences(examples, max_length, pad_token_id, label_pad_id)
        
        # Convert to tensors
        batch = {
            "input_ids": torch.tensor([p["input_ids"] for p in packed]),
            "attention_mask": torch.tensor([p["attention_mask"] for p in packed]),
            "labels": torch.tensor([p["labels"] for p in packed]),
            "position_ids": torch.tensor([p["position_ids"] for p in packed]),
        }
        
        return batch
    
    return collator

class PackedDataset:
    """
    Dataset wrapper that pre-packs sequences for efficient training.
    
    Usage:
        packed = PackedDataset(original_dataset, max_length=4096, tokenizer=tokenizer)
        for batch in DataLoader(packed, batch_size=1):
            ...
    """
    
    def __init__(
        self,
        dataset,
        max_length: int,
        tokenizer = None,
        input_column: str = "input_ids",
        label_column: str = "labels",
    ):
        self.max_length = max_length
        self.pad_token_id = tokenizer.pad_token_id if tokenizer else 0
        
        # Pre-pack all sequences
        examples = []
        for item in dataset:
            examples.append({
                "input_ids": item[input_column] if isinstance(item, dict) else item,
                "labels": item.get(label_column, item[input_column]) if isinstance(item, dict) else item,
            })
        
        self.packed = pack_sequences(
            examples, max_length, self.pad_token_id
        )
        
        print(f"📦 Packed {len(examples)} sequences into {len(self.packed)} examples")
        print(f"   Efficiency: {len(examples)/len(self.packed):.1f}x")
    
    def __len__(self):
        return len(self.packed)
    
    def __getitem__(self, idx):
        item = self.packed[idx]
        return {
            "input_ids": torch.tensor(item["input_ids"]),
            "attention_mask": torch.tensor(item["attention_mask"]),
            "labels": torch.tensor(item["labels"]),
            "position_ids": torch.tensor(item["position_ids"]),
        }
