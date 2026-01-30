import os
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

try:
    from IPython.display import HTML
    from IPython.display import display as ipy_display
    IPYTHON_AVAILABLE = True
except ImportError:
    IPYTHON_AVAILABLE = False

# Local imports
from .builder import HTMLBuilder
from .config import AudioLoggerConfig, SpectrogramConfig, WaveformConfig
from .item import AudioItem


class AudioLogger:
    def __init__(
        self, 
        name: str = "audio_log",
        sr: int = 44100,
        root_dir: str = "audio_logs",
        save_mode: str = "embed",
        plot_config: Optional[Dict[str, Any]] = None,
        hover_effect: bool = True
    ):
        """
        Main entry point for logging audio.
        
        Args:
            name: Name of the logger (files will be saved as {name}.html).
            sr: Sampling rate.
            root_dir: Directory where HTML and assets will be saved.
            save_mode: 'embed' (single file) or 'link' (lightweight + assets folder).
            plot_config: Dictionary to override default Spectrogram/Waveform configs.
            hover_effect: If True, enables row highlighting on mouse hover.
        """
        self.name = name
        
        # Setup Configuration
        self.config = AudioLoggerConfig(
            sr=sr, 
            # root_dir=os.path.join(root_dir, name), 
            root_dir=root_dir,
            save_mode=save_mode,
            hover_effect=hover_effect
        )
        
        # Apply overrides to visualization configs
        self.spec_config = SpectrogramConfig(sr=sr)
        self.wave_config = WaveformConfig()
        
        if plot_config:
            if 'spectrogram' in plot_config:
                for k, v in plot_config['spectrogram'].items():
                    setattr(self.spec_config, k, v)
            if 'waveform' in plot_config:
                for k, v in plot_config['waveform'].items():
                    setattr(self.wave_config, k, v)

        # Initialize Components
        # Pass the specialized configs to builder for dynamic CSS generation
        self.builder = HTMLBuilder(self.config, self.spec_config, self.wave_config)
        
        # State Management
        # We use a DataFrame to store the RENDERED HTML strings of the cells.
        # Index = Rows, Columns = Columns.
        self.df = pd.DataFrame()

    def log(
        self, 
        row: str, 
        col: str, 
        audio: Any, 
        ground_truth: Any = None, 
        meta: Optional[Dict[str, Any]] = None
    ):
        """
        Logs a single audio cell. 
        Processes audio immediately to release memory.
        """
        # Create unique ID for asset naming (used in linked mode)
        cell_id = f"r{row}_c{col}".replace(" ", "_").replace("/", "_")
        
        # Process Data
        item_gen = AudioItem(audio, self.config.sr, label="gen")
        item_gt = AudioItem(ground_truth, self.config.sr, label="gt") if ground_truth is not None else None

        # Apply global normalization if requested
        if self.config.normalize_audio:
            item_gen.normalize()
            if item_gt: 
                item_gt.normalize()

        # Render HTML (Eager evaluation)
        html_content = self.builder.render_cell(
            gen_item=item_gen,
            gt_item=item_gt,
            meta=meta,
            spec_conf=self.spec_config,
            wave_conf=self.wave_config,
            cell_id=cell_id
        )

        # Update State
        # Ensure column exists
        if col not in self.df.columns:
            self.df[col] = "" # Initialize new column with empty strings
        
        # Ensure row exists
        if row not in self.df.index:
            self.df.loc[row] = "" # Initialize new row (old)
            # self.df[col] = pd.Series([""] * len(self.df), index=self.df.index, dtype='object')  # Initialize new row with empty strings for all columns
        # self.df.at[row, col] = html_content
        self.df = self.df.copy()
        self.df.at[row, col] = html_content

    def log_row(self, row: str, data: Dict[str, Any], ground_truth: Dict[str, Any] = None):
        """
        Log a batch of columns for a specific row.
        data: { 'col_name': audio_data, ... }
        """
        for col, audio in data.items():
            gt = ground_truth.get(col) if ground_truth else None
            self.log(row, col, audio, ground_truth=gt)

    def save(self):
        """
        Compiles the DataFrame into an HTML file and writes to disk.
        """
        # Convert DataFrame to nested dictionary for Jinja: {row: {col: html}}
        # We fill NaNs with empty strings
        data_dict = self.df.fillna("").to_dict(orient='index')
        
        # Build Page
        full_html = self.builder.build_page(
            title=self.name,
            columns=self.df.columns.tolist(),
            rows=data_dict
        )
        
        # Ensure dir exists
        Path(self.config.root_dir).parent.mkdir(parents=True, exist_ok=True)
        if not os.path.exists(self.config.root_dir):
             os.makedirs(self.config.root_dir, exist_ok=True)

        # Write
        file_path = os.path.join(self.config.root_dir, f"{self.name}.html")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(full_html)
            
        return file_path

    def display(self):
        """
        Displays the table in a Jupyter Notebook.
        """
        if not IPYTHON_AVAILABLE:
            print("IPython not available. Call .save() to view the table.")
            return
            
        # We simply save and reload the HTML to ensure consistent rendering
        # or we could render directly. Let's render directly to avoid file I/O in memory.
        data_dict = self.df.fillna("").to_dict(orient='index')
        full_html = self.builder.build_page(
            title=self.name,
            columns=self.df.columns.tolist(),
            rows=data_dict
        )
        
        # Wrap in a scrollable div for notebook convenience
        wrapped_html = f"""
        <div style="max-height: 800px; overflow-y: auto; border: 1px solid #ddd;">
            {full_html}
        </div>
        """
        ipy_display(HTML(wrapped_html))

    def merge(self, other: 'AudioLogger'):
        """
        Merges another AudioLogger into this one.
        Overwrites cells if they exist in both.
        """
        if not isinstance(other, AudioLogger):
            raise ValueError("Can only merge with another AudioLogger instance.")
            
        # Pandas combine_first or update. 
        # We use combine_first to prioritize 'self' data, or update to prioritize 'other'.
        # Usually logging implies appending.
        
        # Align schemas
        self.df = self.df.combine_first(other.df)