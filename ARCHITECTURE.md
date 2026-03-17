# AI Video Editor — Architecture Document

> Designed by CTO | Autonomous App Studio
> Target: CPU-only VPS, 16GB free disk, Python 3.x

---

## 1. Open Source Tool Selection

Each tool was evaluated for: CPU performance, disk footprint, Python integration, and active maintenance.

### Video Editing Engine

| Tool | Recommendation | Rationale |
|------|---------------|-----------|
| **FFmpeg** (system) | **PRIMARY** | Already installed. Gold standard for transcoding, filtering, compositing. Zero additional disk. |
| **MoviePy 2.x** | **SECONDARY** | Pythonic wrapper over FFmpeg. Excellent for programmatic composition, transitions, overlays. ~5MB install. |
| vidgear | Skip | Overkill for our use case (designed for streaming/multi-cam). Adds complexity without benefit. |

**Decision:** FFmpeg as the core engine (direct subprocess calls for performance-critical paths), MoviePy for high-level composition (transitions, picture-in-picture, Ken Burns). This mirrors the existing caption.py approach.

### AI Scene Detection

| Tool | Recommendation | Rationale |
|------|---------------|-----------|
| **PySceneDetect** | **CHOSEN** | Lightweight (~2MB), CPU-friendly, multiple detection modes (content-aware, threshold, adaptive). No ML model needed for basic detection. |
| TransNetV2 | Skip | Requires PyTorch (~2GB). Marginal accuracy gain not worth the disk/RAM cost on CPU. |

**Decision:** PySceneDetect with `ContentDetector` (histogram-based) for fast scene boundary detection. Falls back to `AdaptiveDetector` for tricky content.

### AI Background Removal

| Tool | Recommendation | Rationale |
|------|---------------|-----------|
| **rembg** | **CHOSEN** | Uses u2net ONNX model (~170MB). CPU-friendly via onnxruntime (already installed!). Simple API: `rembg.remove(image)`. |
| backgroundremover | Skip | Wraps the same u2net model but with worse API and fewer options. |

**Decision:** rembg with the `u2net` model (general purpose) and `silueta` model (faster, for real-time previews). ONNX runtime is already in the venv.

### AI Upscaling

| Tool | Recommendation | Rationale |
|------|---------------|-----------|
| **Real-ESRGAN (ncnn)** | **CHOSEN** | The `realesrgan-ncnn-vulkan` binary runs on CPU via ncnn (no PyTorch). ~15MB binary + ~10MB models. 2x upscale is practical on CPU. |
| waifu2x | Skip | Anime-focused. Less general-purpose. |
| Pillow LANCZOS | **FALLBACK** | Built-in, zero-cost. Good enough for mild upscaling (1.5x). |

**Decision:** Real-ESRGAN ncnn for quality upscaling (when time permits), Pillow LANCZOS as fast fallback. Only 2x upscale — 4x is too slow on CPU.

### AI Music & Audio

| Tool | Recommendation | Rationale |
|------|---------------|-----------|
| **Demucs (htdemucs)** | **CHOSEN for separation** | Audio source separation (vocals, drums, bass, other). The `htdemucs` model is ~80MB. CPU inference is slow but viable for short clips. |
| audiocraft / MusicGen | Skip | Requires PyTorch (~2GB) + large models (~3.3GB). Too heavy for CPU-only VPS. |
| **FFmpeg audio filters** | **CHOSEN for mixing** | Audio ducking, normalization, EQ, fade — all built into FFmpeg. Zero additional cost. |

**Decision:** Demucs for audio separation (isolate vocals for better captioning, remove/replace background music). FFmpeg filters for all mixing, ducking, normalization. Skip AI music generation — use royalty-free audio library instead.

### Text-to-Speech

| Tool | Recommendation | Rationale |
|------|---------------|-----------|
| **pyttsx3** | **CHOSEN (fast/offline)** | Zero-download, uses system TTS (espeak). Good for quick voiceovers. ~1MB. |
| **Coqui TTS** | **CHOSEN (quality)** | XTTS v2 model for natural speech. ~500MB model. CPU inference ~2-5x real-time. Worth it for branded voiceovers. |
| Bark | Skip | 5GB+ models, very slow on CPU. Quality doesn't justify the cost. |

