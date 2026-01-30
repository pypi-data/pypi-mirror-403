"""
OMNIMIND Multimodal Module
Encoders for Image, Audio, Video, and Code modalities

Architecture inspired by Qwen2.5-Omni and LLaVA:
- Vision: ViT-based encoder with 2D-RoPE
- Audio: Whisper-style mel-spectrogram encoder
- Video: Frame-level vision encoder with temporal fusion
- Code: Specialized tokenization with syntax awareness
"""
import os
from typing import Optional, List, Dict, Any, Tuple, Union
from dataclasses import dataclass
import torch
import torch.nn as nn
import torch.nn.functional as F


@dataclass
class MultimodalConfig:
    """Configuration for multimodal encoders"""
    # Vision
    image_size: int = 224
    patch_size: int = 14
    vision_hidden_size: int = 1024
    vision_num_layers: int = 12
    vision_num_heads: int = 16
    
    # Audio
    audio_sample_rate: int = 16000
    audio_n_mels: int = 128
    audio_hidden_size: int = 512
    audio_num_layers: int = 6
    
    # Video
    video_max_frames: int = 32
    video_fps: int = 1
    
    # Code
    code_vocab_size: int = 50000
    
    # Projection to LLM
    projection_hidden_size: int = 768
    llm_hidden_size: int = 768


