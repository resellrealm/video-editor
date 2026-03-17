"""Effects module — zoom pulses, shake, blur/bokeh, vignette, glitch, particles."""

import os
import subprocess
import tempfile
from pathlib import Path


class Effects:
    """Visual effects for video post-processing."""

    def zoom_pulse(self, video_path: str, timestamps: list[float] = None,
                   intensity: float = 1.1, pulse_duration: float = 0.3) -> str:
        """Apply zoom pulses at specified timestamps (or evenly spaced)."""
        if not timestamps:
            # Get video duration and create pulses every 5 seconds
            probe = subprocess.run(
                ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", video_path],
                capture_output=True, text=True,
            )
            duration = float(probe.stdout.strip())
            timestamps = [i for i in range(5, int(duration), 5)]

        if not timestamps:
            return video_path

        # Build zoom expression that pulses at each timestamp
        zoom_parts = []
        for t in timestamps:
            # Smooth pulse: zoom in and out over pulse_duration
            zoom_parts.append(
                f"if(between(t,{t},{t+pulse_duration}),"
                f"1+({intensity-1})*sin((t-{t})/{pulse_duration}*PI),0)"
            )

        zoom_expr = "+".join(zoom_parts)
        # Total zoom = 1 + sum of all pulse contributions
        full_expr = f"1+{zoom_expr}" if zoom_parts else "1"

        output = os.path.join(tempfile.gettempdir(),
                             f"ve_{Path(video_path).stem}_zoompulse.mp4")
        cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-vf", (
                f"scale=iw*2:ih*2,"
                f"zoompan=z='{full_expr}':"
                f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
                f"d=1:s=iw/2xih/2:fps=30"
            ),
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "copy",
            output,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            # Fallback: return original if filter too complex
            return video_path
        return output

    def shake(self, video_path: str, segments: list[tuple[float, float]] = None,
              intensity: str = "medium") -> str:
        """Apply camera shake effect to specified segments."""
        intensity_map = {
            "light": (2, 2),
            "medium": (5, 5),
            "heavy": (10, 10),
        }
        dx, dy = intensity_map.get(intensity, (5, 5))

        # If no segments specified, apply to whole video
        enable = "1"
        if segments:
            conditions = [f"between(t,{s},{e})" for s, e in segments]
            enable = "+".join(conditions)

        output = os.path.join(tempfile.gettempdir(),
                             f"ve_{Path(video_path).stem}_shake.mp4")
        cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-vf", (
                f"crop=iw-{dx*2}:ih-{dy*2}:"
                f"({dx}+{dx}*random(1)*({enable})):"
                f"({dy}+{dy}*random(2)*({enable})),"
                f"scale=iw+{dx*2}:ih+{dy*2}"
            ),
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "copy",
            output,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return video_path
        return output

    def blur_background(self, video_path: str, face_regions: list = None,
                        blur_strength: int = 20) -> str:
        """Blur everything outside face/subject region."""
        if not face_regions:
            # Apply general background blur (center focus)
            output = os.path.join(tempfile.gettempdir(),
                                 f"ve_{Path(video_path).stem}_blur.mp4")
            cmd = [
                "ffmpeg", "-y", "-i", video_path,
                "-vf", (
                    f"split[original][blurred];"
                    f"[blurred]boxblur={blur_strength}[bg];"
                    f"[bg][original]overlay=(W-w)/2:(H-h)/2:"
                    f"shortest=1"
                ),
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "copy",
                output,
            ]
        else:
            # Blur around face regions
            avg_x = sum(f.x for f in face_regions) // len(face_regions)
            avg_y = sum(f.y for f in face_regions) // len(face_regions)
            avg_w = sum(f.w for f in face_regions) // len(face_regions)
            avg_h = sum(f.h for f in face_regions) // len(face_regions)

            # Expand region
            avg_w = int(avg_w * 2)
            avg_h = int(avg_h * 2.5)
            avg_x = max(0, avg_x - avg_w // 4)
            avg_y = max(0, avg_y - avg_h // 4)

            output = os.path.join(tempfile.gettempdir(),
                                 f"ve_{Path(video_path).stem}_blur.mp4")
            cmd = [
                "ffmpeg", "-y", "-i", video_path,
                "-vf", f"boxblur={blur_strength}:enable='1'",
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "copy",
                output,
            ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return video_path
        return output

    def vignette(self, video_path: str, intensity: float = 0.3) -> str:
        """Apply vignette effect."""
        output = os.path.join(tempfile.gettempdir(),
                             f"ve_{Path(video_path).stem}_vignette.mp4")
        # FFmpeg vignette angle: PI/5 is subtle, PI/2 is strong
        angle = 0.3 + (intensity * 1.0)  # Map 0-1 to subtle-strong

        cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-vf", f"vignette=angle={angle}:mode=forward",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "copy",
            output,
        ]
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        return output

    def glitch(self, video_path: str, timestamps: list[float] = None,
               glitch_duration: float = 0.3) -> str:
        """Apply glitch effect at specified timestamps."""
        if not timestamps:
            return video_path

        # Build enable expression
        conditions = [
            f"between(t,{t},{t+glitch_duration})" for t in timestamps
        ]
        enable = "+".join(conditions)

        output = os.path.join(tempfile.gettempdir(),
                             f"ve_{Path(video_path).stem}_glitch.mp4")

        # Simulate glitch with color channel shift and noise
        cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-vf", (
                f"rgbashift=rh=-5:bh=5:enable='{enable}',"
                f"noise=alls=40:allf=t:enable='{enable}',"
                f"hue=s=0:enable='{enable}'"
            ),
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "copy",
            output,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            # Fallback without rgbashift
            cmd_fallback = [
                "ffmpeg", "-y", "-i", video_path,
                "-vf", f"noise=alls=50:allf=t:enable='{enable}'",
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "copy",
                output,
            ]
            result = subprocess.run(cmd_fallback, capture_output=True, text=True)
            if result.returncode != 0:
                return video_path
        return output

    def particles(self, video_path: str, particle_type: str = "sparkle",
                  opacity: float = 0.5) -> str:
        """Overlay particle effect. Uses generated noise as substitute for pre-rendered particles."""
        output = os.path.join(tempfile.gettempdir(),
                             f"ve_{Path(video_path).stem}_particles.mp4")

        # Generate a light particle-like noise overlay
        if particle_type == "sparkle":
            noise_filter = f"noise=alls=80:allf=t"
        elif particle_type == "snow":
            noise_filter = f"noise=alls=40:allf=t"
        else:
            noise_filter = f"noise=alls=60:allf=t"

        cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-vf", (
                f"split[a][b];"
                f"[b]{noise_filter},colorkey=black:0.3:0.2,"
                f"format=rgba,colorchannelmixer=aa={opacity}[particles];"
                f"[a][particles]overlay=shortest=1"
            ),
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "copy",
            output,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return video_path
        return output


if __name__ == "__main__":
    print("Effects module — available effects:")
    print("  zoom_pulse, shake, blur_background, vignette, glitch, particles")
