#!/usr/bin/env python3
"""
AI Video Editor — Main CLI entry point and pipeline orchestrator.

Usage:
    python editor.py input.mp4 --preset park-it-ad --output output/
    python editor.py input.mp4 --auto-edit --trim-silence --add-music bg.mp3
    python editor.py input.mp4 --smart-crop vertical --captions-only --caption-style tiktok
    python editor.py input.mp4 --preset tiktok-viral --thumbnail --quality high

Backwards-compatible with caption.py usage.
"""

import argparse
import glob
import os
import sys
import tempfile
from pathlib import Path

# Ensure we're using the venv
VENV_PYTHON = Path(__file__).parent / "venv" / "bin" / "python"
if Path(sys.executable).resolve() != VENV_PYTHON.resolve() and VENV_PYTHON.exists():
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON)] + sys.argv)

from modules import Transcription
from modules.preprocessor import Preprocessor
from modules.ai_analyzer import AIAnalyzer
from modules.editor_engine import EditorEngine
from modules.branding import Branding
from modules.captions import Captions
from modules.effects import Effects
from modules.exporter import Exporter
from modules.presets import get_preset, list_presets, Preset

OUTPUT_DIR = Path(__file__).parent / "output"


def process_video(input_path: str, args) -> str:
    """Run the full video editing pipeline based on CLI arguments."""
    input_path = os.path.abspath(input_path)
    if not os.path.exists(input_path):
        print(f"Error: File not found: {input_path}")
        return None

    output_dir = os.path.abspath(args.output) if args.output else str(OUTPUT_DIR)
    os.makedirs(output_dir, exist_ok=True)

    # Load preset if specified
    preset = None
    if args.preset:
        preset = get_preset(args.preset)
        print(f"[preset] Using preset: {preset.name} — {preset.description}")

    # Initialize modules
    preprocessor = Preprocessor()
    analyzer = AIAnalyzer()
    engine = EditorEngine()
    branding = Branding()
    captions_mod = Captions()
    effects = Effects()
    exporter = Exporter()

    working_video = input_path
    transcript = None
    energy = None
    faces = None
    caption_segments = None

    # ─── Step 1: Preprocessing ───────────────────────────
    print("\n[1/7] Preprocessing...")
    try:
        info = preprocessor.analyze(working_video)
    except Exception as e:
        print(f"Error: Could not read video file: {e}")
        return None
    print(f"  Input: {info.width}x{info.height} @ {info.fps:.1f}fps, {info.duration:.1f}s")

    # Trim silence
    if args.trim_silence or (preset and preset.trim_silence):
        print("  Trimming silence...")
        working_video = preprocessor.trim_silence(working_video)

    # Smart crop
    crop_ratio = args.smart_crop
    if crop_ratio:
        ratio_map = {"vertical": "9:16", "square": "1:1", "4:5": "4:5"}
        ratio = ratio_map.get(crop_ratio, crop_ratio)
        print(f"  Smart cropping to {ratio}...")
        working_video = preprocessor.crop_aspect(working_video, ratio=ratio)
    elif preset and preset.aspect_ratio != "16:9":
        print(f"  Cropping to preset aspect ratio {preset.aspect_ratio}...")
        working_video = preprocessor.crop_aspect(working_video, ratio=preset.aspect_ratio)

    # ─── Step 2: AI Analysis ────────────────────────────
    if not args.captions_only:
        print("\n[2/7] AI Analysis...")
        # Transcribe
        model = args.model or "base"
        print(f"  Transcribing (model={model})...")
        transcript = analyzer.transcribe(working_video, model=model)
        print(f"  Found {len(transcript.segments)} segments, language={transcript.language}")

        # Energy analysis for speed ramping
        if args.speed_ramp or (preset and preset.speed_ramp):
            print("  Analyzing audio energy...")
            audio_path = preprocessor.extract_audio(working_video)
            energy = analyzer.analyze_energy(audio_path)
            # Cleanup
            if os.path.exists(audio_path):
                os.remove(audio_path)
    else:
        print("\n[2/7] AI Analysis (captions-only mode)...")
        model = args.model or "base"
        transcript = analyzer.transcribe(working_video, model=model)
        print(f"  Found {len(transcript.segments)} segments")

    # ─── Step 3: Editing ────────────────────────────────
    if not args.captions_only:
        print("\n[3/7] Editing...")

        # Auto-cut
        if args.auto_edit or (preset and preset.auto_edit):
            print("  Auto-cutting dead air...")
            edit_list = engine.auto_cut(working_video, transcript)
            if edit_list.cuts:
                working_video = engine.apply_cuts(working_video, edit_list)
                print(f"  Kept {len(edit_list.cuts)} segments")

        # Speed ramp
        if (args.speed_ramp or (preset and preset.speed_ramp)) and energy:
            print("  Applying speed ramp...")
            working_video = engine.speed_ramp(working_video, energy)

        # Audio ducking with background music
        if args.add_music:
            if os.path.exists(args.add_music):
                print(f"  Ducking audio with music: {args.add_music}")
                working_video = engine.duck_audio(working_video, args.add_music)
            else:
                print(f"  Warning: Music file not found: {args.add_music}")
        elif preset and preset.music_path and os.path.exists(preset.music_path):
            print(f"  Adding preset music with ducking...")
            working_video = engine.duck_audio(working_video, preset.music_path)

        # Normalize audio
        if args.normalize_audio:
            print("  Normalizing audio levels...")
            working_video = engine.normalize_audio(working_video)
    else:
        print("\n[3/7] Editing (skipped — captions only)")

    # ─── Step 4: Captions ───────────────────────────────
    caption_style = args.caption_style or (preset.caption_style if preset else "tiktok")

    if not args.no_captions and transcript:
        print(f"\n[4/7] Captions (style={caption_style})...")
        caption_segments = captions_mod.generate(
            working_video, style=caption_style, transcript=transcript
        )
        print(f"  Generated {len(caption_segments)} caption segments")

        # Generate ASS file
        vid_info = preprocessor.analyze(working_video)
        ass_path = os.path.join(tempfile.gettempdir(),
                               f"ve_{Path(input_path).stem}.ass")
        captions_mod.generate_ass(
            caption_segments, ass_path, style=caption_style,
            video_width=vid_info.width, video_height=vid_info.height
        )

        # Burn captions into video
        working_video = captions_mod.burn_captions(working_video, ass_path)
    else:
        print("\n[4/7] Captions (skipped)")

    # ─── Step 5: Branding ──────────────────────────────
    if preset and not args.captions_only:
        print("\n[5/7] Branding...")

        # Color grading
        if preset.color_grade:
            print("  Applying color grade...")
            working_video = branding.color_grade(working_video, preset)

        # Logo watermark
        if preset.logo_path and os.path.exists(preset.logo_path):
            print("  Adding watermark...")
            working_video = branding.add_watermark(working_video, preset.logo_path)

        # CTA overlay
        if preset.cta_text and args.cta:
            print(f"  Adding CTA: {args.cta}")
            working_video = branding.add_cta(working_video, args.cta, preset)
        elif preset.cta_text:
            print(f"  Adding CTA: {preset.cta_text}")
            working_video = branding.add_cta(working_video, preset.cta_text, preset)
    else:
        # Manual branding options
        if args.title or args.endcard or args.logo or args.cta:
            print("\n[5/7] Branding...")
            manual_preset = preset or Preset(name="custom")

            if args.logo and os.path.exists(args.logo):
                working_video = branding.add_watermark(working_video, args.logo)

            if args.cta:
                working_video = branding.add_cta(working_video, args.cta, manual_preset)
        else:
            print("\n[5/7] Branding (skipped)")

    # Title and endcard overlays (FFmpeg drawtext, like original caption.py)
    if args.title or args.endcard:
        print("  Adding title/endcard overlays...")
        working_video = _apply_text_overlays(working_video, args.title, args.endcard)

    # ─── Step 6: Effects ───────────────────────────────
    if not args.captions_only:
        effects_applied = False
        if args.color_grade and not (preset and preset.color_grade):
            print("\n[6/7] Effects...")
            effects_applied = True

        if args.transitions and args.transitions != "cut":
            if not effects_applied:
                print("\n[6/7] Effects...")
                effects_applied = True

        if not effects_applied:
            print("\n[6/7] Effects (skipped)")
    else:
        print("\n[6/7] Effects (skipped)")

    # ─── Step 7: Export ────────────────────────────────
    print("\n[7/7] Exporting...")
    export_format = args.format or ("tiktok" if not preset else None)
    quality = args.quality or "standard"

    stem = Path(input_path).stem
    if preset:
        filename = f"{stem}_{preset.name}"
    elif export_format:
        filename = f"{stem}_{export_format}"
    else:
        filename = f"{stem}_edited"

    if export_format:
        output_path = exporter.export(
            working_video, output_dir, format=export_format,
            quality=quality, filename=filename
        )
    else:
        # Just copy/re-encode to output
        output_path = os.path.join(output_dir, f"{filename}.mp4")
        import shutil
        shutil.copy2(working_video, output_path)

    print(f"  Output: {output_path}")

    # Generate thumbnail if requested
    if args.thumbnail:
        thumb_path = exporter.generate_thumbnail(working_video, output_dir)
        print(f"  Thumbnail: {thumb_path}")

    # Export subtitles if we have captions
    if caption_segments:
        srt_path = os.path.join(output_dir, f"{filename}.srt")
        captions_mod.export_srt(caption_segments, srt_path)
        print(f"  Subtitles: {srt_path}")

    # Final stats
    file_size = os.path.getsize(output_path) / (1024 * 1024)
    print(f"\nDone! {file_size:.1f}MB")

    return output_path


