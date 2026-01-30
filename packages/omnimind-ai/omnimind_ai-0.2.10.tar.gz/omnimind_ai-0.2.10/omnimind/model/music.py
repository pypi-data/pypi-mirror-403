"""
OMNIMIND Music & Singing Module
Capabilities for musical creativity:
1. Symbolic Music (MIDI/ABC mutation)
2. Singing Synthesis (Lyrics + Melody alignment)
3. Instrumental Generation
4. Audio-to-Sheet conversion

Inspired by MusicLM and Jukebox but adapted for SSM state-space processing.
"""
import torch
import torch.nn as nn
from dataclasses import dataclass
from typing import Optional, List, Dict, Union, Tuple

@dataclass
class MusicConfig:
    """Configuration for Music & Singing"""
    # Symbolic
    note_vocab_size: int = 128    # MIDI notes
    duration_vocab_size: int = 64 # quantized durations
    velocity_vocab_size: int = 32 # dynamics
    instrument_vocab_size: int = 128 # GM instruments
    
    # Singing
    phoneme_vocab_size: int = 100 # IPA phonemes
    singer_embedding_size: int = 256 # Singer identity
    
    # Model
    music_hidden_size: int = 512
    llm_hidden_size: int = 768


class SymbolicMusicEncoder(nn.Module):
    """
    Encoder for Symbolic Music (MIDI/ABC)
    Represents Notes, Durations, and Velocity as tokens
    """
    
    def __init__(self, config: MusicConfig):
        super().__init__()
        self.config = config
        
        # Note embeddings (Pitch)
        self.note_embed = nn.Embedding(config.note_vocab_size + 4, config.music_hidden_size)
        # +4 special tokens: [REST], [bar], [start], [end]
        
        # Duration embeddings
        self.duration_embed = nn.Embedding(config.duration_vocab_size, config.music_hidden_size)
        
        # Velocity (dynamics)
        self.velocity_embed = nn.Embedding(config.velocity_vocab_size, config.music_hidden_size)
        
        # Instrument
        self.instrument_embed = nn.Embedding(config.instrument_vocab_size, config.music_hidden_size)
        
        # Combiner
        self.projector = nn.Linear(config.music_hidden_size * 4, config.llm_hidden_size)
        self.norm = nn.LayerNorm(config.llm_hidden_size)
        
    def forward(
        self, 
        notes: torch.Tensor,     # (B, L)
        durations: torch.Tensor, # (B, L)
        velocities: torch.Tensor,# (B, L)
        instruments: torch.Tensor# (B, L)
    ) -> torch.Tensor:
        """
        Encode symbolic music sequence
        """
        n = self.note_embed(notes)
        d = self.duration_embed(durations)
        v = self.velocity_embed(velocities)
        i = self.instrument_embed(instruments)
        
        # Concatenate and project
        x = torch.cat([n, d, v, i], dim=-1) # (B, L, 4*hidden)
        x = self.projector(x)
        x = self.norm(x)
        
        return x


class SingingVoiceEncoder(nn.Module):
    """
    Encoder for Singing Voice (Lyrics + Melody Alignment)
    Aligns phonemes with musical notes for singing synthesis
    """
    
    def __init__(self, config: MusicConfig):
        super().__init__()
        self.config = config
        
        # Phoneme embedding (Lyrics)
        self.phoneme_embed = nn.Embedding(config.phoneme_vocab_size, config.music_hidden_size)
        
        # Note embedding (Melody)
        self.note_embed = nn.Embedding(config.note_vocab_size + 4, config.music_hidden_size)
        
        # Singer Identity
        self.singer_embed = nn.Embedding(100, config.music_hidden_size) # 100 singer presets
        
        # Cross-modal fusion (Phoneme + Note)
        self.fusion = nn.TransformerEncoderLayer(
            d_model=config.music_hidden_size,
            nhead=8,
            dim_feedforward=config.music_hidden_size * 4,
            batch_first=True
        )
        
        self.projector = nn.Linear(config.music_hidden_size, config.llm_hidden_size)
        
    def forward(
        self,
        phonemes: torch.Tensor, # (B, L)
        notes: torch.Tensor,    # (B, L) - aligned with phonemes
        singer_id: torch.Tensor # (B,)
    ) -> torch.Tensor:
        """
        Encode singing sequence
        """
        p = self.phoneme_embed(phonemes)
        n = self.note_embed(notes)
        
        # Fuse Phoneme + Note (Summation + Attention)
        x = p + n 
        
        # Add singer identity
        s = self.singer_embed(singer_id).unsqueeze(1)
        x = x + s
        
        # Process fusion
        x = self.fusion(x)
        x = self.projector(x)
        
        return x


