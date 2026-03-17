#!/usr/bin/env python3
"""
Video Caption Tool — TikTok/Reels style auto-captioning pipeline.

Upload a video → Whisper transcription → Stylized captions → Export.

Usage:
    python caption.py input/myvideo.mp4
    python caption.py input/myvideo.mp4 --title "POV you meal prep from home"
    python caption.py input/myvideo.mp4 --title "POV you meal prep from home" --trim-silence
    python caption.py input/myvideo.mp4 --title "POV you meal prep from home" --endcard "Download Nutrio+ 🔗"

Outputs to: output/<filename>_captioned.mp4
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# Ensure we're using the venv
VENV_PYTHON = Path(__file__).parent / "venv" / "bin" / "python"
if Path(sys.executable).resolve() != VENV_PYTHON.resolve() and VENV_PYTHON.exists():
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON)] + sys.argv)

from faster_whisper import WhisperModel


# ─── CONFIG ──────────────────────────────────────────────
WHISPER_MODEL = "base"  # base=~500MB RAM. Options: tiny, base, small, medium
FONT = "Arial"
FONT_SIZE = 48
FONT_COLOR = "white"
HIGHLIGHT_COLOR = "&H0000FFFF"  # Yellow (BGR format for ASS)
OUTLINE_COLOR = "black"
OUTLINE_WIDTH = 4
TITLE_FONT_SIZE = 56
TITLE_DURATION = 3  # seconds
ENDCARD_DURATION = 4  # seconds
MAX_WORDS_PER_LINE = 4
OUTPUT_DIR = Path(__file__).parent / "output"
# ─────────────────────────────────────────────────────────


def transcribe(video_path: str, model_size: str = WHISPER_MODEL) -> list[dict]:
    """Transcribe video using faster-whisper. Returns list of word-level timestamps."""
    print(f"🎙️  Transcribing with Whisper ({model_size})...")
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, info = model.transcribe(video_path, beam_size=5, word_timestamps=True)

    # Collect all words with individual timestamps for word-by-word highlighting
    all_words = []
    for segment in segments:
        if segment.words:
            for w in segment.words:
                all_words.append({
                    "start": w.start,
                    "end": w.end,
                    "word": w.word.strip(),
                })
        else:
            all_words.append({
                "start": segment.start,
                "end": segment.end,
                "word": segment.text.strip(),
            })

    # Group words into caption chunks
    captions = []
    for i in range(0, len(all_words), MAX_WORDS_PER_LINE):
        chunk = all_words[i:i + MAX_WORDS_PER_LINE]
        captions.append({
            "start": chunk[0]["start"],
            "end": chunk[-1]["end"],
            "text": " ".join(w["word"] for w in chunk),
            "words": chunk,
        })

    print(f"   Found {len(captions)} caption segments ({info.language}, {info.duration:.1f}s)")
    return captions


def generate_ass(captions: list[dict], ass_path: str, video_width: int = 1920, video_height: int = 1080):
    """Write captions to ASS file with word-by-word highlight effect."""
    with open(ass_path, "w") as f:
        f.write("[Script Info]\n")
        f.write("ScriptType: v4.00+\n")
        f.write(f"PlayResX: {video_width}\n")
        f.write(f"PlayResY: {video_height}\n")
        f.write("WrapStyle: 0\n\n")
        f.write("[V4+ Styles]\n")
        f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
        f.write(f"Style: Default,DejaVu Sans,{FONT_SIZE},&H00FFFFFF,{HIGHLIGHT_COLOR},&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,{OUTLINE_WIDTH},0,2,20,20,120,1\n\n")
        f.write("[Events]\n")
        f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")

        for cap in captions:
            start = _ass_timestamp(cap["start"])
            end = _ass_timestamp(cap["end"])
            words = cap.get("words", [])

            if len(words) > 1:
                # Build word-by-word highlight using karaoke-style override tags
                parts = []
                for w in words:
                    word_dur_cs = int((w["end"] - w["start"]) * 100)  # centiseconds
                    parts.append(f"{{\\kf{word_dur_cs}}}{w['word']}")
                text = " ".join(parts)
                # Use \1c for default white, \3c for outline; karaoke \kf highlights with SecondaryColour
                f.write(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}\n")
            else:
                f.write(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{cap['text']}\n")

    print(f"📝 ASS written: {ass_path}")


def generate_srt(captions: list[dict], srt_path: str):
    """Write captions to SRT file (fallback)."""
    with open(srt_path, "w") as f:
        for i, cap in enumerate(captions, 1):
            start = _srt_timestamp(cap["start"])
            end = _srt_timestamp(cap["end"])
            f.write(f"{i}\n{start} --> {end}\n{cap['text']}\n\n")
    print(f"📝 SRT written: {srt_path}")


def _srt_timestamp(seconds: float) -> str:
    """Convert seconds to SRT timestamp format."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _ass_timestamp(seconds: float) -> str:
    """Convert seconds to ASS timestamp format (H:MM:SS.CC)."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds % 1) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def get_video_dimensions(video_path: str) -> tuple[int, int]:
    """Get video width and height using ffprobe."""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-select_streams", "v:0",
         "-show_entries", "stream=width,height",
         "-of", "csv=p=0:s=x", video_path],
        capture_output=True, text=True
    )
    w, h = result.stdout.strip().split("x")
    return int(w), int(h)


def crop_vertical(video_path: str, output_path: str) -> str:
    """Crop video to 9:16 aspect ratio (center crop) for TikTok/Reels."""
    print("📐 Cropping to 9:16 vertical format...")
    w, h = get_video_dimensions(video_path)

    # Calculate 9:16 crop dimensions
    target_ratio = 9 / 16
    current_ratio = w / h

    if current_ratio > target_ratio:
        # Video is wider than 9:16 — crop width
        new_w = int(h * target_ratio)
        new_w = new_w - (new_w % 2)  # ensure even
        crop_filter = f"crop={new_w}:{h}"
    else:
        # Video is taller than 9:16 — crop height
        new_h = int(w / target_ratio)
        new_h = new_h - (new_h % 2)  # ensure even
        crop_filter = f"crop={w}:{new_h}"

    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vf", crop_filter,
        "-c:a", "copy", "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"⚠️  ffmpeg crop stderr: {result.stderr[-500:]}")
        raise RuntimeError("ffmpeg crop failed")

    new_w, new_h = get_video_dimensions(output_path)
    print(f"   Cropped: {w}x{h} → {new_w}x{new_h}")
    return output_path


def trim_silence(video_path: str, output_path: str):
    """Remove silence from video using auto-editor."""
    print("✂️  Trimming silence...")
    subprocess.run([
        sys.executable, "-m", "auto_editor",
        video_path,
        "--margin", "0.2s",
        "--output", output_path,
    ], check=True, capture_output=True)
    print(f"   Trimmed: {output_path}")
    return output_path


def burn_captions(
    video_path: str,
    sub_path: str | None,
    output_path: str,
    title: str | None = None,
    endcard: str | None = None,
):
    """Burn captions into video using ffmpeg with TikTok-style styling."""
    print("🎬 Burning captions into video...")

    # Get video duration
    probe = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", video_path],
        capture_output=True, text=True
    )
    duration = float(probe.stdout.strip())

    # Build ffmpeg filter chain
    filters = []

    # Burn ASS subtitles (styled in the ASS file itself with word-by-word highlight)
    if sub_path:
        sub_escaped = sub_path.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
        filters.append(f"ass={sub_escaped}")

    # Title overlay at the start
    if title:
        title_escaped = title.replace("'", "'\\''")
        filters.append(
            f"drawtext=text='{title_escaped}':"
            f"fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
            f"fontsize={TITLE_FONT_SIZE}:fontcolor=white:borderw=3:bordercolor=black:"
            f"x=(w-text_w)/2:y=(h-text_h)/2:"
            f"enable='between(t,0,{TITLE_DURATION})':"
            f"alpha='if(lt(t,0.5),t/0.5,if(gt(t,{TITLE_DURATION - 0.5}),(({TITLE_DURATION}-t)/0.5),1))'"
        )

    # End card overlay
    if endcard:
        endcard_escaped = endcard.replace("'", "'\\''")
        end_start = max(0, duration - ENDCARD_DURATION)
        filters.append(
            f"drawtext=text='{endcard_escaped}':"
            f"fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
            f"fontsize={TITLE_FONT_SIZE}:fontcolor=white:borderw=3:bordercolor=black:"
            f"x=(w-text_w)/2:y=(h-text_h)/2:"
            f"enable='between(t,{end_start},{duration})':"
            f"alpha='if(lt(t-{end_start},0.5),(t-{end_start})/0.5,1)'"
        )

    filter_chain = ",".join(filters)

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", filter_chain,
        "-c:a", "copy",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"⚠️  ffmpeg stderr: {result.stderr[-500:]}")
        raise RuntimeError("ffmpeg failed")

    print(f"✅ Output: {output_path}")


def process_video(
    input_path: str,
    title: str | None = None,
    endcard: str | None = None,
    do_trim: bool = False,
    vertical: bool = False,
    model_size: str = WHISPER_MODEL,
    font_size: int = FONT_SIZE,
    words_per_line: int = MAX_WORDS_PER_LINE,
):
    """Full pipeline: transcribe → trim (optional) → crop (optional) → caption → export."""
    input_path = os.path.abspath(input_path)
    if not os.path.exists(input_path):
        print(f"❌ File not found: {input_path}")
        sys.exit(1)

    stem = Path(input_path).stem
    OUTPUT_DIR.mkdir(exist_ok=True)
    suffix = "_vertical" if vertical else ""

    working_video = input_path

    # Step 1: Trim silence (optional)
    if do_trim:
        trimmed_path = str(OUTPUT_DIR / f"{stem}_trimmed.mp4")
        working_video = trim_silence(input_path, trimmed_path)

    # Step 2: Crop to 9:16 vertical (optional)
    if vertical:
        cropped_path = str(OUTPUT_DIR / f"{stem}_cropped.mp4")
        working_video = crop_vertical(working_video, cropped_path)

    # Step 3: Transcribe
    captions = transcribe(working_video, model_size=model_size)

    if not captions:
        print("⚠️  No speech detected. Skipping captions.")
        if not title and not endcard:
            print("Nothing to do.")
            return

    # Step 4: Generate ASS with word-by-word highlight (only if we have captions)
    sub_path = None
    if captions:
        vid_w, vid_h = get_video_dimensions(working_video)
        sub_path = str(OUTPUT_DIR / f"{stem}{suffix}.ass")
        generate_ass(captions, sub_path, video_width=vid_w, video_height=vid_h)

    # Step 5: Burn captions + overlays
    output_path = str(OUTPUT_DIR / f"{stem}{suffix}_captioned.mp4")
    burn_captions(working_video, sub_path, output_path, title=title, endcard=endcard)

    # Cleanup intermediate files
    for tmp_suffix in ["_trimmed.mp4", "_cropped.mp4"]:
        tmp_file = str(OUTPUT_DIR / f"{stem}{tmp_suffix}")
        if os.path.exists(tmp_file):
            os.remove(tmp_file)

    file_size = os.path.getsize(output_path) / (1024 * 1024)
    print(f"\n🎉 Done! Output: {output_path} ({file_size:.1f}MB)")
    print(f"   Captions: {len(captions)} segments")
    if vertical:
        print(f"   Format: 9:16 vertical (TikTok/Reels)")
    if title:
        print(f"   Title: \"{title}\" (first {TITLE_DURATION}s)")
    if endcard:
        print(f"   End card: \"{endcard}\" (last {ENDCARD_DURATION}s)")

    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Auto-caption videos with TikTok/Reels style subtitles"
    )
    parser.add_argument("video", help="Path to input video file")
    parser.add_argument("--title", help="Title text overlay (shown at start)")
    parser.add_argument("--endcard", help="End card text (shown at end)")
    parser.add_argument("--trim-silence", action="store_true",
                        help="Remove silent sections before captioning")
    parser.add_argument("--vertical", action="store_true",
                        help="Crop to 9:16 vertical format for TikTok/Reels")
    parser.add_argument("--model", default=WHISPER_MODEL,
                        choices=["tiny", "base", "small", "medium"],
                        help=f"Whisper model size (default: {WHISPER_MODEL})")
    parser.add_argument("--font-size", type=int, default=FONT_SIZE,
                        help=f"Caption font size (default: {FONT_SIZE})")
    parser.add_argument("--words-per-line", type=int, default=MAX_WORDS_PER_LINE,
                        help=f"Max words per caption line (default: {MAX_WORDS_PER_LINE})")

    args = parser.parse_args()

    process_video(
        args.video,
        title=args.title,
        endcard=args.endcard,
        do_trim=args.trim_silence,
        vertical=args.vertical,
        model_size=args.model,
        font_size=args.font_size,
        words_per_line=args.words_per_line,
    )


if __name__ == "__main__":
    main()