**Decision:** pyttsx3 for draft/preview TTS, Coqui TTS for production voiceovers. Lazy-load Coqui models only when needed.

### Auto-Editing

| Tool | Recommendation | Rationale |
|------|---------------|-----------|
| **auto-editor** | **CHOSEN** | Already installed! Silence detection, motion detection, audio-based cuts. Battle-tested. |
| **FFmpeg filters** | **CHOSEN (complement)** | `silencedetect`, `loudnorm`, `astats` for audio analysis. `mpdecimate` for duplicate frame detection. |

**Decision:** auto-editor for smart silence/dead-air removal. FFmpeg filters for fine-grained audio analysis and normalization.

### Effects & Compositing

| Tool | Recommendation | Rationale |
|------|---------------|-----------|
| **MoviePy** | **CHOSEN** | Transitions (crossfade, slide), compositing (PiP, split screen), Ken Burns (zoom/pan on stills). |
| **Pillow** | **CHOSEN** | Image overlays, logo compositing, thumbnail generation, text rendering for branded assets. |
| **FFmpeg filters** | **CHOSEN** | Hardware-accelerated: blur, vignette, color grading (LUT), shake, zoom. |

**Decision:** Three-tier approach — FFmpeg for filter-chain effects, MoviePy for timeline composition, Pillow for static asset generation.

### Template System

| Tool | Recommendation | Rationale |
|------|---------------|-----------|
| **Jinja2** | **CHOSEN** | Already installed. Template branded intros/outros as HTML/SVG → render to images → composite with MoviePy. Also powers preset config files. |

### Disk Budget Summary

| Component | Estimated Size |
|-----------|---------------|
| MoviePy 2.x | ~5MB |
| PySceneDetect | ~2MB |
| rembg + u2net model | ~180MB |
| Real-ESRGAN ncnn | ~25MB |
| Demucs (htdemucs) | ~100MB |
| pyttsx3 | ~1MB |
| Coqui TTS + model | ~500MB |
| Pillow | ~5MB |
| **Total new deps** | **~820MB** |
| Existing (whisper, auto-editor, etc.) | ~400MB |
| **Grand total** | **~1.2GB** |

Leaves ~14.8GB free for video processing temp files. Comfortable margin.

---

## 2. Modular Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         PIPELINE ORCHESTRATOR                       │
│                       (editor.py / api / web)                       │
└─────────┬───────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  PREPROCESSOR   │────▶│   AI ANALYZER    │────▶│  EDIT PIPELINE  │
│                 │     │                  │     │                 │
│ • Format detect │     │ • Scene detect   │     │ • Smart cuts    │
│ • Normalize res │     │ • Speech-to-text │     │ • Speed ramp    │
│ • Audio extract │     │ • Energy analysis│     │ • Transitions   │
│ • Trim silence  │     │ • Face detection │     │ • PiP/split     │
│ • Aspect ratio  │     │ • Content class  │     │ • Audio ducking │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                                                          ▼
                        ┌──────────────────┐     ┌─────────────────┐
                        │    EXPORTER      │◀────│  POST-PROCESS   │
                        │                  │     │                 │
                        │ • Format presets │     │ • Captions burn │
                        │ • Quality levels │     │ • Branding      │
                        │ • Thumbnails     │     │ • Color grade   │
                        │ • SRT/VTT export │     │ • Effects       │
                        │ • Metadata       │     │ • Logo/watermark│
                        └──────────────────┘     └─────────────────┘
```

### Module Specifications

Each module is a standalone Python file that can be imported and used independently.

#### `preprocessor.py`

```python
class Preprocessor:
    def analyze(video_path: str) -> VideoInfo
        # Returns: resolution, fps, duration, codec, has_audio, aspect_ratio

    def normalize(video_path: str, target_fps=30, target_codec="h264") -> str
        # Normalizes format. Returns path to normalized video.

    def extract_audio(video_path: str, format="wav") -> str
        # Extracts audio track. Returns path to audio file.

    def crop_aspect(video_path: str, ratio="9:16", method="center") -> str
        # Smart crop with face-detection bias when available.

    def trim_silence(video_path: str, margin=0.2) -> str
        # Wraps auto-editor. Returns trimmed video path.
