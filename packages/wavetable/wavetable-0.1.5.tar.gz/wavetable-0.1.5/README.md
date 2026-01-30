# wavetable

<!-- input banner image -->

[![PyPI Version](https://img.shields.io/pypi/v/wavetable)](https://pypi.org/project/wavetable)

<div align="center">
  <img src="wavetable.png" alt="wavetable_banner" width="500px"/>
</div>

 <!-- whitespace here below -->

---

<br>

<!-- line -->

A Python library for generating organized HTML tables of audio samples, waveforms, and spectrograms. wavetable allows you to compare "Generated" vs "Ground Truth" audio directly in your browser or Jupyter Notebook with zero-dependency static HTML output.

## Features

- **Static HTML Output:** Generates self-contained (embedded) or lightweight (linked assets) HTML files.
- **Visualizations:** Automatic Waveform and Spectrogram (STFT or Mel) display.
- **Comparisons:** Native support for displaying reference audio.
- **Customizable:** Control colormaps, frequency scales (Log/Mel/Linear), and magnitude scaling (dB/Linear).

## Installation

```bash
pip install wavetable # if using pip
poetry add wavetable # if using poetry
...
```

## Quick Start

```python
import numpy as np
from wavetable import AudioLogger

logger = AudioLogger(name="my_experiment",
                     sr=44100,
                     root_dir="audio_logs",
                     save_mode="embed" # or "link"
                    )

# Dummy Audio
audio_gen = np.sin(2 * np.pi * 440 * np.linspace(0, 2, 44100*2))
audio_gt  = np.sin(2 * np.pi * 440 * np.linspace(0, 2, 44100*2)) + 0.1

# Log a cell
logger.log(
    row="Epoch_1",
    col="Sample_A",
    audio=audio_gen,
    ground_truth=audio_gt,
    meta="Loss: 0.02"  # Text metadata displayed above the cell
)

# Save to disk (creates audio_logs/my_experiment.html)
save_path = logger.save()

# Optional: Display in Jupyter Notebook
logger.display()
```

Check out `test_notebook.ipynb` for a the visual output or download the example HTML file (`demo.html`).

## Configuration

You can customize the logger by passing a `plot_config` dictionary during initialization. The full configuration options available in the file `wavetable/config.py`.

### 1\. General Settings

| Parameter      | Type | Default        | Description                                                           |
| :------------- | :--- | :------------- | :-------------------------------------------------------------------- |
| `sr`           | int  | 44100          | Global sampling rate.                                                 |
| `save_mode`    | str  | `'embed'`      | `'embed'` (single huge HTML file) or `'link'` (HTML + assets folder). |
| `hover_effect` | bool | `True`         | Highlights the active row on mouse hover.                             |
| `root_dir`     | str  | `'audio_logs'` | Directory where logs are saved.                                       |

### 2\. Spectrogram Configuration

Passed via `plot_config={'spectrogram': {...}}`:

| Parameter          | Options             | Default     | Description                                          |
| :----------------- | :------------------ | :---------- | :--------------------------------------------------- |
| `spectrogram_type` | `'stft'`, `'mel'`   | `'stft'`    | The type of spectrogram to compute.                  |
| `plot_freq_scale`  | `'log'`, `'linear'` | `'log'`     | Y-axis scaling (only used if type is 'stft').        |
| `magnitude_scale`  | `'db'`, `'linear'`  | `'db'`      | Compression of magnitude/power.                      |
| `n_mels`           | int                 | `80`        | Number of Mel bands (only used if type is 'mel').    |
| `cmap`             | str                 | `'inferno'` | Matplotlib colormap name (e.g., 'viridis', 'magma'). |
| `n_fft`            | int                 | `2048`      | FFT window size.                                     |
| `hop_length`       | int                 | `512`       | STFT hop length.                                     |

### 3\. Waveform Configuration

Passed via `plot_config={'waveform': {...}}`:

| Parameter    | Type  | Default     | Description                                                 |
| :----------- | :---- | :---------- | :---------------------------------------------------------- |
| `overlay_gt` | bool  | `False`     | If True, plots Ground Truth signal behind Generated signal. |
| `color_gen`  | str   | `'#007bff'` | Hex color for Generated audio (Blue).                       |
| `color_gt`   | str   | `'#fd7e14'` | Hex color for Ground Truth audio (Orange).                  |
| `ylim`       | tuple | `(-1, 1)`   | Y-axis limits for the waveform plot.                        |

## Advanced Example

```python
logger = AudioLogger(
    name="Mel_Spectrogram_Test",
    sr=22050,
    hover_effect=False, # Disable row highlighting
    plot_config={
        'spectrogram': {
            'spectrogram_type': 'mel',
            'n_mels': 128,
            'magnitude_scale': 'db',
            'cmap': 'magma',
            'dimensions': (300, 80) # W, H in pixels
        },
        'waveform': {
            'overlay_gt': True,     # See Gen and GT on top of each other
            'dimensions': (300, 40)
        }
    }
)
```
