"""Branding module — watermarks, intros, outros, lower thirds, CTAs, color grading."""

import os
import subprocess
import tempfile
from pathlib import Path

from modules.presets import Preset


class Branding:
    """Apply brand elements to videos."""

    def add_watermark(self, video_path: str, logo_path: str,
                      position: str = "bottom-right", opacity: float = 0.7) -> str:
        """Overlay a logo/watermark on the video."""
        if not logo_path or not os.path.exists(logo_path):
            return video_path

        pos_map = {
            "bottom-right": "overlay=W-w-20:H-h-20",
            "bottom-left": "overlay=20:H-h-20",
            "top-right": "overlay=W-w-20:20",
            "top-left": "overlay=20:20",
            "center": "overlay=(W-w)/2:(H-h)/2",
        }
        overlay = pos_map.get(position, pos_map["bottom-right"])

        output = os.path.join(tempfile.gettempdir(),
                             f"ve_{Path(video_path).stem}_watermark.mp4")
        cmd = [
            "ffmpeg", "-y", "-i", video_path, "-i", logo_path,
            "-filter_complex",
            f"[1:v]format=rgba,colorchannelmixer=aa={opacity},"
            f"scale=iw*0.15:-1[logo];[0:v][logo]{overlay}",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "copy",
            output,
        ]
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        return output

    def generate_intro(self, preset: Preset, duration: float = 3,
                       width: int = 1080, height: int = 1920) -> str:
        """Generate a branded intro video from preset colors and text."""
        output = os.path.join(tempfile.gettempdir(), f"ve_intro_{preset.name}.mp4")
        bg_color = preset.colors.get("background", "#000000")
        text_color = preset.colors.get("text", "#FFFFFF")
        app_name = preset.name.replace("-ad", "").replace("-", " ").title()

        # Create color background with animated text
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c={bg_color}:s={width}x{height}:d={duration}:r=30",
            "-vf", (
                f"drawtext=text='{app_name}':"
                f"fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
                f"fontsize=72:fontcolor={text_color}:"
                f"x=(w-text_w)/2:y=(h-text_h)/2-40:"
                f"alpha='if(lt(t,0.8),t/0.8,1)'"
                + (
                    f",drawtext=text='{preset.cta_text}':"
                    f"fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:"
                    f"fontsize=36:fontcolor={text_color}:"
                    f"x=(w-text_w)/2:y=(h/2)+40:"
                    f"alpha='if(lt(t,1.2),0,if(lt(t,1.8),(t-1.2)/0.6,1))'"
                    if preset.cta_text else ""
                )
            ),
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-pix_fmt", "yuv420p",
            output,
        ]
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        return output

    def generate_outro(self, preset: Preset, duration: float = 4,
                       width: int = 1080, height: int = 1920) -> str:
        """Generate a branded outro video."""
        output = os.path.join(tempfile.gettempdir(), f"ve_outro_{preset.name}.mp4")
        bg_color = preset.colors.get("background", "#000000")
        text_color = preset.colors.get("text", "#FFFFFF")
        accent = preset.colors.get("accent", "#3B82F6")

        cta = preset.cta_text or "Thanks for watching!"

        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c={bg_color}:s={width}x{height}:d={duration}:r=30",
            "-vf", (
                f"drawtext=text='{cta}':"
                f"fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
                f"fontsize=64:fontcolor={accent}:"
                f"x=(w-text_w)/2:y=(h-text_h)/2-40:"
                f"alpha='if(lt(t,0.5),t/0.5,1)',"
                f"drawtext=text='Download Now':"
                f"fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:"
                f"fontsize=36:fontcolor={text_color}:"
                f"x=(w-text_w)/2:y=(h/2)+50:"
                f"alpha='if(lt(t,1.0),0,if(lt(t,1.5),(t-1.0)/0.5,1))'"
            ),
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-pix_fmt", "yuv420p",
            output,
        ]
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        return output

    def add_lower_third(self, video_path: str, text: str, preset: Preset,
                        duration: float = 5, start_time: float = 2) -> str:
        """Add a lower-third text overlay."""
        output = os.path.join(tempfile.gettempdir(),
                             f"ve_{Path(video_path).stem}_lt.mp4")
        bg_color = preset.colors.get("primary", "#111827")
        text_color = preset.colors.get("text", "#FFFFFF")

        cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-vf", (
                f"drawbox=x=0:y=ih*0.82:w=iw:h=ih*0.08:color={bg_color}@0.7:t=fill:"
                f"enable='between(t,{start_time},{start_time+duration})',"
                f"drawtext=text='{text}':"
                f"fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
                f"fontsize=32:fontcolor={text_color}:"
                f"x=(w-text_w)/2:y=h*0.84:"
                f"enable='between(t,{start_time},{start_time+duration})':"
                f"alpha='if(lt(t-{start_time},0.3),(t-{start_time})/0.3,"
                f"if(gt(t,{start_time+duration-0.3}),({start_time+duration}-t)/0.3,1))'"
            ),
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "copy",
            output,
        ]
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        return output

    def add_cta(self, video_path: str, text: str, preset: Preset,
                position: str = "bottom", duration: float = 4) -> str:
        """Add a call-to-action overlay at the end of the video."""
        # Get video duration
        probe = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", video_path],
            capture_output=True, text=True,
        )
        vid_duration = float(probe.stdout.strip())
        start = max(0, vid_duration - duration)

        output = os.path.join(tempfile.gettempdir(),
                             f"ve_{Path(video_path).stem}_cta.mp4")
        accent = preset.colors.get("accent", "#3B82F6")

        y_pos = "h*0.85" if position == "bottom" else "h*0.1"

        cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-vf", (
                f"drawtext=text='{text}':"
                f"fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
                f"fontsize=40:fontcolor={accent}:"
                f"borderw=3:bordercolor=black:"
                f"x=(w-text_w)/2:y={y_pos}:"
                f"enable='between(t,{start},{vid_duration})':"
                f"alpha='if(lt(t-{start},0.5),(t-{start})/0.5,1)'"
            ),
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "copy",
            output,
        ]
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        return output

    def color_grade(self, video_path: str, preset: Preset) -> str:
        """Apply color grading from preset settings."""
        grade = preset.color_grade
        if not grade:
            return video_path

        sat = grade.get("saturation", 1.0)
        contrast = grade.get("contrast", 1.0)
        brightness = grade.get("brightness", 1.0)
        temp = grade.get("temperature", 0)

        filters = []
        # Saturation and contrast via eq filter
        filters.append(f"eq=saturation={sat}:contrast={contrast}:brightness={brightness - 1.0}")

        # Temperature via colorbalance
        if temp != 0:
            if temp > 0:
                filters.append(f"colorbalance=rs={temp/100}:gs=0:bs=-{temp/100}")
            else:
                filters.append(f"colorbalance=rs={temp/100}:gs=0:bs={-temp/100}")

        output = os.path.join(tempfile.gettempdir(),
                             f"ve_{Path(video_path).stem}_graded.mp4")
        cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-vf", ",".join(filters),
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "copy",
            output,
        ]
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        return output


if __name__ == "__main__":
    print("Branding module — available operations:")
    print("  add_watermark, generate_intro, generate_outro,")
    print("  add_lower_third, add_cta, color_grade")
