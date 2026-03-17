"""Preprocessor module — format detection, normalization, audio extraction, cropping, trim silence."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from modules import VideoInfo


class Preprocessor:
    """Video preprocessing: analyze, normalize, extract audio, crop, trim silence."""

    def analyze(self, video_path: str) -> VideoInfo:
        """Analyze video and return metadata."""
        cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_format", "-show_streams", video_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)

        video_stream = None
        has_audio = False
        for stream in data.get("streams", []):
            if stream["codec_type"] == "video" and video_stream is None:
                video_stream = stream
            elif stream["codec_type"] == "audio":
                has_audio = True

        if not video_stream:
            raise ValueError(f"No video stream found in {video_path}")

        fmt = data.get("format", {})
        return VideoInfo(
            path=video_path,
            width=int(video_stream["width"]),
            height=int(video_stream["height"]),
            fps=_parse_fps(video_stream.get("r_frame_rate", "30/1")),
            duration=float(fmt.get("duration", video_stream.get("duration", 0))),
            has_audio=has_audio,
            codec=video_stream.get("codec_name", "unknown"),
        )

    def normalize(self, video_path: str, target_fps: int = 30, target_codec: str = "h264") -> str:
        """Normalize video format. Returns path to normalized video."""
        info = self.analyze(video_path)

        # Skip if already normalized
        if info.codec == target_codec and abs(info.fps - target_fps) < 1:
            return video_path

        output = _tmp_path(video_path, "_normalized.mp4")
        cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-c:v", "libx264", "-r", str(target_fps),
            "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            output,
        ]
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        return output

    def extract_audio(self, video_path: str, format: str = "wav") -> str:
        """Extract audio track. Returns path to audio file."""
        output = _tmp_path(video_path, f"_audio.{format}")
        cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-vn", "-acodec", "pcm_s16le" if format == "wav" else "libmp3lame",
            "-ar", "16000", "-ac", "1",
            output,
        ]
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        return output

    def crop_aspect(self, video_path: str, ratio: str = "9:16", method: str = "center",
                    face_regions: list = None) -> str:
        """Smart crop to target aspect ratio with optional face-detection bias."""
        info = self.analyze(video_path)
        target_w, target_h = map(int, ratio.split(":"))
        target_ratio = target_w / target_h
        current_ratio = info.width / info.height

        if abs(current_ratio - target_ratio) < 0.01:
            return video_path  # Already correct ratio

        if current_ratio > target_ratio:
            # Wider — crop width
            new_w = int(info.height * target_ratio)
            new_w -= new_w % 2
            if face_regions and method == "center":
                # Bias crop toward face center
                avg_face_x = sum(f.x + f.w // 2 for f in face_regions) / len(face_regions)
                crop_x = max(0, min(int(avg_face_x - new_w // 2), info.width - new_w))
            else:
                crop_x = (info.width - new_w) // 2
            crop_filter = f"crop={new_w}:{info.height}:{crop_x}:0"
        else:
            # Taller — crop height
            new_h = int(info.width / target_ratio)
            new_h -= new_h % 2
            crop_y = (info.height - new_h) // 2
            crop_filter = f"crop={info.width}:{new_h}:0:{crop_y}"

        output = _tmp_path(video_path, f"_cropped.mp4")
        cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-vf", crop_filter,
            "-c:a", "copy", "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            output,
        ]
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        return output

    def trim_silence(self, video_path: str, margin: float = 0.2) -> str:
        """Remove silent sections using auto-editor. Returns trimmed video path."""
        output = _tmp_path(video_path, "_trimmed.mp4")
        cmd = [
            sys.executable, "-m", "auto_editor",
            video_path,
            "--margin", f"{margin}s",
            "--output", output,
        ]
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        return output


def _parse_fps(fps_str: str) -> float:
    """Parse fps string like '30/1' or '29.97'."""
    if "/" in fps_str:
        num, den = fps_str.split("/")
        return float(num) / float(den) if float(den) != 0 else 30.0
    return float(fps_str)


def _tmp_path(source: str, suffix: str) -> str:
    """Generate a temp output path based on source filename."""
    stem = Path(source).stem
    return os.path.join(tempfile.gettempdir(), f"ve_{stem}{suffix}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m modules.preprocessor <video_path>")
        sys.exit(1)
    p = Preprocessor()
    info = p.analyze(sys.argv[1])
    print(f"Video: {info.width}x{info.height} @ {info.fps:.1f}fps, {info.duration:.1f}s, codec={info.codec}, audio={info.has_audio}")
