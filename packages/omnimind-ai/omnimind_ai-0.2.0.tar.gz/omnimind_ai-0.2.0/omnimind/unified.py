"""
OMNIMIND Unified Model
The "One Model" that integrates all capabilities:
- SSM Core (Thinking & Text)
- Multimodal (Vision, Audio, Video, Code Inputs)
- Creative Lab (Image, Video, Music, Doc Generation)
- Cognitive Tools (Math, Coding, Translation, Realtime Vision)
- Real-time Interface (Voice I/O)
- Text-to-Text (T2T) - Chat & Generation
- Text-to-Speech (TTS) - Voice synthesis
- Speech-to-Text (STT) - Voice transcription
- Agent AI - Autonomous task execution

Usage:
    omnimind = Omnimind("micro")
    omnimind.chat("Hello")                    # Text-to-Text
    omnimind.text_to_speech("สวัสดี")          # TTS
    omnimind.speech_to_text("audio.wav")      # STT
    omnimind.agent_run("Search and summarize") # Agent AI
    omnimind.create("image of a cat")         # Creative
    omnimind.listen()                          # Real-time voice mode
"""
import torch
import torch.nn as nn
from typing import Optional, List, Union, Dict, Any, Callable

# Core
from .model.omnimind_model import create_model
from .training.multilingual_tokenizer import MultilingualTokenizer

# Multimodal Inputs
from .model.multimodal import OmnimindMultimodal, MultimodalConfig

# Generation Capabilities
from .generation.media_generator import OmnimindCreativeLab
from .generation.document_generator import DocumentGenerator
from .model.music import OmnimindMusic

# Cognitive & Tools
from .cognitive.tool_use import ToolAgent, ToolRegistry
from .cognitive.realtime import RealtimeAgent, RealtimeConfig
from .cognitive.standard_tools import get_standard_tools

# Voice Interface (TTS/STT)
from .interface.voice_interface import VoiceInterface, VoiceMessage, SimpleVoiceRecorder

