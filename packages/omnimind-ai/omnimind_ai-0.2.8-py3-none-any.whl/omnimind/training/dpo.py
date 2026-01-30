"""
OMNIMIND Direct Preference Optimization (DPO)
Alignment training to make models follow human preferences (RLHF alternative)

DPO simplifies RLHF by optimizing the policy directly based on preferences,
without training a separate reward model or using PPO.

Usage:
    dpo_trainer = DPOTrainer(model, ref_model, config)
    dpo_trainer.train(preference_dataset)
"""
import copy
import time
import torch
import torch.nn as nn
import torch.nn.functional as F
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

from .trainer import Trainer, TrainingConfig


@dataclass
class DPOConfig(TrainingConfig):
    """Configuration for DPO training"""
    beta: float = 0.1             # Temperature parameter for DPO loss
    loss_type: str = "sigmoid"    # sigmoid, hinge, or ipo
    label_smoothing: float = 0.0  # Label smoothing for DPO loss
    
    # Reference model
    ref_model_free: bool = False  # If True, keeps ref model in CPU memory


class DPOTrainer(Trainer):
    """
    Direct Preference Optimization Trainer
    
    Training data format:
    {
        "prompt": "Question...",
        "chosen": "Better answer...",
        "rejected": "Worse answer..."
    }
    """
    
    def __init__(
        self,
        model: nn.Module,
        ref_model: Optional[nn.Module] = None,
        config: DPOConfig = None,
        tokenizer = None
    ):
        config = config or DPOConfig()
        super().__init__(model, config)
        self.dpo_config = config
        self.tokenizer = tokenizer
        
        # Reference model (frozen)
        if ref_model:
            self.ref_model = ref_model
        else:
            # If not provided, copy the model as reference
            print("📝 Creating reference model from policy model...")
            self.ref_model = copy.deepcopy(model)
        
        # Freeze reference model
        for param in self.ref_model.parameters():
            param.requires_grad = False
        self.ref_model.eval()
        
        # Move to device
        if not self.dpo_config.ref_model_free:
            self.ref_model.to(self.device)
    
    def dpo_loss(
        self,
        policy_chosen_logps: torch.Tensor,
        policy_rejected_logps: torch.Tensor,
        ref_chosen_logps: torch.Tensor,
        ref_rejected_logps: torch.Tensor,
    ):
        """Compute DPO loss"""
        pi_logratios = policy_chosen_logps - policy_rejected_logps
        ref_logratios = ref_chosen_logps - ref_rejected_logps
        
        logits = pi_logratios - ref_logratios
        
        if self.dpo_config.loss_type == "sigmoid":
            losses = -F.logsigmoid(self.dpo_config.beta * logits)
        elif self.dpo_config.loss_type == "hinge":
            losses = torch.relu(1 - self.dpo_config.beta * logits)
        elif self.dpo_config.loss_type == "ipo":
            losses = (logits - 1 / (2 * self.dpo_config.beta)) ** 2
        else:
            raise ValueError(f"Unknown loss type: {self.dpo_config.loss_type}")
            
        chosen_rewards = self.dpo_config.beta * (policy_chosen_logps - ref_chosen_logps).detach()
        rejected_rewards = self.dpo_config.beta * (policy_rejected_logps - ref_rejected_logps).detach()
        
        return losses.mean(), chosen_rewards.mean(), rejected_rewards.mean()
    
    def _get_batch_logps(
        self,
        model,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        logits_to_keep: int
    ):
        """Compute log probabilities of labels"""
        logits = model(input_ids).logits if hasattr(model(input_ids), 'logits') else model(input_ids)
        logits = logits[:, :-1, :]
        input_ids = input_ids[:, 1:]
        
        # Only keep the completion part (ignore prompt)
        # This is simplified; assumes labels only contain indices for completion
        # For full implementation, we need rigorous masking of prompt tokens
        
        per_token_logps = torch.gather(
            logits.log_softmax(-1), dim=2, index=input_ids.unsqueeze(2)
        ).squeeze(2)
        
        # Mask prompt (simplified: take last logits_to_keep tokens)
        if logits_to_keep < per_token_logps.shape[1]:
            per_token_logps = per_token_logps[:, -logits_to_keep:]
            
        return per_token_logps.sum(-1)

    def train_step(self, batch):
        """Override train step for DPO"""
        # Batch should contain: chosen_input_ids, rejected_input_ids, etc.
        # Expected format: {
        #   "prompt_ids": tensor,      # (B, prompt_len)
        #   "chosen_ids": tensor,      # (B, chosen_len)
        #   "rejected_ids": tensor,    # (B, rejected_len)
        #   "attention_mask": tensor   # Optional
        # }
        
        self.model.train()
        
        # Extract batch components
        prompt_ids = batch.get("prompt_ids")
        chosen_ids = batch.get("chosen_ids")
        rejected_ids = batch.get("rejected_ids")
        attention_mask = batch.get("attention_mask", None)
        
        if prompt_ids is None or chosen_ids is None or rejected_ids is None:
            raise ValueError("DPO batch must contain 'prompt_ids', 'chosen_ids', and 'rejected_ids'")
        
        # Concatenate prompt + chosen/rejected for efficient forward pass
        chosen_input_ids = torch.cat([prompt_ids, chosen_ids], dim=1)
        rejected_input_ids = torch.cat([prompt_ids, rejected_ids], dim=1)
        
        # Get log probabilities for chosen sequence
        chosen_logps = self._get_batch_logps(
            self.model,
            chosen_input_ids,
            attention_mask=None,  # Simplified - would need proper masking
            logits_to_keep=chosen_ids.shape[1]
        )
        
        # Get log probabilities for rejected sequence
        rejected_logps = self._get_batch_logps(
            self.model,
            rejected_input_ids,
            attention_mask=None,  # Simplified
            logits_to_keep=rejected_ids.shape[1]
        )
        
        # Reference model forward (no grad)
        with torch.no_grad():
            ref_chosen_logps = self._get_batch_logps(
                self.ref_model,
                chosen_input_ids,
                attention_mask=None,
                logits_to_keep=chosen_ids.shape[1]
            )
            ref_rejected_logps = self._get_batch_logps(
                self.ref_model,
                rejected_input_ids,
                attention_mask=None,
                logits_to_keep=rejected_ids.shape[1]
            )
        
        # Compute DPO loss
        loss, chosen_rewards, rejected_rewards = self.dpo_loss(
            chosen_logps,
            rejected_logps,
            ref_chosen_logps,
            ref_rejected_logps
        )
        
        return {
            "loss": loss,
            "chosen_rewards": chosen_rewards.item(),
            "rejected_rewards": rejected_rewards.item()
        }