```

#### `ai_analyzer.py`

```python
class AIAnalyzer:
    def detect_scenes(video_path: str) -> list[Scene]
        # PySceneDetect. Returns: [{start, end, type}]

    def transcribe(video_path: str, model="base") -> Transcription
        # faster-whisper. Returns word-level timestamps + language.

    def analyze_energy(audio_path: str) -> list[EnergySegment]
        # FFmpeg loudness analysis. Returns: [{start, end, level, is_highlight}]

    def detect_faces(video_path: str, sample_rate=1) -> list[FaceRegion]
        # OpenCV Haar cascades (built into cv2, ~5MB). For smart cropping.

    def classify_content(video_path: str, scenes: list) -> list[ContentType]
        # Heuristic: motion level + face presence + audio → talking_head|broll|screenrec|static
```

#### `editor.py` (Core Edit Engine)

```python
class Editor:
    def auto_cut(video_path: str, transcript: Transcription) -> EditList
        # Remove dead air, ums, long pauses. Returns cut points.

    def speed_ramp(video_path: str, energy: list[EnergySegment]) -> str
        # Slow-mo highlights (0.5x), speed up low-energy (1.5-2x).

    def add_transitions(clips: list[str], style="crossfade", duration=0.5) -> str
        # MoviePy: crossfade, zoom, slide, wipe between clips.

    def picture_in_picture(base: str, overlay: str, position="bottom-right") -> str
        # Composite overlay on base video.

    def split_screen(videos: list[str], layout="side-by-side") -> str
        # 2-up or 3-up split screen composition.

    def ken_burns(image_path: str, duration=5, zoom=(1.0, 1.3)) -> str
        # Animate still image with slow zoom/pan.

    def duck_audio(video_path: str, music_path: str, duck_level=-12) -> str
        # Lower music during speech segments.

    def normalize_audio(video_path: str, target_lufs=-16) -> str
        # FFmpeg loudnorm filter.
```

#### `branding.py`

```python
class Branding:
    def add_watermark(video: str, logo: str, position="bottom-right", opacity=0.7) -> str
    def generate_intro(preset: Preset, duration=3) -> str
        # Renders branded intro from Jinja2 template → image sequence → video.
    def generate_outro(preset: Preset, duration=4) -> str
    def add_lower_third(video: str, text: str, preset: Preset) -> str
    def add_cta(video: str, text: str, preset: Preset, position="bottom") -> str
    def color_grade(video: str, preset: Preset) -> str
        # FFmpeg LUT or colorbalance/curves filters per brand.
```

#### `captions.py` (Extends existing caption.py)

```python
class Captions:
    # Preserves ALL existing caption.py functionality

    def generate(video: str, style="tiktok", model="base") -> CaptionResult
        # Styles: tiktok, instagram, youtube, minimal, bold, karaoke
    def word_highlight(captions, style="yellow") -> str  # existing ASS logic
    def emoji_insert(captions, transcript) -> list       # contextual emoji
    def multi_language(captions, target_lang) -> list     # translation stub
    def export_srt(captions, path) -> str
    def export_vtt(captions, path) -> str
    def export_ass(captions, path, style) -> str
```

#### `effects.py`

```python
class Effects:
    def zoom_pulse(video: str, beats: list[float], intensity=1.1) -> str
        # FFmpeg zoompan synced to audio beats.
    def shake(video: str, segments: list, intensity="medium") -> str
    def blur_background(video: str, face_regions: list) -> str
        # Blur everything outside face region.
    def vignette(video: str, intensity=0.3) -> str
    def glitch(video: str, timestamps: list, duration=0.3) -> str
    def particles(video: str, type="sparkle", opacity=0.5) -> str
        # Pre-rendered particle overlay composited via MoviePy.