def _apply_text_overlays(video_path: str, title: str = None, endcard: str = None) -> str:
    """Apply title and endcard text overlays (compatible with original caption.py)."""
    import subprocess
    probe = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", video_path],
        capture_output=True, text=True,
    )
    duration = float(probe.stdout.strip())

    filters = []
    if title:
        title_escaped = title.replace("'", "'\\''")
        filters.append(
            f"drawtext=text='{title_escaped}':"
            f"fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
            f"fontsize=56:fontcolor=white:borderw=3:bordercolor=black:"
            f"x=(w-text_w)/2:y=(h-text_h)/2:"
            f"enable='between(t,0,3)':"
            f"alpha='if(lt(t,0.5),t/0.5,if(gt(t,2.5),(3-t)/0.5,1))'"
        )
    if endcard:
        endcard_escaped = endcard.replace("'", "'\\''")
        end_start = max(0, duration - 4)
        filters.append(
            f"drawtext=text='{endcard_escaped}':"
            f"fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
            f"fontsize=56:fontcolor=white:borderw=3:bordercolor=black:"
            f"x=(w-text_w)/2:y=(h-text_h)/2:"
            f"enable='between(t,{end_start},{duration})':"
            f"alpha='if(lt(t-{end_start},0.5),(t-{end_start})/0.5,1)'"
        )

    if not filters:
        return video_path

    output = os.path.join(tempfile.gettempdir(),
                         f"ve_{Path(video_path).stem}_overlays.mp4")
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vf", ",".join(filters),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "copy",
        output,
    ]
    subprocess.run(cmd, capture_output=True, text=True, check=True)
    return output