def train_dpo(
    model: nn.Module,
    dataset: List[Dict],
    tokenizer,
    ref_model: Optional[nn.Module] = None,
    beta: float = 0.1,
    num_epochs: int = 3
):
    """
    Helper function for DPO training
    
    Args:
        model: Policy model to train
        dataset: List of dicts with 'prompt', 'chosen', 'rejected' keys
        tokenizer: Tokenizer for encoding text
        ref_model: Reference model (optional, will copy policy model if None)
        beta: DPO temperature parameter
        num_epochs: Number of training epochs
        
    Returns:
        Trained model
    """
    config = DPOConfig(beta=beta, num_epochs=num_epochs)
    trainer = DPOTrainer(model, ref_model, config, tokenizer)
    
    print("🚀 Starting DPO Alignment...")
    
    # Process dataset into DPO format
    # Expected format: [{"prompt": "...", "chosen": "...", "rejected": "..."}, ...]
    if dataset and isinstance(dataset[0], dict):
        # Check if dataset is already in correct format
        if "prompt" in dataset[0] and "chosen" in dataset[0] and "rejected" in dataset[0]:
            print(f"   Found {len(dataset)} preference pairs")
            # Dataset is in correct format, can proceed with training
            # Note: Full training requires DataLoader with proper collator
            # For now, we'll prepare the trainer and return it
            print("   ✅ DPO Trainer ready (use trainer.train() with DataLoader)")
        else:
            print("   ⚠️  Dataset format incorrect. Expected: {'prompt', 'chosen', 'rejected'}")
            print("   Please format your dataset with these keys.")
    else:
        print("   ⚠️  Empty or invalid dataset provided")
    
    return trainer