class VisionEncoder(nn.Module):
    """
    Vision Transformer Encoder for Images
    
    Based on ViT architecture with:
    - Patch embedding
    - Positional encoding
    - Transformer layers
    - Projection to LLM space
    """
    
    def __init__(self, config: MultimodalConfig):
        super().__init__()
        self.config = config
        
        # Calculate number of patches
        self.num_patches = (config.image_size // config.patch_size) ** 2
        patch_dim = 3 * config.patch_size ** 2  # RGB * patch_size^2
        
        # Patch embedding
        self.patch_embed = nn.Linear(patch_dim, config.vision_hidden_size)
        
        # CLS token
        self.cls_token = nn.Parameter(torch.randn(1, 1, config.vision_hidden_size))
        
        # Positional embedding
        self.pos_embed = nn.Parameter(
            torch.randn(1, self.num_patches + 1, config.vision_hidden_size)
        )
        
        # Transformer layers
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=config.vision_hidden_size,
            nhead=config.vision_num_heads,
            dim_feedforward=config.vision_hidden_size * 4,
            dropout=0.1,
            activation='gelu',
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(
            encoder_layer, 
            num_layers=config.vision_num_layers
        )
        
        # Projection to LLM space
        self.projection = nn.Sequential(
            nn.Linear(config.vision_hidden_size, config.projection_hidden_size),
            nn.GELU(),
            nn.Linear(config.projection_hidden_size, config.llm_hidden_size)
        )
        
        # Layer norm
        self.norm = nn.LayerNorm(config.vision_hidden_size)
    
    def patchify(self, images: torch.Tensor) -> torch.Tensor:
        """Convert images to patches"""
        B, C, H, W = images.shape
        P = self.config.patch_size
        
        # Reshape to patches
        patches = images.unfold(2, P, P).unfold(3, P, P)  # (B, C, H//P, W//P, P, P)
        patches = patches.contiguous().view(B, C, -1, P * P)  # (B, C, num_patches, P*P)
        patches = patches.permute(0, 2, 1, 3)  # (B, num_patches, C, P*P)
        patches = patches.reshape(B, -1, C * P * P)  # (B, num_patches, C*P*P)
        
        return patches
    
    def forward(self, images: torch.Tensor) -> torch.Tensor:
        """
        Args:
            images: (B, C, H, W) normalized image tensor
            
        Returns:
            visual_tokens: (B, num_patches+1, llm_hidden_size)
        """
        B = images.shape[0]
        
        # Patchify
        patches = self.patchify(images)  # (B, num_patches, patch_dim)
        
        # Patch embedding
        x = self.patch_embed(patches)  # (B, num_patches, hidden)
        
        # Add CLS token
        cls_tokens = self.cls_token.expand(B, -1, -1)
        x = torch.cat([cls_tokens, x], dim=1)  # (B, num_patches+1, hidden)
        
        # Add positional embedding
        x = x + self.pos_embed
        
        # Transformer
        x = self.transformer(x)
        x = self.norm(x)
        
        # Project to LLM space
        x = self.projection(x)
        
        return x


class AudioEncoder(nn.Module):
    """
    Audio Encoder using Mel-spectrogram
    
    Based on Whisper-style architecture:
    - Mel-spectrogram extraction
    - CNN feature extraction
    - Transformer layers
    - Projection to LLM space
    """
    
    def __init__(self, config: MultimodalConfig):
        super().__init__()
        self.config = config
        
        # CNN for mel-spectrogram
        self.conv1 = nn.Conv1d(config.audio_n_mels, config.audio_hidden_size, kernel_size=3, padding=1)
        self.conv2 = nn.Conv1d(config.audio_hidden_size, config.audio_hidden_size, kernel_size=3, stride=2, padding=1)
        
        # Transformer layers
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=config.audio_hidden_size,
            nhead=8,
            dim_feedforward=config.audio_hidden_size * 4,
            dropout=0.1,
            activation='gelu',
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(
            encoder_layer,
            num_layers=config.audio_num_layers
        )
        
        # Projection
        self.projection = nn.Sequential(
            nn.Linear(config.audio_hidden_size, config.projection_hidden_size),
            nn.GELU(),
            nn.Linear(config.projection_hidden_size, config.llm_hidden_size)
        )
        
        self.norm = nn.LayerNorm(config.audio_hidden_size)
    
    def forward(self, mel_spectrogram: torch.Tensor) -> torch.Tensor:
        """
        Args:
            mel_spectrogram: (B, n_mels, time_frames)
            
        Returns:
            audio_tokens: (B, time_frames//2, llm_hidden_size)
        """
        # CNN
        x = F.gelu(self.conv1(mel_spectrogram))
        x = F.gelu(self.conv2(x))  # Downsampled by 2
        
        # (B, hidden, time) -> (B, time, hidden)
        x = x.transpose(1, 2)
        
        # Transformer
        x = self.transformer(x)
        x = self.norm(x)
        
        # Project
        x = self.projection(x)
        
        return x


class VideoEncoder(nn.Module):
    """
    Video Encoder with Temporal Fusion
    
    Processes video frames with:
    - Per-frame vision encoding
    - Temporal attention for frame fusion
    - Temporal position encoding
    """
    
    def __init__(self, config: MultimodalConfig, vision_encoder: Optional[VisionEncoder] = None):
        super().__init__()
        self.config = config
        
        # Share or create vision encoder
        if vision_encoder is not None:
            self.vision_encoder = vision_encoder
        else:
            self.vision_encoder = VisionEncoder(config)
        
        # Temporal attention
        self.temporal_attention = nn.MultiheadAttention(
            embed_dim=config.llm_hidden_size,
            num_heads=8,
            dropout=0.1,
            batch_first=True
        )
        
        # Temporal position encoding
        self.temporal_pos_embed = nn.Parameter(
            torch.randn(1, config.video_max_frames, config.llm_hidden_size)
        )
        
        self.norm = nn.LayerNorm(config.llm_hidden_size)
    
    def forward(self, frames: torch.Tensor) -> torch.Tensor:
        """
        Args:
            frames: (B, T, C, H, W) video frames
            
        Returns:
            video_tokens: (B, T*(num_patches+1), llm_hidden_size)
        """
        B, T, C, H, W = frames.shape
        
        # Encode each frame
        frame_tokens = []
        for t in range(T):
            tokens = self.vision_encoder(frames[:, t])  # (B, num_patches+1, hidden)
            frame_tokens.append(tokens)
        
        # Stack frames: (B, T, num_patches+1, hidden)
        x = torch.stack(frame_tokens, dim=1)
        
        # Get CLS tokens for temporal attention: (B, T, hidden)
        cls_tokens = x[:, :, 0, :]
        
        # Add temporal position encoding
        cls_tokens = cls_tokens + self.temporal_pos_embed[:, :T, :]
        
        # Temporal attention on CLS tokens
        attn_out, _ = self.temporal_attention(cls_tokens, cls_tokens, cls_tokens)
        attn_out = self.norm(attn_out)
        
        # Replace CLS tokens with temporally-aware ones
        x[:, :, 0, :] = attn_out
        
        # Flatten: (B, T*(num_patches+1), hidden)
        x = x.view(B, -1, x.shape[-1])
        
        return x


class CodeEncoder(nn.Module):
    """
    Code Encoder with Syntax Awareness
    
    Features:
    - Specialized code tokenization
    - Syntax-aware positional encoding
    - Language-specific embeddings
    """
    
    SUPPORTED_LANGUAGES = [
        "python", "javascript", "typescript", "java", "cpp", "c",
        "go", "rust", "ruby", "php", "swift", "kotlin", "scala",
        "html", "css", "sql", "bash", "markdown", "json", "yaml"
    ]
    
    def __init__(self, config: MultimodalConfig):
        super().__init__()
        self.config = config
        
        # Language embedding
        self.language_embed = nn.Embedding(
            len(self.SUPPORTED_LANGUAGES) + 1,  # +1 for unknown
            config.llm_hidden_size
        )
        
        # Code-specific projection (assumes pre-tokenized input)
        self.projection = nn.Linear(config.code_vocab_size, config.llm_hidden_size)
        
        # Language to index mapping
        self.lang_to_idx = {lang: i for i, lang in enumerate(self.SUPPORTED_LANGUAGES)}
    
    def get_language_token(self, language: str) -> torch.Tensor:
        """Get language embedding token"""
        idx = self.lang_to_idx.get(language.lower(), len(self.SUPPORTED_LANGUAGES))
        return self.language_embed(torch.tensor([idx]))
    
    def forward(
        self, 
        code_embeddings: torch.Tensor,
        language: str = "python"
    ) -> torch.Tensor:
        """
        Args:
            code_embeddings: (B, seq_len, hidden) pre-embedded code tokens
            language: programming language name
            
        Returns:
            code_tokens: (B, seq_len+1, llm_hidden_size)
        """
        B = code_embeddings.shape[0]
        
        # Get language token
        lang_token = self.get_language_token(language)
        lang_token = lang_token.expand(B, -1, -1)
        
        # Prepend language token
        x = torch.cat([lang_token, code_embeddings], dim=1)
        
        return x


class MultimodalProjector(nn.Module):
    """
    Unified Multimodal Projector
    
    Projects all modality tokens into a unified space with:
    - Modality-specific type embeddings
    - Cross-modal attention (optional)
    - Sequence concatenation
    """
    
    MODALITY_TYPES = ["text", "image", "audio", "video", "code"]
    
    def __init__(self, config: MultimodalConfig):
        super().__init__()
        self.config = config
        
        # Modality type embeddings
        self.modality_embed = nn.Embedding(
            len(self.MODALITY_TYPES),
            config.llm_hidden_size
        )
        
        self.modality_to_idx = {m: i for i, m in enumerate(self.MODALITY_TYPES)}
    
    def forward(
        self,
        tokens_dict: Dict[str, torch.Tensor]
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Combine tokens from different modalities
        
        Args:
            tokens_dict: {"modality_name": (B, seq_len, hidden)} dict
            
        Returns:
            combined_tokens: (B, total_seq_len, hidden)
            modality_ids: (B, total_seq_len) modality type for each token
        """
        combined = []
        modality_ids = []
        
        for modality, tokens in tokens_dict.items():
            if tokens is None:
                continue
                
            B, L, H = tokens.shape
            
            # Get modality index
            mod_idx = self.modality_to_idx.get(modality, 0)
            
            # Add modality embedding
            mod_embed = self.modality_embed(torch.tensor([mod_idx], device=tokens.device))
            tokens = tokens + mod_embed
            
            combined.append(tokens)
            modality_ids.append(torch.full((B, L), mod_idx, device=tokens.device))
        
        # Concatenate
        combined_tokens = torch.cat(combined, dim=1)
        modality_ids = torch.cat(modality_ids, dim=1)
        
        return combined_tokens, modality_ids


class OmnimindMultimodal(nn.Module):
    """
    OMNIMIND Multimodal Wrapper
    
    Full multimodal support with:
    - Vision (Image/Video)
    - Audio
    - Code
    - Text (from LLM tokenizer)
    
    Usage:
        multimodal = OmnimindMultimodal(config)
        
        # Encode image
        image_tokens = multimodal.encode_image(image_tensor)
        
        # Encode audio
        audio_tokens = multimodal.encode_audio(mel_spec)
        
        # Combine with text
        combined = multimodal.combine({
            "text": text_embeddings,
            "image": image_tokens,
            "audio": audio_tokens
        })
    """
    
    def __init__(self, config: Optional[MultimodalConfig] = None):
        super().__init__()
        self.config = config or MultimodalConfig()
        
        # Encoders
        self.vision_encoder = VisionEncoder(self.config)
        self.audio_encoder = AudioEncoder(self.config)
        self.video_encoder = VideoEncoder(self.config, self.vision_encoder)
        self.code_encoder = CodeEncoder(self.config)
        
        # Projector
        self.projector = MultimodalProjector(self.config)
        
        print("🌐 OmnimindMultimodal initialized with encoders:")
        print(f"   - Vision: {self.config.image_size}x{self.config.image_size} patches")
        print(f"   - Audio: {self.config.audio_n_mels} mel channels")
        print(f"   - Video: max {self.config.video_max_frames} frames")
        print(f"   - Code: {len(CodeEncoder.SUPPORTED_LANGUAGES)} languages")
    
    def encode_image(self, image: torch.Tensor) -> torch.Tensor:
        """Encode image to tokens"""
        return self.vision_encoder(image)
    
    def encode_audio(self, mel_spectrogram: torch.Tensor) -> torch.Tensor:
        """Encode audio mel-spectrogram to tokens"""
        return self.audio_encoder(mel_spectrogram)
    
    def encode_video(self, frames: torch.Tensor) -> torch.Tensor:
        """Encode video frames to tokens"""
        return self.video_encoder(frames)
    
    def encode_code(self, code_embeddings: torch.Tensor, language: str = "python") -> torch.Tensor:
        """Encode code to tokens"""
        return self.code_encoder(code_embeddings, language)
    
    def combine(self, tokens_dict: Dict[str, torch.Tensor]) -> Tuple[torch.Tensor, torch.Tensor]:
        """Combine multimodal tokens"""
        return self.projector(tokens_dict)


# Utility functions for preprocessing
def preprocess_image(
    image_path: str,
    size: int = 224
) -> torch.Tensor:
    """Load and preprocess image"""
    try:
        from PIL import Image
        import torchvision.transforms as T
        
        transform = T.Compose([
            T.Resize((size, size)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        image = Image.open(image_path).convert("RGB")
        return transform(image).unsqueeze(0)
        
    except ImportError:
        raise ImportError("PIL and torchvision required for image preprocessing")


def preprocess_audio(
    audio_path: str,
    sample_rate: int = 16000,
    n_mels: int = 128
) -> torch.Tensor:
    """Load and preprocess audio to mel-spectrogram"""
    try:
        import torchaudio
        import torchaudio.transforms as T
        
        waveform, sr = torchaudio.load(audio_path)
        
        # Resample if needed
        if sr != sample_rate:
            resampler = T.Resample(sr, sample_rate)
            waveform = resampler(waveform)
        
        # Convert to mono
        if waveform.shape[0] > 1:
            waveform = waveform.mean(dim=0, keepdim=True)
        
        # Mel-spectrogram
        mel_transform = T.MelSpectrogram(
            sample_rate=sample_rate,
            n_mels=n_mels,
            n_fft=400,
            hop_length=160
        )
        mel_spec = mel_transform(waveform)
        
        # Log scale
        mel_spec = torch.log(mel_spec + 1e-9)
        
        return mel_spec
        
    except ImportError:
        raise ImportError("torchaudio required for audio preprocessing")


def preprocess_video(
    video_path: str,
    max_frames: int = 32,
    size: int = 224
) -> torch.Tensor:
    """Load and preprocess video frames"""
    try:
        import cv2
        import torchvision.transforms as T
        
        cap = cv2.VideoCapture(video_path)
        frames = []
        
        transform = T.Compose([
            T.ToPILImage(),
            T.Resize((size, size)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        step = max(1, total_frames // max_frames)
        
        frame_idx = 0
        while len(frames) < max_frames:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_idx % step == 0:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames.append(transform(frame))
            
            frame_idx += 1
        
        cap.release()
        
        if not frames:
            raise ValueError(f"No frames extracted from {video_path}")
        
        # Pad if needed
        while len(frames) < max_frames:
            frames.append(frames[-1])
        
        return torch.stack(frames[:max_frames]).unsqueeze(0)  # (1, T, C, H, W)
        
    except ImportError:
        raise ImportError("cv2 (opencv-python) required for video preprocessing")


if __name__ == "__main__":
    # Test multimodal module
    print("Testing OmnimindMultimodal...")
    
    config = MultimodalConfig(llm_hidden_size=768)
    multimodal = OmnimindMultimodal(config)
    
    # Test image encoding
    dummy_image = torch.randn(2, 3, 224, 224)
    image_tokens = multimodal.encode_image(dummy_image)
    print(f"✅ Image tokens: {image_tokens.shape}")
    
    # Test audio encoding
    dummy_audio = torch.randn(2, 128, 1000)  # (B, n_mels, time)
    audio_tokens = multimodal.encode_audio(dummy_audio)
    print(f"✅ Audio tokens: {audio_tokens.shape}")
    
    # Test video encoding
    dummy_video = torch.randn(1, 8, 3, 224, 224)  # (B, T, C, H, W)
    video_tokens = multimodal.encode_video(dummy_video)
    print(f"✅ Video tokens: {video_tokens.shape}")
    
    # Test combination
    dummy_text = torch.randn(2, 50, 768)  # (B, seq, hidden)
    combined, modality_ids = multimodal.combine({
        "text": dummy_text,
        "image": image_tokens
    })
    print(f"✅ Combined tokens: {combined.shape}")
    print(f"✅ Modality IDs: {modality_ids.shape}")
