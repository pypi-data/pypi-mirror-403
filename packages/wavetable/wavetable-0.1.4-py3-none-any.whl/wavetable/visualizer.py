import io

import matplotlib

# Force headless backend before importing pyplot
matplotlib.use('Agg')
from typing import Optional, Tuple

import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np

from .config import SpectrogramConfig, WaveformConfig
from .item import AudioItem


class Visualizer:
    """
    Stateless engine for generating plotting buffers from AudioItems.
    """

    @staticmethod
    def _create_figure(dimensions: Tuple[int, int], dpi: int = 100):
        """
        Creates a figure with precise pixel dimensions and no margins.
        """
        w_px, h_px = dimensions
        # Convert pixels to inches
        fig = plt.figure(figsize=(w_px / dpi, h_px / dpi), dpi=dpi)
        # [left, bottom, width, height] in fractions of figure width/height
        # 0,0,1,1 fills the whole image, removing all white borders/axes labels space
        ax = fig.add_axes([0, 0, 1, 1])
        return fig, ax

    @classmethod
    def generate_spectrogram(
        cls, 
        item: AudioItem, 
        config: SpectrogramConfig,
        max_duration: Optional[float] = None
    ) -> Optional[io.BytesIO]:
        """
        Generates a spectrogram image buffer.
        Returns None if audio is empty/silent.
        
        Args:
            max_duration: If provided, sets the x-axis limit to this value (in seconds).
                          Useful for aligning plots of different lengths.
        """
        if item.is_empty or item.is_silent:
            return None

        fig = None
        try:
            fig, ax = cls._create_figure(config.dimensions)
            
            # 1. Prepare Audio
            y = item.audio
            if len(y) < config.n_fft:
                y = np.pad(y, (0, int(config.n_fft - len(y))))

            # 2. Compute Features (STFT or Mel)
            if config.spectrogram_type == 'mel':
                # Compute Mel Spectrogram (Power)
                S = librosa.feature.melspectrogram(
                    y=y, 
                    sr=item.sr, 
                    n_fft=config.n_fft, 
                    hop_length=config.hop_length, 
                    win_length=config.win_length,
                    window=config.window,
                    n_mels=config.n_mels,
                    fmin=config.fmin,
                    fmax=config.fmax
                )
                # Plotting axis mode
                y_axis_mode = 'mel'
            else:
                # Compute STFT (Complex -> Magnitude)
                D = librosa.stft(
                    y, 
                    n_fft=config.n_fft, 
                    hop_length=config.hop_length,
                    win_length=config.win_length,
                    window=config.window
                )
                S = np.abs(D)
                # Plotting axis mode ('log' or 'linear')
                y_axis_mode = config.plot_freq_scale

            # 3. Magnitude Compression (Log/dB vs Linear)
            if config.magnitude_scale == 'db':
                # ref=np.max scales the max value to 0 dB
                S_plot = librosa.power_to_db(S**2 if config.spectrogram_type != 'mel' else S, ref=np.max, top_db=config.top_db)
                vmin = config.vmin_db
                vmax = config.vmax_db
            else:
                S_plot = S
                vmin = None
                vmax = None

            # 4. Plot
            img = librosa.display.specshow(
                S_plot,
                sr=item.sr,
                hop_length=config.hop_length,
                x_axis='time',
                y_axis=y_axis_mode,
                fmin=config.fmin, 
                fmax=config.fmax,
                cmap=config.cmap,
                vmin=vmin,
                vmax=vmax,
                ax=ax
            )

            # 5. Handle Alignment
            if max_duration is not None:
                ax.set_xlim(0, max_duration)

            # 6. Axis visibility
            if not config.show_axis:
                ax.axis('off')
            else:
                fig.clf()
                ax = fig.add_subplot(111)
                librosa.display.specshow(
                    S_plot, sr=item.sr, hop_length=config.hop_length,
                    x_axis='time', y_axis=y_axis_mode,
                    fmin=config.fmin, fmax=config.fmax,
                    cmap=config.cmap, vmin=vmin, vmax=vmax, ax=ax
                )
                if max_duration is not None:
                    ax.set_xlim(0, max_duration)
                plt.tight_layout()

            # 7. Save to buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100)
            buf.seek(0)
            return buf

        except Exception as e:
            print(f"Error generating spectrogram: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            if fig:
                plt.close(fig)

    @classmethod
    def generate_waveform(
        cls, 
        item: AudioItem, 
        config: WaveformConfig,
        gt_item: Optional[AudioItem] = None,
        max_duration: Optional[float] = None
    ) -> Optional[io.BytesIO]:
        """
        Generates a waveform image buffer.
        Supports overlaying a Ground Truth (GT) signal behind the generated signal.
        """
        if item.is_empty and (gt_item is None or gt_item.is_empty):
            return None

        fig = None
        try:
            fig, ax = cls._create_figure(config.dimensions)

            # Helper to plot a single array
            def plot_signal(audio_data, color, linewidth):
                # Downsample for visualization speed if array is massive (>100k samples)
                if len(audio_data) > 100000:
                    step = len(audio_data) // 5000
                    plot_data = audio_data[::step]
                    # Create an x-axis that matches the original scale
                    x_axis = np.arange(len(plot_data)) * step
                    ax.plot(x_axis, plot_data, color=color, linewidth=linewidth)
                else:
                    ax.plot(audio_data, color=color, linewidth=linewidth)

            # Ground Truth (Background)
            if config.overlay_gt and gt_item is not None and not gt_item.is_empty:
                plot_signal(gt_item.audio, config.color_gt, config.linewidth)

            # Generated (Foreground)
            if not item.is_empty and not item.is_silent:
                plot_signal(item.audio, config.color_gen, config.linewidth)

            # Styling
            ax.set_ylim(config.ylim)
            
            # Determine X-Limit
            current_max_samples = max(len(item.audio) if not item.is_empty else 0, 
                                      len(gt_item.audio) if gt_item else 0)
            
            if max_duration is not None:
                # Convert duration to samples (using the primary item's Sample Rate)
                max_samples_from_duration = int(max_duration * item.sr)
                # Ensure we don't accidentally crop if max_duration is slightly smaller due to rounding
                limit = max(current_max_samples, max_samples_from_duration)
                ax.set_xlim(0, limit)
            else:
                ax.set_xlim(0, current_max_samples)
                
            ax.axis('off') # Waveforms are strictly aesthetic in the table view
            
            # Save
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100, transparent=True)
            buf.seek(0)
            return buf

        except Exception as e:
            print(f"Error generating waveform: {e}")
            return None
        finally:
            if fig:
                plt.close(fig)
