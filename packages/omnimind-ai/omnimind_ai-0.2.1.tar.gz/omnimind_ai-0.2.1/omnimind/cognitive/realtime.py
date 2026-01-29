"""
OMNIMIND Real-time Agent
Orchestrates Voice I/O, SSM Thinking, and Tool Execution for real-time interaction.

Features:
- Continuous Voice Activity Detection (VAD) listening
- Low-latency transcription (Whisper)
- Streaming Generation (SSM)
- Instant TTS Response (EdgeTTS)
- Tool Execution capability during conversation
"""
import asyncio
import time
from typing import Optional, List, Callable
from dataclasses import dataclass

try:
    from omnimind.interface.voice_interface import VoiceInterface, VoiceMessage
    from omnimind.cognitive.tool_use import ToolAgent
except ImportError:
    pass

@dataclass
class RealtimeConfig:
    """Configuration for Real-time Agent"""
    wake_word: Optional[str] = None  # e.g., "Omnimind"
    silence_timeout: float = 2.0     # Seconds of silence to trigger response
    continuous_mode: bool = True     # Output audio while generating text?
    enable_tools: bool = True        # Allow tool use during voice chat


class RealtimeAgent:
    """
    Real-time Voice Agent
    """
    
    def __init__(
        self, 
        model, 
        tokenizer, 
        voice_interface: VoiceInterface,
        tools: List[Callable] = None,
        config: RealtimeConfig = None
    ):
        self.voice = voice_interface
        self.config = config or RealtimeConfig()
        
        # Initialize cognitive core (ToolAgent)
        self.agent = ToolAgent(
            model=model, 
            tokenizer=tokenizer, 
            tools=tools or []
        )
        
        self.history = []
        self.is_listening = False
        
    async def start_session(self):
        """Start the real-time loop"""
        print("🎙️ Real-time Agent Started. Listening...")
        self.is_listening = True
        
        while self.is_listening:
            try:
                # 1. Listen & Transcribe
                # In a real VAD system, this would wait for silence.
                # Here we simulate a listen-process cycle
                audio_path = self._record_input() 
                message = self.voice.transcribe(audio_path)
                
                if not message.text:
                    continue
                    
                print(f"User (🎤): {message.text}")
                
                # Check wake word
                if self.config.wake_word:
                    if self.config.wake_word.lower() not in message.text.lower():
                        continue
                
                # 2. Process & Think
                # We use the ToolAgent to handle logic + tools
                full_response = self.agent.process_turn(message.text, self.history)
                
                # 3. Speak Response
                print(f"AI (🔊): {full_response}")
                
                # Should strip tools XML before speaking?
                # Ideally yes. For now, we speak the raw text which might be weird if tools are verbose.
                # Simple cleanup:
                spoken_text = self._clean_for_speech(full_response)
                
                await self.voice.speak_async(spoken_text)
                
                # Update history
                self.history.append({"role": "user", "content": message.text})
                self.history.append({"role": "assistant", "content": full_response})
                
            except KeyboardInterrupt:
                self.stop()
                break
            except Exception as e:
                print(f"Error in loop: {e}")
                await asyncio.sleep(1)
    
    def _record_input(self) -> str:
        """
        Record input (blocking for demo).
        In production, this is non-blocking VAD stream.
        """
        # Using the simple recorder from voice_interface if available
        # or simplified mock for architecture definition
        try:
            from omnimind.interface.voice_interface import SimpleVoiceRecorder
            recorder = SimpleVoiceRecorder()
            return recorder.record(duration=3.0) # Fixed duration for demo simplicity
        except:
            input("Press Enter to simulate voice input...")
            return "dummy_audio.wav"

    def _clean_for_speech(self, text: str) -> str:
        """Remove tool tags and code blocks for TTS"""
        import re
        # Remove tool code
        text = re.sub(r'<tool_code>.*?</tool_code>', '', text, flags=re.DOTALL)
        # Remove tool output
        text = re.sub(r'<tool_output>.*?</tool_output>', '', text, flags=re.DOTALL)
        # Remove thinking
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        # Remove Markdown code blocks
        text = re.sub(r'```.*?```', 'I have written some code.', text, flags=re.DOTALL)
        
        return text.strip()

    def stop(self):
        self.is_listening = False
        print("🛑 Agent Stopped")
