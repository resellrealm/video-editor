"""Presets module — brand presets and social media presets for the video editor."""

from dataclasses import dataclass, field
from pathlib import Path

ASSETS_DIR = Path(__file__).parent.parent / "assets"
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


@dataclass
class Preset:
    name: str
    description: str = ""
    colors: dict = field(default_factory=dict)
    fonts: dict = field(default_factory=dict)
    caption_style: str = "tiktok"
    transitions: str = "crossfade"
    intro_template: str = ""
    outro_template: str = ""
    cta_text: str = ""
    cta_position: str = "bottom"
    aspect_ratio: str = "9:16"
    color_grade: dict = field(default_factory=dict)
    logo_path: str | None = None
    music_path: str | None = None
    auto_edit: bool = False
    speed_ramp: bool = False
    trim_silence: bool = False


# ─── Brand Presets ────────────────────────────────────────

PARK_IT_AD = Preset(
    name="park-it-ad",
    description="Monochrome, clean, Uber-style parking app",
    colors={
        "primary": "#111827",
        "secondary": "#F9FAFB",
        "accent": "#3B82F6",
        "background": "#111827",
        "text": "#F9FAFB",
    },
    fonts={
        "heading": "DejaVu Sans Bold",
        "body": "DejaVu Sans",
        "caption": "DejaVu Sans Bold",
    },
    caption_style="minimal",
    transitions="crossfade",
    intro_template="park-it-intro.html",
    outro_template="park-it-outro.html",
    cta_text="Find Parking Fast",
    cta_position="bottom",
    aspect_ratio="9:16",
    color_grade={
        "saturation": 0.3,
        "contrast": 1.1,
        "brightness": 1.0,
        "temperature": -5,
    },
    logo_path=str(ASSETS_DIR / "park-it-logo.png"),
    music_path=None,
)

SURVE_AD = Preset(
    name="surve-ad",
    description="Colorful, friendly survey app",
    colors={
        "primary": "#7C3AED",
        "secondary": "#FCD34D",
        "accent": "#EC4899",
        "background": "#1E1B4B",
        "text": "#FFFFFF",
    },
    fonts={
        "heading": "DejaVu Sans Bold",
        "body": "DejaVu Sans",
        "caption": "DejaVu Sans Bold",
    },
    caption_style="tiktok",
    transitions="slide",
    intro_template="surve-intro.html",
    outro_template="surve-outro.html",
    cta_text="Quick Surveys",
    cta_position="bottom",
    aspect_ratio="9:16",
    color_grade={
        "saturation": 1.3,
        "contrast": 1.05,
        "brightness": 1.05,
        "temperature": 5,
    },
    logo_path=str(ASSETS_DIR / "surve-logo.png"),
    music_path=str(ASSETS_DIR / "surve-upbeat.mp3"),
)

NUTRIO_AD = Preset(
    name="nutrio-ad",
    description="Health/fitness nutrition app",
    colors={
        "primary": "#065F46",
        "secondary": "#D1FAE5",
        "accent": "#F59E0B",
        "background": "#064E3B",
        "text": "#ECFDF5",
    },
    fonts={
        "heading": "DejaVu Sans Bold",
        "body": "DejaVu Sans",
        "caption": "DejaVu Sans Bold",
    },
    caption_style="bold",
    transitions="crossfade",
    intro_template="nutrio-intro.html",
    outro_template="nutrio-outro.html",
    cta_text="Eat Smart",
    cta_position="bottom",
    aspect_ratio="9:16",
    color_grade={
        "saturation": 1.1,
        "contrast": 1.0,
        "brightness": 1.05,
        "temperature": 3,
    },
    logo_path=str(ASSETS_DIR / "nutrio-logo.png"),
    music_path=str(ASSETS_DIR / "nutrio-chill.mp3"),
)

# ─── Social Media Presets ────────────────────────────────

TIKTOK_VIRAL = Preset(
    name="tiktok-viral",
    description="TikTok viral style — fast cuts, zoom transitions",
    caption_style="tiktok",
    transitions="zoom",
    aspect_ratio="9:16",
    auto_edit=True,
    speed_ramp=True,
    color_grade={"saturation": 1.2, "contrast": 1.15},
)

YOUTUBE_SHORT = Preset(
    name="youtube-short",
    description="YouTube Shorts — clean, centered captions",
    caption_style="youtube",
    transitions="crossfade",
    aspect_ratio="9:16",
    auto_edit=True,
    color_grade={"saturation": 1.0, "contrast": 1.05},
)

INSTAGRAM_REEL = Preset(
    name="instagram-reel",
    description="Instagram Reels — sleek, minimal",
    caption_style="instagram",
    transitions="slide",
    aspect_ratio="9:16",
    auto_edit=True,
    color_grade={"saturation": 1.15, "contrast": 1.1, "temperature": 3},
)

# ─── Registry ────────────────────────────────────────────

ALL_PRESETS: dict[str, Preset] = {
    "park-it-ad": PARK_IT_AD,
    "surve-ad": SURVE_AD,
    "nutrio-ad": NUTRIO_AD,
    "tiktok-viral": TIKTOK_VIRAL,
    "youtube-short": YOUTUBE_SHORT,
    "instagram-reel": INSTAGRAM_REEL,
}


def get_preset(name: str) -> Preset:
    """Get a preset by name. Raises KeyError if not found."""
    if name not in ALL_PRESETS:
        raise KeyError(f"Unknown preset: {name}. Available: {list(ALL_PRESETS.keys())}")
    return ALL_PRESETS[name]


def list_presets() -> list[dict]:
    """Return list of preset summaries for API/UI."""
    return [
        {"name": p.name, "description": p.description, "aspect_ratio": p.aspect_ratio}
        for p in ALL_PRESETS.values()
    ]


if __name__ == "__main__":
    for name, preset in ALL_PRESETS.items():
        print(f"  {name}: {preset.description}")
