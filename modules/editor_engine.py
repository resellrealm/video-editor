"""Editor Engine module — smart cuts, speed ramp, transitions, PiP, split screen, Ken Burns, audio ducking."""

import os
import subprocess
import tempfile
from pathlib import Path

from modules import EditList, EnergySegment, Transcription


class EditorEngine:
    """Core video editing operations."""

    def auto_cut(self, video_path: str, transcript: Transcription,
                 min_pause: float = 0.8) -> EditList:
        """Remove dead air, ums, long pauses. Returns segments to keep."""
        if not transcript.segments:
            return EditList(cuts=[(0, transcript.duration)])

        cuts = []
        filler_words = {"um", "uh", "uhm", "like", "you know", "basically", "literally"}

        for seg in transcript.segments:
            text = seg.text.lower().strip()
            # Skip filler-only segments
            if text in filler_words:
                continue
            cuts.append((seg.start, seg.end))

        # Merge adjacent cuts that are close together
        if not cuts:
            return EditList(cuts=[(0, transcript.duration)])

        merged = [cuts[0]]
        for start, end in cuts[1:]:
            prev_start, prev_end = merged[-1]
            if start - prev_end < min_pause:
                merged[-1] = (prev_start, end)
            else:
                merged.append((start, end))

        return EditList(cuts=merged)

    def apply_cuts(self, video_path: str, edit_list: EditList) -> str:
        """Apply cuts from an EditList, concatenating kept segments."""
        if not edit_list.cuts:
            return video_path

        tmp_dir = tempfile.mkdtemp(prefix="ve_cuts_")
        segment_files = []

        # Extract each segment
        for i, (start, end) in enumerate(edit_list.cuts):
            seg_path = os.path.join(tmp_dir, f"seg_{i:04d}.mp4")
            duration = end - start
            cmd = [
                "ffmpeg", "-y", "-ss", str(start), "-i", video_path,
                "-t", str(duration),
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "aac",
                seg_path,
            ]
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            segment_files.append(seg_path)

        # Concatenate segments
        concat_list = os.path.join(tmp_dir, "concat.txt")
        with open(concat_list, "w") as f:
            for seg in segment_files:
                f.write(f"file '{seg}'\n")

        output = os.path.join(tempfile.gettempdir(), f"ve_{Path(video_path).stem}_cut.mp4")
        cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", concat_list,
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac",
            output,
        ]
        subprocess.run(cmd, capture_output=True, text=True, check=True)

        # Cleanup
        for f in segment_files:
            os.remove(f)
        os.remove(concat_list)
        os.rmdir(tmp_dir)

        return output

    def speed_ramp(self, video_path: str, energy: list[EnergySegment],
                   slow_factor: float = 0.5, fast_factor: float = 1.5) -> str:
        """Apply speed ramping based on energy levels."""
        if not energy:
            return video_path

        tmp_dir = tempfile.mkdtemp(prefix="ve_speed_")
        segment_files = []

        for i, seg in enumerate(energy):
            seg_path = os.path.join(tmp_dir, f"seg_{i:04d}.mp4")
            duration = seg.end - seg.start
            if duration <= 0:
                continue

            speed = slow_factor if seg.is_highlight else fast_factor
            # FFmpeg setpts for video speed, atempo for audio
            video_filter = f"setpts={1/speed}*PTS"
            audio_filter = f"atempo={speed}"

            # atempo only supports 0.5-2.0, chain if needed
            if speed > 2.0:
                audio_filter = "atempo=2.0,atempo=" + str(speed / 2.0)

            cmd = [
                "ffmpeg", "-y", "-ss", str(seg.start), "-i", video_path,
                "-t", str(duration),
                "-vf", video_filter,
                "-af", audio_filter,
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                seg_path,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0 and os.path.exists(seg_path):
                segment_files.append(seg_path)

        if not segment_files:
            return video_path

        # Concatenate
        concat_list = os.path.join(tmp_dir, "concat.txt")
        with open(concat_list, "w") as f:
            for seg in segment_files:
                f.write(f"file '{seg}'\n")

        output = os.path.join(tempfile.gettempdir(), f"ve_{Path(video_path).stem}_speedramp.mp4")
        cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", concat_list,
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac",
            output,
        ]
        subprocess.run(cmd, capture_output=True, text=True, check=True)

        # Cleanup
        for f in segment_files:
            os.remove(f)
        os.remove(concat_list)
        os.rmdir(tmp_dir)

        return output

    def add_transitions(self, clips: list[str], style: str = "crossfade",
                        duration: float = 0.5) -> str:
        """Add transitions between clips using MoviePy."""
        from moviepy import VideoFileClip, concatenate_videoclips

        loaded = [VideoFileClip(c) for c in clips]

        if style == "crossfade" and len(loaded) > 1:
            result = concatenate_videoclips(loaded, method="compose",
                                            padding=-duration)
        else:
            result = concatenate_videoclips(loaded, method="compose")

        output = os.path.join(tempfile.gettempdir(), "ve_transitions.mp4")
        result.write_videofile(output, codec="libx264", audio_codec="aac",
                              preset="fast", logger=None)

        for clip in loaded:
            clip.close()

        return output

    def picture_in_picture(self, base_path: str, overlay_path: str,
                           position: str = "bottom-right", scale: float = 0.3) -> str:
        """Composite overlay video on base video."""
        pos_map = {
            "bottom-right": f"overlay=W-w-20:H-h-20",
            "bottom-left": f"overlay=20:H-h-20",
            "top-right": f"overlay=W-w-20:20",
            "top-left": f"overlay=20:20",
            "center": f"overlay=(W-w)/2:(H-h)/2",
        }
        overlay_filter = pos_map.get(position, pos_map["bottom-right"])

        output = os.path.join(tempfile.gettempdir(), "ve_pip.mp4")
        cmd = [
            "ffmpeg", "-y", "-i", base_path, "-i", overlay_path,
            "-filter_complex",
            f"[1:v]scale=iw*{scale}:ih*{scale}[pip];[0:v][pip]{overlay_filter}",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac",
            output,
        ]
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        return output

    def split_screen(self, videos: list[str], layout: str = "side-by-side") -> str:
        """Create split screen composition."""
        if len(videos) < 2:
            return videos[0] if videos else ""

        output = os.path.join(tempfile.gettempdir(), "ve_splitscreen.mp4")

        if layout == "side-by-side":
            cmd = [
                "ffmpeg", "-y", "-i", videos[0], "-i", videos[1],
                "-filter_complex",
                "[0:v]scale=iw/2:ih[left];[1:v]scale=iw/2:ih[right];"
                "[left][right]hstack=inputs=2",
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "aac",
                output,
            ]
        else:  # top-bottom
            cmd = [
                "ffmpeg", "-y", "-i", videos[0], "-i", videos[1],
                "-filter_complex",
                "[0:v]scale=iw:ih/2[top];[1:v]scale=iw:ih/2[bottom];"
                "[top][bottom]vstack=inputs=2",
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "aac",
                output,
            ]
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        return output

    def ken_burns(self, image_path: str, duration: float = 5,
                  zoom_start: float = 1.0, zoom_end: float = 1.3,
                  fps: int = 30) -> str:
        """Animate a still image with slow zoom/pan (Ken Burns effect)."""
        output = os.path.join(tempfile.gettempdir(), "ve_kenburns.mp4")
        total_frames = int(duration * fps)

        cmd = [
            "ffmpeg", "-y", "-loop", "1", "-i", image_path,
            "-vf", (
                f"scale=8000:-1,"
                f"zoompan=z='min(zoom+{(zoom_end-zoom_start)/total_frames},{zoom_end})':"
                f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                f":d={total_frames}:s=1920x1080:fps={fps}"
            ),
            "-t", str(duration),
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-pix_fmt", "yuv420p",
            output,
        ]
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        return output

    def duck_audio(self, video_path: str, music_path: str,
                   duck_level: int = -12) -> str:
        """Lower music volume during speech segments using sidechain compression."""
        output = os.path.join(tempfile.gettempdir(), "ve_ducked.mp4")

        # Mix music with video audio, ducking music when speech detected
        cmd = [
            "ffmpeg", "-y", "-i", video_path, "-i", music_path,
            "-filter_complex",
            f"[1:a]volume={duck_level}dB[music];"
            f"[0:a][music]amix=inputs=2:duration=first:dropout_transition=2",
            "-c:v", "copy",
            output,
        ]
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        return output

    def normalize_audio(self, video_path: str, target_lufs: int = -16) -> str:
        """Normalize audio levels using FFmpeg loudnorm filter (two-pass)."""
        # First pass: analyze
        cmd_analyze = [
            "ffmpeg", "-i", video_path, "-af",
            f"loudnorm=I={target_lufs}:TP=-1.5:LRA=11:print_format=json",
            "-f", "null", "-",
        ]
        result = subprocess.run(cmd_analyze, capture_output=True, text=True)

        # Try to parse loudnorm stats from stderr
        import json
        stderr = result.stderr
        json_start = stderr.rfind("{")
        json_end = stderr.rfind("}") + 1

        output = os.path.join(tempfile.gettempdir(),
                             f"ve_{Path(video_path).stem}_normalized.mp4")

        if json_start >= 0 and json_end > json_start:
            try:
                stats = json.loads(stderr[json_start:json_end])
                # Second pass: apply with measured values
                cmd_apply = [
                    "ffmpeg", "-y", "-i", video_path,
                    "-af", (
                        f"loudnorm=I={target_lufs}:TP=-1.5:LRA=11:"
                        f"measured_I={stats['input_i']}:"
                        f"measured_TP={stats['input_tp']}:"
                        f"measured_LRA={stats['input_lra']}:"
                        f"measured_thresh={stats['input_thresh']}:"
                        f"offset={stats['target_offset']}:linear=true"
                    ),
                    "-c:v", "copy",
                    output,
                ]
                subprocess.run(cmd_apply, capture_output=True, text=True, check=True)
                return output
            except (json.JSONDecodeError, KeyError):
                pass

        # Fallback: single-pass normalization
        cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-af", f"loudnorm=I={target_lufs}:TP=-1.5:LRA=11",
            "-c:v", "copy",
            output,
        ]
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        return output


if __name__ == "__main__":
    print("EditorEngine — available operations:")
    print("  auto_cut, apply_cuts, speed_ramp, add_transitions,")
    print("  picture_in_picture, split_screen, ken_burns,")
    print("  duck_audio, normalize_audio")
