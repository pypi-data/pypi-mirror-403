import base64
from pathlib import Path
from typing import Any, Dict, List, Optional

import jinja2

from .config import AudioLoggerConfig, SpectrogramConfig, WaveformConfig
from .item import AudioItem
from .visualizer import Visualizer

# -----------------------------------------------------------------------------
# JINJA2 TEMPLATES
# -----------------------------------------------------------------------------

JS_SCRIPTS = """
<script>
    function downloadBase64(base64Data, fileName) {
        if (!base64Data || base64Data === "") { alert("No audio data available."); return; }
        
        // Handle data URI prefix if present
        const dataStart = base64Data.indexOf(',') + 1;
        const b64 = base64Data.substring(dataStart);
        const contentType = base64Data.substring(5, dataStart - 8);

        const byteCharacters = atob(b64);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
            byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], {type: contentType});
        
        const link = document.createElement('a');
        link.href = window.URL.createObjectURL(blob);
        link.download = fileName;
        link.click();
        window.URL.revokeObjectURL(link.href);
    }
</script>
"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{{ title }}</title>
    {{ css }}
    {{ js }}
</head>
<body>
    <div class="al-container">
        <h2>{{ title }}</h2>
        <table class="al-table">
            <thead>
                <tr>
                    <th>Row ID</th>
                    {% for col in columns %}
                    <th>{{ col }}</th>
                    {% endfor %}
                </tr>
            </thead>
            <tbody>
                {% for row_id, cells in rows.items() %}
                <tr>
                    <td><strong>{{ row_id }}</strong></td>
                    {% for col in columns %}
                    <td>
                        {% if col in cells %}
                            {{ cells[col] }}
                        {% else %}
                            <span style="color: #ccc;">-</span>
                        {% endif %}
                    </td>
                    {% endfor %}
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</body>
</html>
"""

CELL_TEMPLATE = """
<div class="al-cell">
    {% if meta %}
    <div class="al-meta">{{ meta }}</div>
    {% endif %}

    {% if gen_audio_src %}
    <div>
        <div class="al-controls">
            <span class="al-label">Gen</span>
            <audio controls src="{{ gen_audio_src }}"></audio>
            {% if allow_download %}
                {% if is_embed %}
                <button class="al-btn-dl" onclick="downloadBase64('{{ gen_audio_src }}', '{{ gen_filename }}')">⬇</button>
                {% else %}
                <a href="{{ gen_audio_src }}" download="{{ gen_filename }}" class="al-btn-dl" style="text-decoration:none;">⬇</a>
                {% endif %}
            {% endif %}
        </div>
        {% if gen_spec_src %}
        <div class="al-viz-container"><img src="{{ gen_spec_src }}" class="al-viz-img" title="Spectrogram"></div>
        {% endif %}
        {% if gen_wave_src %}
        <div class="al-viz-container"><img src="{{ gen_wave_src }}" class="al-viz-img" title="Waveform"></div>
        {% endif %}
    </div>
    {% endif %}

    {% if gt_audio_src %}
    <div style="margin-top: 5px; opacity: 0.9;">
        <div class="al-controls" style="background: #fff5f5;">
            <span class="al-label" style="color: #d73a49;">Ref</span>
            <audio controls src="{{ gt_audio_src }}"></audio>
             {% if allow_download %}
                {% if is_embed %}
                <button class="al-btn-dl" onclick="downloadBase64('{{ gt_audio_src }}', '{{ gt_filename }}')">⬇</button>
                {% else %}
                <a href="{{ gt_audio_src }}" download="{{ gt_filename }}" class="al-btn-dl" style="text-decoration:none;">⬇</a>
                {% endif %}
            {% endif %}
        </div>
        
        {% if gt_spec_src %}
        <div class="al-viz-container"><img src="{{ gt_spec_src }}" class="al-viz-img"></div>
        {% endif %}
        
        {% if gt_wave_src %}
        <div class="al-viz-container"><img src="{{ gt_wave_src }}" class="al-viz-img"></div>
        {% endif %}
    </div>
    {% endif %}
</div>
"""