```

#### `exporter.py`

```python
class Exporter:
    PRESETS = {
        "tiktok":    {"width": 1080, "height": 1920, "fps": 30, "codec": "h264"},
        "instagram": {"width": 1080, "height": 1350, "fps": 30, "codec": "h264"},  # 4:5
        "ig_reel":   {"width": 1080, "height": 1920, "fps": 30, "codec": "h264"},
        "ig_square": {"width": 1080, "height": 1080, "fps": 30, "codec": "h264"},
        "youtube":   {"width": 1920, "height": 1080, "fps": 30, "codec": "h264"},
        "yt_short":  {"width": 1080, "height": 1920, "fps": 30, "codec": "h264"},
    }

    QUALITY = {
        "draft":    {"crf": 28, "preset": "ultrafast"},
        "standard": {"crf": 23, "preset": "fast"},
        "high":     {"crf": 18, "preset": "slow"},
    }

    def export(video: str, format="tiktok", quality="standard") -> str
    def generate_thumbnail(video: str, timestamp="best") -> str
        # "best" = highest contrast/sharpness frame via FFmpeg.
    def export_subtitles(captions, format="srt") -> str
    def inject_metadata(video: str, title, description, tags) -> str
```

#### `presets.py`

```python
@dataclass
class Preset:
    name: str
    colors: dict          # primary, secondary, background, text, accent
    fonts: dict           # heading_font, body_font, caption_font
    caption_style: str    # tiktok, minimal, bold, karaoke
    transitions: str      # crossfade, zoom, slide, cut
    intro_template: str   # Jinja2 template name
    outro_template: str
    cta_text: str
    cta_position: str
    aspect_ratio: str     # 9:16, 16:9, 1:1, 4:5
    color_grade: dict     # brightness, contrast, saturation, temperature adjustments
    logo_path: str | None
    music_path: str | None

# See Section 4 for preset definitions
```

### Data Flow Contracts

Modules communicate via simple Python dataclasses:

```python
@dataclass
class VideoInfo:
    path: str
    width: int
    height: int
    fps: float
    duration: float
    has_audio: bool
    codec: str

@dataclass
class Scene:
    start: float
    end: float
    type: str  # "cut", "fade", "dissolve"

@dataclass
class Transcription:
    language: str
    duration: float
    segments: list[CaptionSegment]

@dataclass
class CaptionSegment:
    start: float
    end: float
    text: str
    words: list[WordTimestamp]

@dataclass
class EditList:
    cuts: list[tuple[float, float]]  # (start, end) of segments to KEEP
    speed_map: list[tuple[float, float, float]]  # (start, end, speed_factor)
```

---

## 3. Interface Design

### CLI Interface (`editor.py`)

The main entry point. Backwards-compatible with existing caption.py usage.

```bash
# Basic preset processing
python editor.py input.mp4 --preset park-it-ad --output output/

# Full auto-edit pipeline
python editor.py input.mp4 --auto-edit --trim-silence --add-music background.mp3

# Smart crop + highlight reel
python editor.py input.mp4 --smart-crop vertical --highlight-reel --duration 30

# Caption-only mode (backwards compat with caption.py)
python editor.py input.mp4 --captions-only --caption-style tiktok

# Advanced composition
python editor.py input.mp4 --preset tiktok-viral --no-captions --speed-ramp --transitions zoom