class Omnimind:
    """
    The Ultimate OMNIMIND Model
    Combines Intelligence, Perception, Creation, and Interaction.
    """
    
    def __init__(self, size: str = "micro", device: str = None):
        print(f"🧠 Initializing OMNIMIND ({size})...")
        if device == "auto" or device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        # 1. Core Intelligence (SSM)
        self.tokenizer = MultilingualTokenizer()
        self.core = create_model(size).to(self.device)
        self.core.eval()
        
        # 2. Perception (Multimodal Inputs)
        self.senses = OmnimindMultimodal().to(self.device)
        
        # 3. Creativity (Generation Engines)
        self.creator = OmnimindCreativeLab()
        self.musician = OmnimindMusic()
        self.writer = DocumentGenerator()
        
        # 4. Cognition (Tools & Agent)
        # Register all standard tools automatically
        self.tools = get_standard_tools()
        
        # Register Creation tools into the Agent's toolset
        self.tools.extend([
            self.creator.create_image,
            self.creator.create_video,
            self.creator.create_audio,
            self.musician.encode_midi, # Symbolic music gen
            self.writer.create_pdf,
            self.writer.create_docx
        ])
        
        # Create the Cognitive Agent wrapper
        self.agent = ToolAgent(
            model=self.core,
            tokenizer=self.tokenizer,
            tools=self.tools
        )
        
        # 5. Interaction (Real-time Voice)
        # Lazy load voice interface to speed up init if not needed
        self._realtime_agent = None
        self._voice_interface = None
        self._recorder = None
        
        # 6. Conversation history for agent
        self._history: List[Dict[str, str]] = []
        
        print("✅ OMNIMIND Ready: All systems online.")

    def chat(self, user_input: str, history: List[Dict] = None) -> str:
        """
        Smart Chat with Tool Use (Text Mode)
        """
        history = history or []
        print(f"👤 You: {user_input}")
        
        # Agent handles thinking and tool use automatically
        response = self.agent.process_turn(user_input, history)
        
        print(f"🤖 OMNIMIND: {response}")
        return response

    def create(self, prompt: str, media_type: str = "image") -> str:
        """
        Direct Creation Mode
        """
        if media_type == "image":
            return self.creator.create_image(prompt)
        elif media_type == "video":
            return self.creator.create_video(prompt)
        elif media_type == "music":
            return self.creator.create_audio(prompt)
        elif media_type == "document":
            return self.writer.create_pdf(prompt, "document.pdf")
        else:
            return "Unknown media type"

    def listen(self):
        """
        Start Real-time Voice Mode
        """
        if not self._realtime_agent:
            try:
                from .interface.voice_interface import VoiceInterface
                voice = VoiceInterface()
                self._realtime_agent = RealtimeAgent(
                    model=self.core,
                    tokenizer=self.tokenizer,
                    voice_interface=voice,
                    tools=self.tools
                )
            except ImportError as e:
                print(f"❌ Voice interface error: {e}")
                return

        import asyncio
        asyncio.run(self._realtime_agent.start_session())

    def compose_music(self, midi_path: str):
        """Analyze or Compose symbolic music"""
        return self.musician.encode_midi(midi_path)

    # ========== TEXT-TO-TEXT (T2T) ==========
    def text_to_text(self, input_text: str, max_tokens: int = 256) -> str:
        """
        Pure text generation without tool use
        
        Args:
            input_text: Input text prompt
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text response
        """
        ids = self.tokenizer.encode(input_text)
        input_tensor = torch.tensor([ids]).to(self.device)
        
        with torch.no_grad():
            output_ids = self.core.generate(input_tensor, max_new_tokens=max_tokens)
        
        return self.tokenizer.decode(output_ids[0].tolist())
    
    def t2t(self, input_text: str, max_tokens: int = 256) -> str:
        """Alias for text_to_text"""
        return self.text_to_text(input_text, max_tokens)

    # ========== TEXT-TO-SPEECH (TTS) ==========
    def _ensure_voice_interface(self):
        """Lazy load voice interface"""
        if self._voice_interface is None:
            self._voice_interface = VoiceInterface()
    
    def text_to_speech(self, text: str, output_path: str = None, 
                       voice: str = None) -> str:
        """
        Convert text to speech audio
        
        Args:
            text: Text to convert to speech
            output_path: Output audio file path (optional)
            voice: Voice name (optional, default: Thai female)
            
        Returns:
            Path to generated audio file
        """
        self._ensure_voice_interface()
        
        if voice:
            self._voice_interface.tts_voice = voice
            
        audio_path = self._voice_interface.speak(text, output_path)
        print(f"🔊 TTS: Generated audio at {audio_path}")
        return audio_path
    
    def tts(self, text: str, output_path: str = None) -> str:
        """Alias for text_to_speech"""
        return self.text_to_speech(text, output_path)
    
    async def text_to_speech_stream(self, text: str):
        """
        Stream TTS audio chunks (async)
        
        Args:
            text: Text to convert
            
        Yields:
            Audio data chunks
        """
        self._ensure_voice_interface()
        async for chunk in self._voice_interface.speak_stream_async(text):
            yield chunk

    # ========== SPEECH-TO-TEXT (STT) ==========
    def speech_to_text(self, audio_path: str, language: str = "th") -> str:
        """
        Transcribe audio to text
        
        Args:
            audio_path: Path to audio file
            language: Language code (th, en, etc.)
            
        Returns:
            Transcribed text
        """
        self._ensure_voice_interface()
        
        result = self._voice_interface.transcribe(audio_path, language)
        print(f"🎤 STT: '{result.text}' (lang={result.language})")
        return result.text
    
    def stt(self, audio_path: str, language: str = "th") -> str:
        """Alias for speech_to_text"""
        return self.speech_to_text(audio_path, language)
    
    def record_and_transcribe(self, duration: float = 5.0, 
                               language: str = "th") -> str:
        """
        Record audio from microphone and transcribe
        
        Args:
            duration: Recording duration in seconds
            language: Language code
            
        Returns:
            Transcribed text
        """
        if self._recorder is None:
            self._recorder = SimpleVoiceRecorder()
        
        audio_path = self._recorder.record(duration)
        return self.speech_to_text(audio_path, language)

    # ========== SPEECH-TO-SPEECH (S2S) ==========
    def speech_to_speech(self, audio_path: str, language: str = "th") -> str:
        """
        Full voice conversation: STT -> Process -> TTS
        
        Args:
            audio_path: Input audio file
            language: Language code
            
        Returns:
            Path to response audio file
        """
        # 1. STT
        user_text = self.speech_to_text(audio_path, language)
        
        # 2. Process with Agent
        response_text = self.chat(user_text)
        
        # 3. TTS
        return self.text_to_speech(response_text)
    
    def s2s(self, audio_path: str, language: str = "th") -> str:
        """Alias for speech_to_speech"""
        return self.speech_to_speech(audio_path, language)

    # ========== AGENT AI ==========
    def agent_run(self, task: str, max_iterations: int = 10, 
                  verbose: bool = True) -> str:
        """
        Run Agent AI for autonomous task execution
        
        The agent will:
        - Break down complex tasks
        - Use available tools automatically
        - Loop until task is complete
        
        Args:
            task: Task description
            max_iterations: Maximum tool call iterations
            verbose: Print progress
            
        Returns:
            Final response
        """
        if verbose:
            print(f"🤖 Agent AI: Starting task...")
            print(f"   Task: {task}")
            print(f"   Tools: {len(self.tools)} available")
        
        # Use agent with fresh history for isolated task
        response = self.agent.process_turn(task, [])
        
        if verbose:
            print(f"✅ Agent AI: Task completed")
        
        return response
    
    def agent_chat(self, user_input: str) -> str:
        """
        Chat with Agent AI (maintains conversation history)
        
        Args:
            user_input: User message
            
        Returns:
            Agent response
        """
        response = self.agent.process_turn(user_input, self._history)
        
        # Update history
        self._history.append({"role": "user", "content": user_input})
        self._history.append({"role": "assistant", "content": response})
        
        return response
    
    def agent_reset(self):
        """Reset agent conversation history"""
        self._history = []
        print("🔄 Agent history cleared")
    
    def register_tool(self, func: Callable):
        """
        Register a custom tool for the agent
        
        Args:
            func: Python function with docstring
        """
        self.tools.append(func)
        self.agent.registry.register(func)
        print(f"🔧 Tool registered: {func.__name__}")

    # ========== AVAILABLE VOICES ==========
    def get_available_voices(self, language: str = "th") -> List[str]:
        """Get available TTS voices for a language"""
        self._ensure_voice_interface()
        return self._voice_interface.get_available_voices(language)

    # ========== STREAMING GENERATION ==========
    def generate_stream(self, prompt: str, max_tokens: int = 256, 
                        temperature: float = 0.7):
        """
        Stream text generation token by token
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Yields:
            Generated tokens one at a time
        """
        ids = self.tokenizer.encode(prompt)
        input_tensor = torch.tensor([ids]).to(self.device)
        
        # Process prompt
        with torch.no_grad():
            outputs = self.core.model.forward(input_tensor, return_cache=True)
            cache = outputs["cache"]
            logits = outputs["logits"][:, -1, :]
        
        for _ in range(max_tokens):
            # Sample next token
            if temperature > 0:
                logits = logits / temperature
                probs = torch.softmax(logits, dim=-1)
                next_token = torch.multinomial(probs, num_samples=1)
            else:
                next_token = logits.argmax(dim=-1, keepdim=True)
            
            # Decode and yield
            token_text = self.tokenizer.decode([next_token.item()])
            yield token_text
            
            # Check EOS
            if next_token.item() == self.tokenizer.eos_token_id:
                break
            
            # Forward one step
            with torch.no_grad():
                outputs = self.core.model.forward(next_token, cache=cache, return_cache=True)
                cache = outputs["cache"]
                logits = outputs["logits"][:, -1, :]

    # ========== MULTIMODAL METHODS ==========
    def see(self, image_path: str) -> torch.Tensor:
        """
        Process an image and get visual features
        
        Args:
            image_path: Path to image file
            
        Returns:
            Visual feature tensor
        """
        from .model.multimodal import preprocess_image
        image_tensor = preprocess_image(image_path).to(self.device)
        return self.senses.encode_image(image_tensor)
    
    def hear(self, audio_path: str) -> torch.Tensor:
        """
        Process audio and get audio features
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Audio feature tensor
        """
        from .model.multimodal import preprocess_audio
        audio_tensor = preprocess_audio(audio_path).to(self.device)
        return self.senses.encode_audio(audio_tensor)

    # ========== UTILITY METHODS ==========
    def info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "size": self.config.name if hasattr(self.config, 'name') else "unknown",
            "parameters": sum(p.numel() for p in self.core.parameters()),
            "device": str(self.device),
            "tools_available": len(self.tools),
            "capabilities": [
                "text_to_text", "text_to_speech", "speech_to_text",
                "speech_to_speech", "agent", "create_image", 
                "create_video", "create_audio", "vision", "audio"
            ]
        }

    @property
    def config(self):
        return self.core.config


