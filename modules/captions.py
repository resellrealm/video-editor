"""Captions module — extends existing caption.py with multiple styles, emoji, multi-language."""

import os
import subprocess
import tempfile
from pathlib import Path

from modules import CaptionSegment, Transcription, WordTimestamp

# Caption style definitions
CAPTION_STYLES = {
    "tiktok": {
        "font": "DejaVu Sans Bold",
        "fontsize": 52,
        "primary_color": "&H00FFFFFF",  # White
        "highlight_color": "&H0000FFFF",  # Yellow (karaoke highlight)
        "outline_color": "&H00000000",  # Black
        "outline_width": 4,
        "alignment": 2,  # Bottom center
        "margin_v": 120,
        "bold": True,
    },
    "instagram": {
        "font": "DejaVu Sans",
        "fontsize": 42,
        "primary_color": "&H00FFFFFF",
        "highlight_color": "&H00FF88FF",  # Pink
        "outline_color": "&H80000000",
        "outline_width": 3,
        "alignment": 2,
        "margin_v": 200,
        "bold": False,
    },
    "youtube": {
        "font": "DejaVu Sans Bold",
        "fontsize": 48,
        "primary_color": "&H00FFFFFF",
        "highlight_color": "&H0000CCFF",  # Orange
        "outline_color": "&H00000000",
        "outline_width": 4,
        "alignment": 2,
        "margin_v": 60,
        "bold": True,
    },
    "minimal": {
        "font": "DejaVu Sans",
        "fontsize": 38,
        "primary_color": "&H00FFFFFF",
        "highlight_color": "&H00FFFFFF",  # No highlight (same as primary)
        "outline_color": "&H50000000",
        "outline_width": 2,
        "alignment": 2,
        "margin_v": 100,
        "bold": False,
    },
    "bold": {
        "font": "DejaVu Sans Bold",
        "fontsize": 58,
        "primary_color": "&H00FFFFFF",
        "highlight_color": "&H0000FF00",  # Green
        "outline_color": "&H00000000",
        "outline_width": 5,
        "alignment": 2,
        "margin_v": 100,
        "bold": True,
    },
    "karaoke": {
        "font": "DejaVu Sans Bold",
        "fontsize": 50,
        "primary_color": "&H00AAAAAA",  # Gray (unsung)
        "highlight_color": "&H0000FFFF",  # Yellow (sung)
        "outline_color": "&H00000000",
        "outline_width": 4,
        "alignment": 2,
        "margin_v": 100,
        "bold": True,
    },
}

MAX_WORDS_PER_LINE = 4