# Batch processing
python editor.py input/*.mp4 --preset park-it-ad --output output/
```

**CLI argument groups:**

```
Input:
  video                  Input video file(s) or glob pattern
  --output DIR           Output directory (default: output/)

Presets:
  --preset NAME          Apply named preset (park-it-ad, surve-ad, nutrio-ad,
                         tiktok-viral, youtube-short, instagram-reel)

Processing:
  --auto-edit            Smart auto-cut (remove dead air, ums, pauses)
  --trim-silence         Remove silent sections
  --speed-ramp           Auto speed ramp (slow-mo highlights, speed up boring)
  --smart-crop RATIO     Smart crop to ratio (vertical/9:16, square/1:1, 4:5)
  --highlight-reel       Generate highlight reel from best moments
  --duration SECS        Target duration for highlight reel

Captions:
  --captions-only        Only add captions (skip other processing)
  --caption-style STYLE  tiktok, instagram, youtube, minimal, bold, karaoke
  --no-captions          Skip captions entirely
  --model SIZE           Whisper model: tiny, base, small, medium

Branding:
  --title TEXT           Title overlay at start
  --endcard TEXT         End card text
  --logo PATH            Logo/watermark image
  --cta TEXT             Call-to-action overlay text

Audio:
  --add-music PATH       Add background music with auto-ducking
  --normalize-audio      Normalize audio levels (target: -16 LUFS)
  --tts TEXT             Generate TTS voiceover

Effects:
  --transitions STYLE    crossfade, zoom, slide, cut (default from preset)
  --color-grade PRESET   Apply color grading from preset or custom LUT

Export:
  --format FORMAT        tiktok, instagram, ig_reel, ig_square, youtube, yt_short
  --quality LEVEL        draft, standard, high
  --thumbnail            Also generate thumbnail image
```

### REST API (`api.py`)

Flask-based API server (extends existing web.py Flask app).

```
POST /api/process
Content-Type: application/json

{
  "input": "path/to/video.mp4",
  "preset": "park-it-ad",
  "options": {
    "auto_edit": true,
    "trim_silence": true,
    "captions": true,
    "caption_style": "tiktok",
    "smart_crop": "vertical",
    "add_music": "path/to/music.mp3",
    "normalize_audio": true,
    "output_format": "tiktok",
    "quality": "standard",
    "title": "Find Parking Fast",
    "endcard": "Download Park-It",
    "logo": "assets/park-it-logo.png",
    "cta": "Available on App Store"
  }
}

Response: 202 Accepted
{
  "job_id": "abc123",
  "status": "processing",
  "status_url": "/api/jobs/abc123"
}
```

```
GET /api/jobs/{job_id}
Response: 200
{
  "job_id": "abc123",
  "status": "complete",       // processing | complete | failed
  "progress": 100,
  "output": "/api/download/abc123/output.mp4",
  "thumbnail": "/api/download/abc123/thumbnail.jpg",
  "subtitles": "/api/download/abc123/captions.srt",
  "metadata": {
    "duration": 32.5,
    "resolution": "1080x1920",
    "captions_count": 24,
    "file_size_mb": 12.3
  }
}
```

```
GET /api/presets
Response: 200
{
  "presets": [
    {"name": "park-it-ad", "description": "Park-It brand preset", ...},
    ...
  ]
}
```

```
POST /api/upload
Content-Type: multipart/form-data
# Upload video file, returns input path for use with /api/process
```

**Implementation:** Jobs run in a background thread with progress tracking. Job state stored in a simple SQLite database (or in-memory dict for v1).

### Web UI (Enhanced `web.py`)

Extends the existing Flask web UI:

1. **Upload page** — drag-and-drop video upload (existing, keep as-is)
2. **Preset selector** — visual cards for each preset with preview thumbnails
3. **Settings panel** — toggle: auto-edit, captions, crop, effects, music
4. **Scene preview** — after upload, show detected scenes as thumbnail strip
5. **Progress bar** — real-time progress via polling `/api/jobs/{id}`
6. **Download page** — download video + thumbnail + subtitles
7. **History** — list of previously processed videos with re-download

The web UI remains a single-file Flask app (web.py) with inline HTML templates for simplicity. No frontend build step required.

---

## 4. App Preset Definitions

### Park-It Preset (`park-it-ad`)

```yaml
name: park-it-ad
description: "Monochrome, clean, Uber-style parking app"
colors:
  primary: "#111827"      # Near-black
  secondary: "#F9FAFB"    # Near-white
  accent: "#3B82F6"       # Blue for CTAs
  background: "#111827"
  text: "#F9FAFB"
caption_style: minimal     # Clean white text, subtle shadow
fonts:
  heading: "DejaVu Sans Bold"
  body: "DejaVu Sans"
  caption: "DejaVu Sans Bold"
transitions: crossfade
intro_template: "park-it-intro.html"
  # Animated: dark bg → "Park-It" fades in → tagline slides up
outro_template: "park-it-outro.html"
  # App store badges + "Find Parking Fast" + QR code placeholder
cta_text: "Find Parking Fast"
cta_position: bottom
aspect_ratio: "9:16"
color_grade:
  saturation: 0.3          # Desaturated, near-monochrome
  contrast: 1.1
  brightness: 1.0
  temperature: -5           # Slightly cool
logo_path: "assets/park-it-logo.png"
music_path: null            # Clean/minimal, no music by default
```

### Surve Preset (`surve-ad`)

```yaml
name: surve-ad
description: "Colorful, friendly survey app"
colors:
  primary: "#7C3AED"       # Purple
  secondary: "#FCD34D"     # Yellow
  accent: "#EC4899"        # Pink
  background: "#1E1B4B"    # Deep indigo
  text: "#FFFFFF"
caption_style: tiktok       # Bold, word-by-word highlight in yellow
fonts:
  heading: "DejaVu Sans Bold"
  body: "DejaVu Sans"
  caption: "DejaVu Sans Bold"
transitions: slide
intro_template: "surve-intro.html"
  # Colorful gradient bg → survey icons animate in → "Surve" bounces in
outro_template: "surve-outro.html"
  # "Quick Surveys" + "Earn Rewards" + app badge
cta_text: "Quick Surveys"
cta_position: bottom
aspect_ratio: "9:16"
color_grade:
  saturation: 1.3           # Vibrant, punchy colors
  contrast: 1.05
  brightness: 1.05
  temperature: 5            # Slightly warm
logo_path: "assets/surve-logo.png"
music_path: "assets/surve-upbeat.mp3"   # Upbeat, friendly
```

### Nutrio+ Preset (`nutrio-ad`)

```yaml
name: nutrio-ad
description: "Health/fitness nutrition app"
colors:
  primary: "#065F46"       # Dark green
  secondary: "#D1FAE5"     # Light mint
  accent: "#F59E0B"        # Amber/gold
  background: "#064E3B"    # Forest green
  text: "#ECFDF5"
caption_style: bold          # Large, clean, white with green outline
fonts:
  heading: "DejaVu Sans Bold"
  body: "DejaVu Sans"
  caption: "DejaVu Sans Bold"
transitions: crossfade
intro_template: "nutrio-intro.html"
  # Green gradient → leaf/health icon → "Nutrio+" → "Eat Smart"
outro_template: "nutrio-outro.html"
  # Meal prep montage bg → "Eat Smart" + "Track Nutrition" + app badge
cta_text: "Eat Smart"
cta_position: bottom
aspect_ratio: "9:16"
color_grade:
  saturation: 1.1
  contrast: 1.0
  brightness: 1.05
  temperature: 3             # Slightly warm (food looks better warm)
logo_path: "assets/nutrio-logo.png"
music_path: "assets/nutrio-chill.mp3"   # Chill, wellness vibe
```

### Social Media Presets

```yaml
tiktok-viral:
  caption_style: tiktok     # Word-by-word yellow highlight
  transitions: zoom          # Fast zooms between cuts
  auto_edit: true            # Aggressive cuts, no dead air
  speed_ramp: true           # Slow-mo → speed-up pattern
  aspect_ratio: "9:16"
  color_grade: {saturation: 1.2, contrast: 1.15}

youtube-short:
  caption_style: youtube     # Clean, centered, white with shadow
  transitions: crossfade
  auto_edit: true
  aspect_ratio: "9:16"
  color_grade: {saturation: 1.0, contrast: 1.05}
  # Includes subscribe CTA end card

instagram-reel:
  caption_style: instagram   # Sleek, minimal, bottom-aligned
  transitions: slide
  auto_edit: true
  aspect_ratio: "9:16"
  color_grade: {saturation: 1.15, contrast: 1.1, temperature: 3}
  # Includes swipe-up CTA
```

---

## 5. Directory Structure

```
/root/projects/video-tool/
├── ARCHITECTURE.md          # This document
├── CLAUDE.md                # Dev instructions
├── editor.py                # NEW — Main CLI entry point & pipeline orchestrator
├── caption.py               # EXISTING — Kept as-is, imported by captions.py
├── web.py                   # EXISTING — Enhanced with preset selector & progress
├── api.py                   # NEW — REST API server
├── modules/
│   ├── __init__.py
│   ├── preprocessor.py      # Format detection, normalization, crop, trim
│   ├── ai_analyzer.py       # Scene detection, transcription, energy, faces
│   ├── editor_engine.py     # Smart cuts, speed ramp, transitions, PiP, audio
│   ├── branding.py          # Watermarks, intros, outros, lower thirds, CTAs
│   ├── captions.py          # Caption generation (wraps existing caption.py)
│   ├── effects.py           # Visual effects: zoom, shake, blur, vignette, glitch
│   ├── exporter.py          # Export presets, quality, thumbnails, metadata
│   └── presets.py           # Preset definitions and loader
├── templates/
│   ├── park-it-intro.html   # Jinja2 branded intro templates
│   ├── park-it-outro.html
│   ├── surve-intro.html
│   ├── surve-outro.html
│   ├── nutrio-intro.html
│   └── nutrio-outro.html
├── assets/
│   ├── park-it-logo.png
│   ├── surve-logo.png
│   ├── nutrio-logo.png
│   └── fonts/               # Any custom fonts
├── input/                   # EXISTING — Upload directory
├── output/                  # EXISTING — Output directory
├── venv/                    # EXISTING — Python virtual environment
└── requirements.txt         # NEW — All dependencies
```

---

## 6. Dependency Installation Plan

```bash
# Activate venv
source /root/projects/video-tool/venv/bin/activate

# Core editing
pip install moviepy pillow

# AI analysis
pip install scenedetect[opencv]    # PySceneDetect + OpenCV
pip install rembg onnxruntime      # Background removal (onnxruntime already installed)

# Audio
pip install demucs                 # Audio separation
pip install pyttsx3                # Basic TTS

# TTS (optional, install on demand due to size)
# pip install TTS                  # Coqui TTS — ~500MB, install only when needed

# Already installed (no action needed):
# faster-whisper, auto-editor, flask, jinja2, onnxruntime
```

---

## 7. Implementation Priority

The Fullstack Developer should implement in this order:

1. **`preprocessor.py`** + **`exporter.py`** — Foundation: get video in, get video out
2. **`captions.py`** — Wrap existing caption.py, add new styles
3. **`ai_analyzer.py`** — Scene detection + energy analysis
4. **`editor_engine.py`** — Auto-cut, speed ramp, transitions
5. **`branding.py`** + **`presets.py`** — Brand presets and overlays
6. **`effects.py`** — Visual effects layer
7. **`editor.py`** (CLI) — Wire everything together
8. **`api.py`** — REST API with job queue
9. **`web.py`** enhancements — Preset selector, progress bar, history

Each module should have a simple `if __name__ == "__main__"` test block for standalone testing.

---

## 8. Performance Considerations

- **Temp files:** Use `/tmp` for intermediate files. Clean up after each pipeline stage.
- **Streaming:** Use FFmpeg pipe mode where possible to avoid writing intermediate files.
- **Lazy loading:** Only import heavy modules (rembg, demucs, coqui) when their features are requested.
- **Model caching:** Download AI models to `~/.cache/` (default for huggingface_hub). First run will be slow.
- **Parallel processing:** Audio analysis and video analysis can run concurrently (use `concurrent.futures.ThreadPoolExecutor`).
- **Progress reporting:** Each module reports progress to a callback function. The API/web UI polls for progress.
- **Memory:** Keep MoviePy clip references minimal. Close/delete clips after each operation to prevent RAM accumulation.
- **CPU targets:** A 60-second video should process in under 5 minutes for `standard` quality with full pipeline.
