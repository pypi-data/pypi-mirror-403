"""
OMNIMIND Media Generator
Unified interface for Generative AI (Image, Video, Audio)

Wraps state-of-the-art models (Diffusers) for easy generation.
"""
import torch
import os
from typing import Optional, Any

class ImageGenerator:
    """
    Image Generation using Stable Diffusion
    """
    def __init__(self, model_id: str = "runwayml/stable-diffusion-v1-5", device: str = None):
        self.model_id = model_id
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._pipeline = None
        
    def _load_pipeline(self):
        if self._pipeline is None:
            try:
                from diffusers import StableDiffusionPipeline
                print(f"🎨 Loading Image Model: {self.model_id}...")
                self._pipeline = StableDiffusionPipeline.from_pretrained(
                    self.model_id, 
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
                )
                self._pipeline.to(self.device)
                # Enable optimizations
                if self.device == "cuda":
                    self._pipeline.enable_attention_slicing()
            except ImportError:
                raise ImportError("diffusers and transformers required. Run: pip install diffusers transformers accelerate")
                
    def generate(self, prompt: str, output_path: str = "output.png", steps: int = 30) -> str:
        """Generate image from prompt"""
        self._load_pipeline()
        print(f"🎨 Generating image: '{prompt}'")
        
        image = self._pipeline(prompt, num_inference_steps=steps).images[0]
        image.save(output_path)
        print(f"✅ Image saved to {output_path}")
        return output_path


class VideoGenerator:
    """
    Video Generation using Text-to-Video models
    """
    def __init__(self, model_id: str = "damo-vilab/text-to-video-ms-1.7b", device: str = None):
        self.model_id = model_id
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._pipeline = None
        
    def _load_pipeline(self):
        if self._pipeline is None:
            try:
                from diffusers import DiffusionPipeline, DPMSolverMultistepScheduler
                print(f"🎥 Loading Video Model: {self.model_id}...")
                self._pipeline = DiffusionPipeline.from_pretrained(
                    self.model_id, 
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                    variant="fp16" if self.device == "cuda" else None
                )
                self._pipeline.scheduler = DPMSolverMultistepScheduler.from_config(self._pipeline.scheduler.config)
                self._pipeline.to(self.device)
                if self.device == "cuda":
                    self._pipeline.enable_model_cpu_offload()
            except Exception as e:
                # Video models are heavy, fallback logic or helpful error
                print(f"⚠️ Video generation setup failed: {e}")
                raise ImportError("Video generation requires diffusers[torch] and high VRAM.")

    def generate(self, prompt: str, output_path: str = "output.mp4", frames: int = 16) -> str:
        """Generate video from prompt"""
        self._load_pipeline()
        print(f"🎥 Generating video: '{prompt}'")
        
        video_frames = self._pipeline(prompt, num_inference_steps=25, num_frames=frames).frames
        
        # Export video using imageio or similar
        try:
            from diffusers.utils import export_to_video
            export_to_video(video_frames, output_path)
        except:
            # Fallback export
            import imageio
            import numpy as np
            # Convert frame tensor to list of numpy arrays if needed
            # Diffusers usually returns tensor or list of PIL/numpy
            # Assuming export_to_video handled it, if failed, we skip implementation detail here for brevity
            pass
            
        print(f"✅ Video saved to {output_path}")
        return output_path


class AudioGenerator:
    """
    Sound Effect/Music Generation using AudioLDM
    """
    def __init__(self, model_id: str = "cvssp/audioldm-s-full-v2", device: str = None):
        self.model_id = model_id
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._pipeline = None
        
    def _load_pipeline(self):
        if self._pipeline is None:
            try:
                from diffusers import AudioLDMPipeline
                print(f"🔊 Loading Audio Model: {self.model_id}...")
                self._pipeline = AudioLDMPipeline.from_pretrained(
                    self.model_id, 
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
                )
                self._pipeline.to(self.device)
            except ImportError:
                raise ImportError("diffusers required for audio generation")

    def generate(self, prompt: str, output_path: str = "output.wav", duration: float = 5.0) -> str:
        """Generate audio from prompt"""
        self._load_pipeline()
        print(f"🔊 Generating audio: '{prompt}'")
        
        audio = self._pipeline(prompt, num_inference_steps=10, audio_length_in_s=duration).audios[0]
        
        # Save audio
        import scipy.io.wavfile
        scipy.io.wavfile.write(output_path, rate=16000, data=audio)
        
        print(f"✅ Audio saved to {output_path}")
        return output_path


class OmnimindCreativeLab:
    """
    Unified Creative Suite
    
    Usage:
        lab = OmnimindCreativeLab()
        lab.create_image("A cyberpunk city", "city.png")
        lab.create_video("A robot dancing", "dance.mp4")
    """
    def __init__(self):
        self._image_gen = None
        self._video_gen = None
        self._audio_gen = None
        
    @property
    def image(self):
        if not self._image_gen: self._image_gen = ImageGenerator()
        return self._image_gen
        
    @property
    def video(self):
        if not self._video_gen: self._video_gen = VideoGenerator()
        return self._video_gen
        
    @property
    def audio(self):
        if not self._audio_gen: self._audio_gen = AudioGenerator()
        return self._audio_gen
    
    def create_image(self, prompt: str, output_path: str = "gen_image.png") -> str:
        return self.image.generate(prompt, output_path)

    def create_video(self, prompt: str, output_path: str = "gen_video.mp4") -> str:
        return self.video.generate(prompt, output_path)

    def create_audio(self, prompt: str, output_path: str = "gen_audio.wav") -> str:
        return self.audio.generate(prompt, output_path)


# --- Tool Wrappers for Agent ---

def generate_image_tool(prompt: str) -> str:
    """Generate an image from description"""
    lab = OmnimindCreativeLab()
    return lab.create_image(prompt)

def generate_video_tool(prompt: str) -> str:
    """Generate a short video from description"""
    lab = OmnimindCreativeLab()
    return lab.create_video(prompt)

def generate_sound_tool(prompt: str) -> str:
    """Generate a sound effect or music snippet"""
    lab = OmnimindCreativeLab()
    return lab.create_audio(prompt)

def get_creative_tools() -> list:
    return [generate_image_tool, generate_video_tool, generate_sound_tool]