# -----------------------------------------------------------------------------
# BUILDER CLASS
# -----------------------------------------------------------------------------

class HTMLBuilder:
    def __init__(
        self, 
        config: AudioLoggerConfig, 
        spec_config: SpectrogramConfig, 
        wave_config: WaveformConfig
    ):
        self.config = config
        self.spec_config = spec_config
        self.wave_config = wave_config
        
        self.env = jinja2.Environment(loader=jinja2.BaseLoader())
        self.cell_template = self.env.from_string(CELL_TEMPLATE)
        self.page_template = self.env.from_string(HTML_TEMPLATE)

    def _generate_css(self) -> str:
        """Generates CSS based on the current visual configuration."""
        # We determine cell width based on the Spectrogram width (usually the primary visual)
        width = max(self.spec_config.dimensions[0], self.wave_config.dimensions[0])
        
        # Conditional Hover Effect
        hover_css = ""
        if self.config.hover_effect:
            hover_css = ".al-table tbody tr:hover { background-color: #f1f8ff; transition: background-color 0.2s; }"

        return f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600;700&display=swap');

            .al-container {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 20px; }}
            
            /* Table Styling */
            .al-table {{ border-collapse: collapse; width: auto; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }} 
            .al-table th, .al-table td {{ border: 1px solid #e1e4e8; padding: 12px; vertical-align: top; }}
            
            /* Header Styling - Scientific Font */
            .al-table th {{ 
                background-color: #eaecef; 
                text-align: center; 
                font-weight: 600; 
                color: #24292e;
                font-family: 'IBM Plex Sans', 'Inter', 'Roboto', 'Segoe UI', system-ui, sans-serif;
                letter-spacing: 0.02em;
            }}
            
            /* Row Header Styling (First Column) */
            .al-table td:first-child {{ 
                vertical-align: middle; 
                text-align: center; 
                font-weight: bold; 
                background-color: #f6f8fa;
                color: #444;
                font-family: 'IBM Plex Sans', monospace; /* Technical look for IDs */
            }}
            
            /* Zebra Striping */
            .al-table tbody tr:nth-child(even) {{ background-color: #fcfcfc; }}
            
            /* Hover Effect (Conditional) */
            {hover_css}
            
            /* Cell Layout - Centering */
            .al-cell {{ 
                display: flex; 
                flex-direction: column; 
                gap: 6px; 
                width: {width}px; 
                align-items: center; 
                margin: 0 auto; 
            }}
            
            /* Audio Player Styling */
            audio {{ height: 25px; width: 100%; max-width: {width}px; }}
            
            /* Visualization Containers */
            .al-viz-container {{ position: relative; width: 100%; line-height: 0; background: #fff; border: 1px solid #eee; }}
            .al-viz-img {{ width: 100%; height: auto; display: block; }}
            
            /* Controls Row */
            .al-controls {{ display: flex; align-items: center; justify-content: center; gap: 5px; padding: 4px; background: #f1f3f5; border-radius: 4px; width: 100%; box-sizing: border-box; }}
            .al-label {{ font-size: 10px; font-weight: bold; color: #586069; text-transform: uppercase; }}
            .al-meta {{ font-size: 11px; color: #555; margin-bottom: 4px; white-space: pre-wrap; text-align: center; }}
            .al-btn-dl {{ font-size: 10px; padding: 1px 6px; cursor: pointer; border: 1px solid #ccc; background: #fff; border-radius: 3px; }}
        </style>
        """

    def _save_asset(self, buffer, filename: str, subfolder: str = "assets") -> str:
        """
        Saves bytes to disk and returns relative path.
        Used only in 'link' mode.
        """
        base_path = Path(self.config.root_dir)
        full_dir = base_path / subfolder
        full_dir.mkdir(parents=True, exist_ok=True)
        
        full_path = full_dir / filename
        
        if isinstance(buffer, str):
            return ""
            
        with open(full_path, 'wb') as f:
            f.write(buffer.getbuffer())
            
        return f"./{subfolder}/{filename}"

    def _get_b64_img(self, buffer) -> str:
        """Converts BytesIO image buffer to base64 src string."""
        if buffer is None: return ""
        b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return f"data:image/png;base64,{b64}"

    def render_cell(
        self, 
        gen_item: AudioItem, 
        gt_item: Optional[AudioItem],
        meta: Dict[str, Any],
        spec_conf: SpectrogramConfig,
        wave_conf: WaveformConfig,
        cell_id: str
    ) -> str:
        """Renders the HTML for a single cell."""
        context = {
            'meta': str(meta) if meta else None,
            'allow_download': True,
            'is_embed': (self.config.save_mode == 'embed'),
            'gen_filename': f"{cell_id}_gen.wav",
            'gt_filename': f"{cell_id}_gt.wav"
        }
        
        # Calculate shared max duration for spectrogram alignment (in seconds)
        dur_gen = (len(gen_item.audio) / gen_item.sr) if (not gen_item.is_empty and not gen_item.is_silent) else 0.0
        dur_gt = (len(gt_item.audio) / gt_item.sr) if (gt_item and not gt_item.is_empty and not gt_item.is_silent) else 0.0
        max_dur = max(dur_gen, dur_gt) if (dur_gen > 0 or dur_gt > 0) else None

        # --- 1. Process GENERATED Audio ---
        if not gen_item.is_empty and not gen_item.is_silent:
            if self.config.save_mode == 'embed':
                context['gen_audio_src'] = gen_item.to_base64()
            else:
                rel_path = f"./assets/{cell_id}_gen.wav"
                full_path = Path(self.config.root_dir) / "assets" / f"{cell_id}_gen.wav"
                gen_item.to_file(full_path)
                context['gen_audio_src'] = rel_path

            # Visualizations
            wave_buf = Visualizer.generate_waveform(gen_item, wave_conf, gt_item)
            if self.config.save_mode == 'embed':
                context['gen_wave_src'] = self._get_b64_img(wave_buf)
            elif wave_buf:
                context['gen_wave_src'] = self._save_asset(wave_buf, f"{cell_id}_wave.png")

            spec_buf = Visualizer.generate_spectrogram(gen_item, spec_conf, max_duration=max_dur)
            if self.config.save_mode == 'embed':
                context['gen_spec_src'] = self._get_b64_img(spec_buf)
            elif spec_buf:
                context['gen_spec_src'] = self._save_asset(spec_buf, f"{cell_id}_spec.png")

        # --- 2. Process GROUND TRUTH Audio ---
        if gt_item and not gt_item.is_empty and not gt_item.is_silent:
            if self.config.save_mode == 'embed':
                context['gt_audio_src'] = gt_item.to_base64()
            else:
                rel_path = f"./assets/{cell_id}_gt.wav"
                full_path = Path(self.config.root_dir) / "assets" / f"{cell_id}_gt.wav"
                gt_item.to_file(full_path)
                context['gt_audio_src'] = rel_path

            # Spectrogram FIRST (to match Gen layout)
            # Pass max_dur here as well to ensure it scales same as Generated
            spec_buf = Visualizer.generate_spectrogram(gt_item, spec_conf, max_duration=max_dur)
            if self.config.save_mode == 'embed':
                context['gt_spec_src'] = self._get_b64_img(spec_buf)
            elif spec_buf:
                context['gt_spec_src'] = self._save_asset(spec_buf, f"{cell_id}_gt_spec.png")
            
            # Waveform SECOND
            gt_wave_buf = Visualizer.generate_waveform(gt_item, wave_conf, gt_item=None, max_duration=max_dur)
            if self.config.save_mode == 'embed':
                context['gt_wave_src'] = self._get_b64_img(gt_wave_buf)
            elif gt_wave_buf:
                context['gt_wave_src'] = self._save_asset(gt_wave_buf, f"{cell_id}_gt_wave.png")

        return self.cell_template.render(context)

    def build_page(self, title: str, columns: List[str], rows: Dict[str, Dict[str, str]]) -> str:
        """Assembles the final HTML page."""
        return self.page_template.render(
            title=title,
            css=self._generate_css(),
            js=JS_SCRIPTS,
            columns=columns,
            rows=rows
        )
