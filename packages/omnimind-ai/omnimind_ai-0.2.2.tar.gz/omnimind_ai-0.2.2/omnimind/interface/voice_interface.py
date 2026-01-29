"""
OMNIMIND Interface Layer - Voice Interface
Voice I/O Handler (Optional)
"""
from typing import Optional, Generator
from dataclasses import dataclass
import asyncio
import tempfile
import os


@dataclass
class VoiceMessage:
    """Voice message structure"""
    text: str           # Transcribed text
    audio_path: str     # Path to audio file
    language: str       # Detected language
    confidence: float   # Transcription confidence


class VoiceInterface:
    """
    Voice Interface - Voice I/O Handler
    
    ทำหน้าที่:
    - Speech-to-Text (STT) using Whisper
    - Text-to-Speech (TTS) using edge-tts
    - Voice Activity Detection
    """
    
    def __init__(self, 
                 whisper_model: str = "base",
                 tts_voice: str = "th-TH-PremwadeeNeural"):
        self.whisper_model = whisper_model
        self.tts_voice = tts_voice
        self._whisper = None
        self._temp_dir = tempfile.gettempdir()
    
    def _load_whisper(self):
        """Lazy load Whisper model"""
        if self._whisper is None:
            try:
                import whisper
                print(f"🔄 Loading Whisper model: {self.whisper_model}")
                self._whisper = whisper.load_model(self.whisper_model)
                print("✅ Whisper loaded!")
            except ImportError:
                print("⚠️ Whisper not installed. Run: pip install openai-whisper")
                raise
    
    def transcribe(self, audio_path: str, language: str = "th") -> VoiceMessage:
        """
        Transcribe audio file to text using Whisper
        
        Args:
            audio_path: Path to audio file
            language: Language code (th, en, etc.)
            
        Returns:
            VoiceMessage with transcribed text
        """
        self._load_whisper()
        
        result = self._whisper.transcribe(
            audio_path,
            language=language,
            task="transcribe"
        )
        
        return VoiceMessage(
            text=result["text"].strip(),
            audio_path=audio_path,
            language=result.get("language", language),
            confidence=1.0  # Whisper doesn't provide confidence
        )
    
    async def speak_async(self, text: str, output_path: str = None) -> str:
        """
        Convert text to speech asynchronously
        
        Args:
            text: Text to speak
            output_path: Output audio file path
            
        Returns:
            Path to generated audio file
        """
        try:
            import edge_tts
        except ImportError:
            print("⚠️ edge-tts not installed. Run: pip install edge-tts")
            raise
        
        if output_path is None:
            output_path = os.path.join(self._temp_dir, "omnimind_speech.mp3")
        
        communicate = edge_tts.Communicate(text, self.tts_voice)
        await communicate.save(output_path)
        
        return output_path
    
    def speak(self, text: str, output_path: str = None) -> str:
        """
        Convert text to speech (synchronous wrapper)
        
        Args:
            text: Text to speak
            output_path: Output audio file path
            
        Returns:
            Path to generated audio file
        """
        return asyncio.run(self.speak_async(text, output_path))
    
    async def speak_stream_async(self, text: str) -> Generator[bytes, None, None]:
        """
        Stream TTS audio chunks
        
        Args:
            text: Text to speak
            
        Yields:
            Audio data chunks
        """
        try:
            import edge_tts
        except ImportError:
            raise ImportError("edge-tts not installed")
        
        communicate = edge_tts.Communicate(text, self.tts_voice)
        
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                yield chunk["data"]
    
    def get_available_voices(self, language: str = "th") -> list:
        """
        Get available TTS voices for a language
        
        Args:
            language: Language code
            
        Returns:
            List of available voice names
        """
        # Common Thai voices in edge-tts
        thai_voices = [
            "th-TH-PremwadeeNeural",  # Female
            "th-TH-NiwatNeural",       # Male
        ]
        
        if language == "th":
            return thai_voices
        
        # For other languages, return empty (would need to query edge-tts)
        return []
    
    def is_available(self) -> bool:
        """Check if voice interface is available"""
        try:
            import whisper
            import edge_tts
            return True
        except ImportError:
            return False


class SimpleVoiceRecorder:
    """
    Simple voice recorder using sounddevice
    (For demo purposes)
    """
    
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self._recording = False
    
    def record(self, duration: float = 5.0, output_path: str = None) -> str:
        """
        Record audio for specified duration
        
        Args:
            duration: Recording duration in seconds
            output_path: Output file path
            
        Returns:
            Path to recorded audio file
        """
        try:
            import sounddevice as sd
            import scipy.io.wavfile as wav
            import numpy as np
        except ImportError:
            raise ImportError("sounddevice and scipy required for recording")
        
        if output_path is None:
            output_path = os.path.join(tempfile.gettempdir(), "omnimind_input.wav")
        
        print(f"🎤 Recording for {duration} seconds...")
        
        # Record
        audio = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=1,
            dtype=np.float32
        )
        sd.wait()
        
        # Save
        wav.write(output_path, self.sample_rate, audio)
        
        print("✅ Recording complete!")
        return output_path