class Captions:
    """Caption generation with multiple styles, word-by-word highlight, emoji support."""

    def generate(self, video_path: str, style: str = "tiktok",
                 model: str = "base", transcript: Transcription = None) -> list[CaptionSegment]:
        """Generate captions from video. Optionally reuse an existing transcript."""
        if transcript is None:
            from modules.ai_analyzer import AIAnalyzer
            analyzer = AIAnalyzer()
            transcript = analyzer.transcribe(video_path, model=model)

        # Re-chunk into display-friendly segments
        segments = []
        for seg in transcript.segments:
            words = seg.words if seg.words else [
                WordTimestamp(start=seg.start, end=seg.end, word=seg.text)
            ]
            for i in range(0, len(words), MAX_WORDS_PER_LINE):
                chunk = words[i:i + MAX_WORDS_PER_LINE]
                segments.append(CaptionSegment(
                    start=chunk[0].start,
                    end=chunk[-1].end,
                    text=" ".join(w.word for w in chunk),
                    words=chunk,
                ))

        return segments

    def generate_ass(self, captions: list[CaptionSegment], output_path: str,
                     style: str = "tiktok", video_width: int = 1080,
                     video_height: int = 1920) -> str:
        """Write captions to ASS file with word-by-word highlight effect."""
        style_def = CAPTION_STYLES.get(style, CAPTION_STYLES["tiktok"])

        with open(output_path, "w") as f:
            f.write("[Script Info]\n")
            f.write("ScriptType: v4.00+\n")
            f.write(f"PlayResX: {video_width}\n")
            f.write(f"PlayResY: {video_height}\n")
            f.write("WrapStyle: 0\n\n")

            f.write("[V4+ Styles]\n")
            f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
                    "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
                    "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
                    "Alignment, MarginL, MarginR, MarginV, Encoding\n")
            bold_flag = -1 if style_def["bold"] else 0
            f.write(
                f"Style: Default,{style_def['font']},{style_def['fontsize']},"
                f"{style_def['primary_color']},{style_def['highlight_color']},"
                f"{style_def['outline_color']},&H80000000,"
                f"{bold_flag},0,0,0,100,100,0,0,1,"
                f"{style_def['outline_width']},0,"
                f"{style_def['alignment']},20,20,{style_def['margin_v']},1\n\n"
            )

            f.write("[Events]\n")
            f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")

            for cap in captions:
                start = _ass_timestamp(cap.start)
                end = _ass_timestamp(cap.end)

                if len(cap.words) > 1:
                    parts = []
                    for w in cap.words:
                        dur_cs = int((w.end - w.start) * 100)
                        parts.append(f"{{\\kf{dur_cs}}}{w.word}")
                    text = " ".join(parts)
                else:
                    text = cap.text

                f.write(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}\n")

        return output_path

    def burn_captions(self, video_path: str, ass_path: str) -> str:
        """Burn ASS captions into video."""
        output = os.path.join(tempfile.gettempdir(),
                             f"ve_{Path(video_path).stem}_captioned.mp4")
        sub_escaped = ass_path.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
        cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-vf", f"ass={sub_escaped}",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "copy",
            output,
        ]
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        return output

    def emoji_insert(self, captions: list[CaptionSegment]) -> list[CaptionSegment]:
        """Insert contextual emoji based on caption text."""
        emoji_map = {
            "love": "\u2764\ufe0f", "heart": "\u2764\ufe0f",
            "fire": "\U0001f525", "hot": "\U0001f525", "amazing": "\U0001f525",
            "laugh": "\U0001f602", "funny": "\U0001f602", "lol": "\U0001f602",
            "sad": "\U0001f622", "cry": "\U0001f622",
            "wow": "\U0001f631", "omg": "\U0001f631",
            "food": "\U0001f37d\ufe0f", "eat": "\U0001f37d\ufe0f", "cook": "\U0001f37d\ufe0f",
            "money": "\U0001f4b0", "rich": "\U0001f4b0", "cash": "\U0001f4b0",
            "music": "\U0001f3b5", "song": "\U0001f3b5",
            "happy": "\U0001f60a", "great": "\U0001f60a",
            "think": "\U0001f914", "hmm": "\U0001f914",
            "check": "\u2705", "done": "\u2705", "yes": "\u2705",
            "no": "\u274c", "wrong": "\u274c",
            "fast": "\u26a1", "quick": "\u26a1",
            "star": "\u2b50", "best": "\u2b50",
            "park": "\U0001f697", "car": "\U0001f697", "drive": "\U0001f697",
            "health": "\U0001f4aa", "fit": "\U0001f4aa", "strong": "\U0001f4aa",
        }

        for cap in captions:
            words_lower = cap.text.lower().split()
            for word in words_lower:
                clean = word.strip(".,!?")
                if clean in emoji_map:
                    cap.text += f" {emoji_map[clean]}"
                    break  # One emoji per segment max

        return captions

    def multi_language(self, captions: list[CaptionSegment],
                       target_lang: str) -> list[CaptionSegment]:
        """Stub for multi-language translation. Returns original captions with a note."""
        # In production, this would call a translation API
        print(f"[captions] Multi-language translation to '{target_lang}' is a stub — "
              "integrate a translation API for production use.")
        return captions

    def export_srt(self, captions: list[CaptionSegment], path: str) -> str:
        """Export captions to SRT format."""
        with open(path, "w") as f:
            for i, cap in enumerate(captions, 1):
                start = _srt_timestamp(cap.start)
                end = _srt_timestamp(cap.end)
                f.write(f"{i}\n{start} --> {end}\n{cap.text}\n\n")
        return path

    def export_vtt(self, captions: list[CaptionSegment], path: str) -> str:
        """Export captions to WebVTT format."""
        with open(path, "w") as f:
            f.write("WEBVTT\n\n")
            for i, cap in enumerate(captions, 1):
                start = _vtt_timestamp(cap.start)
                end = _vtt_timestamp(cap.end)
                f.write(f"{i}\n{start} --> {end}\n{cap.text}\n\n")
        return path


def _ass_timestamp(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds % 1) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _srt_timestamp(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _vtt_timestamp(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


if __name__ == "__main__":
    print("Available caption styles:", list(CAPTION_STYLES.keys()))