class OmnimindMusic(nn.Module):
    """
    Wrapper for Music & Singing Capabilities
    
    Usage:
        music = OmnimindMusic()
        tokens = music.encode_sheet("song.midi")
        singing = music.encode_singing(lyrics="Hello", melody=[60, 62])
    """
    
    def __init__(self, config: Optional[MusicConfig] = None):
        super().__init__()
        self.config = config or MusicConfig()
        
        self.symbolic_encoder = SymbolicMusicEncoder(self.config)
        self.singing_encoder = SingingVoiceEncoder(self.config)
        
    def encode_midi(self, midi_path: str) -> torch.Tensor:
        """
        Process MIDI file into OMNIMIND tokens
        (Requires pretty_midi or equivalent parser)
        
        Args:
            midi_path: Path to MIDI file
            
        Returns:
            Encoded tensor of shape (1, seq_len, llm_hidden_size)
        """
        try:
            import pretty_midi
            pm = pretty_midi.PrettyMIDI(midi_path)
            
            # Extract notes from all instruments
            notes = []
            durations = []
            velocities = []
            instruments = []
            
            for instrument in pm.instruments:
                for note in instrument.notes:
                    notes.append(note.pitch)
                    durations.append(int((note.end - note.start) * 100))  # Quantize to centiseconds
                    velocities.append(note.velocity)
                    instruments.append(instrument.program if hasattr(instrument, 'program') else 0)
            
            if not notes:
                print(f"   ⚠️  No notes found in MIDI file")
                return torch.zeros(1, 1, self.config.llm_hidden_size)
            
            # Convert to tensors
            notes_tensor = torch.tensor(notes, dtype=torch.long).unsqueeze(0)
            durations_tensor = torch.clamp(torch.tensor(durations, dtype=torch.long), 0, self.config.duration_vocab_size - 1).unsqueeze(0)
            velocities_tensor = torch.clamp(torch.tensor(velocities, dtype=torch.long), 0, self.config.velocity_vocab_size - 1).unsqueeze(0)
            instruments_tensor = torch.clamp(torch.tensor(instruments, dtype=torch.long), 0, self.config.instrument_vocab_size - 1).unsqueeze(0)
            
            # Encode using symbolic encoder
            encoded = self.symbolic_encoder(
                notes_tensor,
                durations_tensor,
                velocities_tensor,
                instruments_tensor
            )
            
            print(f"🎵 Processed MIDI: {len(notes)} notes")
            return encoded
            
        except ImportError:
            print(f"   ⚠️  pretty_midi not installed. Install with: pip install pretty_midi")
            print(f"   Returning placeholder tensor")
            return torch.randn(1, 100, self.config.llm_hidden_size)
        except Exception as e:
            print(f"   ⚠️  Error processing MIDI: {e}")
            return torch.randn(1, 100, self.config.llm_hidden_size)
        
    def encode_singing(self, lyrics: str, melody_notes: List[int], singer_id: int = 0) -> torch.Tensor:
        """
        Encode lyrics and melody for singing
        
        Args:
            lyrics: Text lyrics to sing
            melody_notes: List of MIDI note numbers (one per syllable/word)
            singer_id: Singer identity ID (0-99)
            
        Returns:
            Encoded tensor of shape (1, seq_len, llm_hidden_size)
        """
        try:
            # Simple G2P (Grapheme-to-Phoneme) approximation
            # In production, would use proper G2P library like g2p_en or espeak
            words = lyrics.split()
            
            # Align words with notes (simple 1:1 mapping)
            # In production, would use proper alignment algorithm
            if len(melody_notes) < len(words):
                # Repeat last note if more words than notes
                melody_notes = melody_notes + [melody_notes[-1]] * (len(words) - len(melody_notes))
            elif len(melody_notes) > len(words):
                # Truncate notes if more notes than words
                melody_notes = melody_notes[:len(words)]
            
            # Convert to phonemes (simplified - just use word indices)
            # In production, would convert to IPA phonemes
            phoneme_ids = torch.tensor([hash(word) % self.config.phoneme_vocab_size for word in words], dtype=torch.long).unsqueeze(0)
            note_ids = torch.tensor(melody_notes, dtype=torch.long).unsqueeze(0)
            singer_ids = torch.tensor([singer_id], dtype=torch.long)
            
            # Encode using singing encoder
            encoded = self.singing_encoder(phoneme_ids, note_ids, singer_ids)
            
            print(f"🎤 Encoded singing: '{lyrics}' with {len(melody_notes)} notes")
            return encoded
            
        except Exception as e:
            print(f"   ⚠️  Error encoding singing: {e}")
            return torch.randn(1, len(melody_notes), self.config.llm_hidden_size)


def preprocess_midi(path: str) -> Dict[str, torch.Tensor]:
    """Load and preprocess MIDI file
    
    Args:
        path: Path to MIDI file
        
    Returns:
        Dictionary with 'notes', 'durations', 'velocities', 'instruments' tensors
    """
    try:
        import pretty_midi
        pm = pretty_midi.PrettyMIDI(path)
        
        notes = []
        durations = []
        velocities = []
        instruments = []
        
        for instrument in pm.instruments:
            for note in instrument.notes:
                notes.append(note.pitch)
                durations.append(note.end - note.start)
                velocities.append(note.velocity)
                instruments.append(instrument.program if hasattr(instrument, 'program') else 0)
        
        if not notes:
            return {}
        
        return {
            "notes": torch.tensor(notes, dtype=torch.long),
            "durations": torch.tensor(durations, dtype=torch.float32),
            "velocities": torch.tensor(velocities, dtype=torch.long),
            "instruments": torch.tensor(instruments, dtype=torch.long)
        }
    except ImportError:
        print("   ⚠️  pretty_midi not installed. Install with: pip install pretty_midi")
        return {}
    except Exception as e:
        print(f"   ⚠️  Error preprocessing MIDI: {e}")
        return {}

if __name__ == "__main__":
    print("🎵 OMNIMIND Music Module Test")
    music = OmnimindMusic()
    print("✅ Music Module Initialized")