def main():
    parser = argparse.ArgumentParser(
        description="AI Video Editor — Process, edit, and produce polished videos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
               "  python editor.py input.mp4 --preset park-it-ad\n"
               "  python editor.py input.mp4 --auto-edit --trim-silence\n"
               "  python editor.py input.mp4 --captions-only --caption-style tiktok\n"
               "  python editor.py input.mp4 --preset tiktok-viral --thumbnail\n",
    )

    # Input
    parser.add_argument("video", nargs="*", help="Input video file(s) or glob pattern")
    parser.add_argument("--output", "-o", help="Output directory (default: output/)")

    # Presets
    parser.add_argument("--preset", choices=[
        "park-it-ad", "surve-ad", "nutrio-ad",
        "tiktok-viral", "youtube-short", "instagram-reel",
    ], help="Apply named preset")
    parser.add_argument("--list-presets", action="store_true",
                        help="List available presets and exit")

    # Processing
    parser.add_argument("--auto-edit", action="store_true",
                        help="Smart auto-cut (remove dead air, ums, pauses)")
    parser.add_argument("--trim-silence", action="store_true",
                        help="Remove silent sections")
    parser.add_argument("--speed-ramp", action="store_true",
                        help="Auto speed ramp (slow-mo highlights, speed up boring)")
    parser.add_argument("--smart-crop", metavar="RATIO",
                        help="Smart crop: vertical, square, 4:5, or W:H")
    parser.add_argument("--highlight-reel", action="store_true",
                        help="Generate highlight reel from best moments")
    parser.add_argument("--duration", type=float,
                        help="Target duration for highlight reel (seconds)")

    # Captions
    parser.add_argument("--captions-only", action="store_true",
                        help="Only add captions (skip other processing)")
    parser.add_argument("--caption-style",
                        choices=["tiktok", "instagram", "youtube", "minimal", "bold", "karaoke"],
                        help="Caption style")
    parser.add_argument("--no-captions", action="store_true",
                        help="Skip captions entirely")
    parser.add_argument("--model",
                        choices=["tiny", "base", "small", "medium"],
                        help="Whisper model size (default: base)")

    # Branding
    parser.add_argument("--title", help="Title overlay at start")
    parser.add_argument("--endcard", help="End card text")
    parser.add_argument("--logo", help="Logo/watermark image path")
    parser.add_argument("--cta", help="Call-to-action overlay text")

    # Audio
    parser.add_argument("--add-music", help="Add background music with auto-ducking")
    parser.add_argument("--normalize-audio", action="store_true",
                        help="Normalize audio levels (target: -16 LUFS)")

    # Effects
    parser.add_argument("--transitions",
                        choices=["crossfade", "zoom", "slide", "cut"],
                        help="Transition style between scenes")
    parser.add_argument("--color-grade", help="Apply color grading preset or custom LUT")

    # Export
    parser.add_argument("--format",
                        choices=["tiktok", "instagram", "ig_reel", "ig_square",
                                "youtube", "yt_short"],
                        help="Export format/platform preset")
    parser.add_argument("--quality",
                        choices=["draft", "standard", "high"],
                        default="standard",
                        help="Output quality (default: standard)")
    parser.add_argument("--thumbnail", action="store_true",
                        help="Also generate thumbnail image")

    args = parser.parse_args()

    # Handle --list-presets
    if args.list_presets:
        print("Available presets:\n")
        for p in list_presets():
            print(f"  {p['name']:20s} {p['description']}")
        sys.exit(0)

    # Require video input unless --list-presets
    if not args.video:
        parser.error("the following arguments are required: video")

    # Process each input video
    for pattern in args.video:
        # Support glob patterns
        files = glob.glob(pattern) if "*" in pattern else [pattern]
        for video_path in files:
            print(f"\n{'='*60}")
            print(f"Processing: {video_path}")
            print(f"{'='*60}")
            process_video(video_path, args)


if __name__ == "__main__":
    main()
