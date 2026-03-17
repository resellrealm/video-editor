"""Exporter module — platform presets, quality settings, thumbnails, subtitles, metadata."""

import json
import os
import subprocess
import tempfile
from pathlib import Path


class Exporter:
    """Export videos with platform-specific presets and quality settings."""

    PLATFORM_PRESETS = {
        "tiktok":    {"width": 1080, "height": 1920, "fps": 30, "codec": "h264"},
        "instagram": {"width": 1080, "height": 1350, "fps": 30, "codec": "h264"},
        "ig_reel":   {"width": 1080, "height": 1920, "fps": 30, "codec": "h264"},
        "ig_square": {"width": 1080, "height": 1080, "fps": 30, "codec": "h264"},
        "youtube":   {"width": 1920, "height": 1080, "fps": 30, "codec": "h264"},
        "yt_short":  {"width": 1080, "height": 1920, "fps": 30, "codec": "h264"},
    }

    QUALITY_PRESETS = {
        "draft":    {"crf": 28, "preset": "ultrafast"},
        "standard": {"crf": 23, "preset": "fast"},
        "high":     {"crf": 18, "preset": "slow"},
    }

    def export(self, video_path: str, output_dir: str, format: str = "tiktok",
               quality: str = "standard", filename: str = None) -> str:
        """Export video with platform format and quality preset."""
        platform = self.PLATFORM_PRESETS.get(format)
        if not platform:
            raise ValueError(f"Unknown format: {format}. Options: {list(self.PLATFORM_PRESETS.keys())}")

        qual = self.QUALITY_PRESETS.get(quality)
        if not qual:
            raise ValueError(f"Unknown quality: {quality}. Options: {list(self.QUALITY_PRESETS.keys())}")

        os.makedirs(output_dir, exist_ok=True)
        stem = filename or f"{Path(video_path).stem}_{format}"
        output = os.path.join(output_dir, f"{stem}.mp4")

        # Scale to target resolution, maintaining aspect ratio with padding
        scale_filter = (
            f"scale={platform['width']}:{platform['height']}:"
            f"force_original_aspect_ratio=decrease,"
            f"pad={platform['width']}:{platform['height']}:(ow-iw)/2:(oh-ih)/2:black"
        )

        cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-vf", scale_filter,
            "-r", str(platform["fps"]),
            "-c:v", f"lib{platform['codec']}",
            "-crf", str(qual["crf"]),
            "-preset", qual["preset"],
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart",
            output,
        ]
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        return output

    def generate_thumbnail(self, video_path: str, output_dir: str,
                           timestamp: str = "best") -> str:
        """Generate thumbnail image. 'best' selects the highest contrast frame."""
        os.makedirs(output_dir, exist_ok=True)
        stem = Path(video_path).stem
        output = os.path.join(output_dir, f"{stem}_thumbnail.jpg")

        if timestamp == "best":
            # Use thumbnail filter to find best frame in first 30 seconds
            cmd = [
                "ffmpeg", "-y", "-i", video_path,
                "-vf", "thumbnail=300,scale=1280:720:force_original_aspect_ratio=decrease",
                "-frames:v", "1",
                "-q:v", "2",
                output,
            ]
        else:
            cmd = [
                "ffmpeg", "-y", "-i", video_path,
                "-ss", str(timestamp),
                "-vf", "scale=1280:720:force_original_aspect_ratio=decrease",
                "-frames:v", "1",
                "-q:v", "2",
                output,
            ]
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        return output

    def export_subtitles(self, captions, format: str = "srt",
                         output_dir: str = None) -> str:
        """Export captions to SRT or VTT format."""
        output_dir = output_dir or tempfile.gettempdir()
        os.makedirs(output_dir, exist_ok=True)

        if format == "srt":
            return self._export_srt(captions, output_dir)
        elif format == "vtt":
            return self._export_vtt(captions, output_dir)
        else:
            raise ValueError(f"Unknown subtitle format: {format}")

    def _export_srt(self, captions, output_dir: str) -> str:
        output = os.path.join(output_dir, "captions.srt")
        with open(output, "w") as f:
            for i, cap in enumerate(captions, 1):
                start = _format_srt_time(cap.start)
                end = _format_srt_time(cap.end)
                f.write(f"{i}\n{start} --> {end}\n{cap.text}\n\n")
        return output

    def _export_vtt(self, captions, output_dir: str) -> str:
        output = os.path.join(output_dir, "captions.vtt")
        with open(output, "w") as f:
            f.write("WEBVTT\n\n")
            for i, cap in enumerate(captions, 1):
                start = _format_vtt_time(cap.start)
                end = _format_vtt_time(cap.end)
                f.write(f"{i}\n{start} --> {end}\n{cap.text}\n\n")
        return output

    def inject_metadata(self, video_path: str, title: str = None,
                        description: str = None, tags: list[str] = None) -> str:
        """Inject metadata into video file."""
        output = video_path + ".tmp.mp4"
        cmd = ["ffmpeg", "-y", "-i", video_path, "-c", "copy"]
        if title:
            cmd += ["-metadata", f"title={title}"]
        if description:
            cmd += ["-metadata", f"comment={description}"]
        if tags:
            cmd += ["-metadata", f"genre={','.join(tags)}"]
        cmd.append(output)
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        os.replace(output, video_path)
        return video_path


def _format_srt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _format_vtt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


if __name__ == "__main__":
    print("Available platform presets:", list(Exporter.PLATFORM_PRESETS.keys()))
    print("Available quality presets:", list(Exporter.QUALITY_PRESETS.keys()))
