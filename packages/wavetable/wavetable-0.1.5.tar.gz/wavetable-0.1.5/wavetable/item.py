import base64
import io
from pathlib import Path
from typing import Optional, Union

import numpy as np
import soundfile as sf

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

class AudioItem:
    def __init__(
        self, 
        audio_data: Union[np.ndarray, 'torch.Tensor', str, Path], 
        sr: int, 
        label: str = "gen"
    ):
        """
        Encapsulates audio data for logging.
        
        Args:
            audio_data: Input audio (Tensor, Numpy array, or file path).
            sr: Sampling rate.
            label: Identifier ('gen' or 'gt').
        """
        self.sr = sr
        self.label = label
        self.is_empty = False
        self.is_silent = False
        
        self.audio = self._ingest(audio_data)
        
        # 2. Validation & Cleanup
        if self.audio is not None:
            self._validate_and_fix()
            self._check_silence()
        else:
            self.is_empty = True

    def _ingest(self, data) -> Optional[np.ndarray]:
        """Converts input data to a standard numpy array (C, T) or (T,)."""
        if data is None:
            return None

        # Handle Path/String
        if isinstance(data, (str, Path)):
            if not Path(data).exists():
                raise FileNotFoundError(f"Audio file not found: {data}")
            y, _ = sf.read(data, always_2d=True)
            return y.T  # sf reads as (T, C), we want (C, T) internally or just (T)

        # Handle Torch
        if TORCH_AVAILABLE and isinstance(data, torch.Tensor):
            data = data.detach().cpu().numpy()

        # Handle Numpy
        if isinstance(data, np.ndarray):
            data = data.astype(np.float32)
            # Ensure shape consistency (flatten if mono 2D)
            if data.ndim == 2 and data.shape[0] == 1:
                data = data.flatten()
            elif data.ndim == 2 and data.shape[1] == 1:
                 data = data.flatten()
            return data
            
        raise TypeError(f"Unsupported audio type: {type(data)}")

    def _validate_and_fix(self):
        """Handles NaNs, Infs, and standardizes shape."""
        # Check for invalid values
        if not np.isfinite(self.audio).all():
            # Replace NaN/Inf with 0
            self.audio = np.nan_to_num(self.audio, nan=0.0, posinf=0.0, neginf=0.0)
        
        # Force Mono (Requirement 2.1)
        # If shape is (Channels, Time) and Channels > 1, mix down
        if self.audio.ndim > 1:
            self.audio = np.mean(self.audio, axis=0)

    def _check_silence(self):
        """Detects if audio is pure zeros."""
        if np.max(np.abs(self.audio)) < 1e-7:
            self.is_silent = True
            print("Warning: Audio is silent (all zeros).")

    def normalize(self, target_peak: float = 0.95):
        """Applies peak normalization safely."""
        if self.is_empty or self.is_silent:
            return
            
        peak = np.max(np.abs(self.audio))
        if peak > 0:
            self.audio = (self.audio / peak) * target_peak

    def to_base64(self, format='wav') -> str:
        """Encodes audio to Base64 string for HTML embedding."""
        if self.is_empty or self.is_silent:
            return ""
            
        buffer = io.BytesIO()
        sf.write(buffer, self.audio, self.sr, format=format)
        buffer.seek(0)
        b64_data = base64.b64encode(buffer.read()).decode('utf-8')
        return f"data:audio/{format};base64,{b64_data}"

    def to_file(self, path: Union[str, Path]):
        """Writes audio to disk for Linked mode."""
        if self.is_empty or self.is_silent:
            return
            
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        sf.write(path, self.audio, self.sr)

    def get_duration(self) -> float:
        if self.is_empty or self.audio is None:
            return 0.0
        return len(self.audio) / self.sr