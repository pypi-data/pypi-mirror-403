from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class SpectrogramConfig:
    """Configuration for spectrogram visualization."""
    sr: int = 44100
    n_fft: int = 2048
    hop_length: int = 512
    win_length: Optional[int] = None
    window: str = 'hann'
    cmap: str = 'inferno'
    vmin_db: float = -80.0
    vmax_db: float = 0.0
    show_axis: bool = False
    dimensions: Tuple[int, int] = (200, 30)  # width, height in pixels
    plot_freq_scale: str = 'log'  # 'linear' or 'log'

    spectrogram_type: str = 'stft'  # 'stft' or 'mel'
    magnitude_scale: str = 'db'     # 'db' or 'linear'
    n_mels: int = 80                # Number of Mel bands
    fmin: float = 0.0               # Min frequency for Mel
    fmax: Optional[float] = None    # Max frequency for Mel
    top_db: float = 80.0

@dataclass
class WaveformConfig:
    """Configuration for waveform visualization."""
    color_gen: str = '#007bff'  # Standard blue
    color_gt: str = '#fd7e14'   # Standard orange
    linewidth: float = 0.5
    ylim: Tuple[float, float] = (-1.0, 1.0)
    overlay_gt: bool = False    # If True, plots GT behind Generated
    dimensions: Tuple[int, int] = (200, 20)

@dataclass
class AudioLoggerConfig:
    """Global configuration for the AudioLogger."""
    sr: int = 44100
    save_mode: str = 'embed'  # 'embed' or 'link'
    root_dir: str = 'audio_logs'
    normalize_audio: bool = False  # If True, normalizes audio to 0.95 peak
    hover_effect: bool = True # Controls row hover highlighting