# ==================== LITE VERSION ====================
class OmnimindLite:
    """
    Lightweight version of Omnimind - Text only, no multimodal
    Faster to load, lower memory footprint
    """
    
    def __init__(self, size: str = "micro", device: str = None):
        print(f"🧠 Initializing OMNIMIND Lite ({size})...")
        
        if device == "auto" or device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        # Core only
        self.tokenizer = MultilingualTokenizer()
        self.core = create_model(size).to(self.device)
        self.core.eval()
        
        # Basic tools only
        from .cognitive.standard_tools import MathTools, WebSearch, DateTimeTool
        self.tools = [
            MathTools.calculate,
            WebSearch.search,
            DateTimeTool.get_current_time,
        ]
        
        self.agent = ToolAgent(
            model=self.core,
            tokenizer=self.tokenizer,
            tools=self.tools
        )
        
        self._history = []
        print("✅ OMNIMIND Lite Ready")
    
    def chat(self, user_input: str) -> str:
        """Simple chat"""
        return self.agent.process_turn(user_input, self._history)
    
    def generate(self, prompt: str, max_tokens: int = 256) -> str:
        """Generate text"""
        ids = self.tokenizer.encode(prompt)
        input_tensor = torch.tensor([ids]).to(self.device)
        
        with torch.no_grad():
            output_ids = self.core.generate(input_tensor, max_new_tokens=max_tokens)
        
        return self.tokenizer.decode(output_ids[0].tolist())
    
    def reset(self):
        """Reset conversation"""
        self._history = []


# Convenience
def load_omnimind(size: str = "micro", lite: bool = False) -> Union[Omnimind, OmnimindLite]:
    """
    Load OMNIMIND model
    
    Args:
        size: Model size (tiny, nano, micro, small, etc.)
        lite: If True, load lightweight text-only version
        
    Returns:
        Omnimind or OmnimindLite instance
    """
    if lite:
        return OmnimindLite(size)
    return Omnimind(size)
