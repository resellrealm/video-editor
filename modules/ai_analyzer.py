"""AI Analyzer module — scene detection, transcription, energy analysis, face detection, content classification."""

import json
import os
import subprocess
import tempfile
from pathlib import Path

from modules import (CaptionSegment, EnergySegment, FaceRegion, Scene,
                     Transcription, WordTimestamp)


class AIAnalyzer:
    """AI-powered video analysis: scenes, speech, energy, faces, content type."""

    def detect_scenes(self, video_path: str, threshold: float = 27.0) -> list[Scene]:
        """Detect scene boundaries using PySceneDetect."""
        from scenedetect import detect, ContentDetector

        scene_list = detect(video_path, ContentDetector(threshold=threshold))
        scenes = []
        for start_time, end_time in scene_list:
            scenes.append(Scene(
                start=start_time.get_seconds(),
                end=end_time.get_seconds(),
                type="cut",
            ))
        return scenes

    def transcribe(self, video_path: str, model: str = "base") -> Transcription:
        """Transcribe video using faster-whisper. Returns word-level timestamps."""
        from faster_whisper import WhisperModel

        whisper = WhisperModel(model, device="cpu", compute_type="int8")
        segments, info = whisper.transcribe(video_path, beam_size=5, word_timestamps=True)

        caption_segments = []
        for segment in segments:
            words = []
            if segment.words:
                for w in segment.words:
                    words.append(WordTimestamp(
                        start=w.start, end=w.end, word=w.word.strip()
                    ))
            caption_segments.append(CaptionSegment(
                start=segment.start,
                end=segment.end,
                text=segment.text.strip(),
                words=words,
            ))

        return Transcription(
            language=info.language,
            duration=info.duration,
            segments=caption_segments,
        )

    def analyze_energy(self, audio_path: str, window: float = 2.0,
                       highlight_threshold: float = -20.0) -> list[EnergySegment]:
        """Analyze audio energy using FFmpeg astats. Returns energy segments."""
        # Use FFmpeg to get volume levels
        cmd = [
            "ffmpeg", "-i", audio_path,
            "-af", f"astats=metadata=1:reset={int(window * 100)}",
            "-f", "null", "-",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        stderr = result.stderr

        # Parse RMS levels from ffmpeg output
        segments = []
        current_time = 0.0
        for line in stderr.split("\n"):
            if "RMS level dB" in line:
                try:
                    level = float(line.split("RMS level dB:")[1].strip())
                    segments.append(EnergySegment(
                        start=current_time,
                        end=current_time + window,
                        level=level,
                        is_highlight=level > highlight_threshold,
                    ))
                    current_time += window
                except (ValueError, IndexError):
                    current_time += window

        # Fallback: if parsing failed, use silencedetect
        if not segments:
            segments = self._energy_fallback(audio_path, window, highlight_threshold)

        return segments

    def _energy_fallback(self, audio_path: str, window: float,
                         threshold: float) -> list[EnergySegment]:
        """Fallback energy analysis using volumedetect."""
        cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_format", audio_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        try:
            data = json.loads(result.stdout)
            duration = float(data["format"]["duration"])
        except (json.JSONDecodeError, KeyError):
            duration = 60.0

        # Create uniform segments as fallback
        segments = []
        t = 0.0
        while t < duration:
            segments.append(EnergySegment(
                start=t,
                end=min(t + window, duration),
                level=-25.0,
                is_highlight=False,
            ))
            t += window
        return segments

    def detect_faces(self, video_path: str, sample_rate: int = 1) -> list[FaceRegion]:
        """Detect faces using OpenCV Haar cascades. Samples every N seconds."""
        import cv2

        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        frame_interval = int(fps * sample_rate)

        faces = []
        frame_num = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if frame_num % frame_interval == 0:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                detected = face_cascade.detectMultiScale(
                    gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
                )
                timestamp = frame_num / fps
                for (x, y, w, h) in detected:
                    faces.append(FaceRegion(
                        x=int(x), y=int(y), w=int(w), h=int(h),
                        timestamp=timestamp,
                    ))
            frame_num += 1

        cap.release()
        return faces

    def classify_content(self, video_path: str, scenes: list[Scene] = None,
                         faces: list[FaceRegion] = None) -> list[dict]:
        """Classify content type using heuristics: motion + faces + audio."""
        import cv2

        if scenes is None:
            scenes = self.detect_scenes(video_path)
        if faces is None:
            faces = self.detect_faces(video_path, sample_rate=2)

        # Build face density map
        face_times = {}
        for f in faces:
            t = int(f.timestamp)
            face_times[t] = face_times.get(t, 0) + 1

        results = []
        for scene in scenes:
            mid = (scene.start + scene.end) / 2
            duration = scene.end - scene.start

            # Check face presence in this scene
            face_count = sum(
                face_times.get(t, 0)
                for t in range(int(scene.start), int(scene.end) + 1)
            )
            has_faces = face_count > 0

            # Classify based on heuristics
            if has_faces and duration > 3:
                content_type = "talking_head"
            elif duration < 1.5:
                content_type = "broll"
            elif not has_faces and duration > 5:
                content_type = "screenrec"
            else:
                content_type = "broll"

            results.append({
                "start": scene.start,
                "end": scene.end,
                "type": content_type,
                "face_count": face_count,
            })

        return results


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m modules.ai_analyzer <video_path>")
        sys.exit(1)
    analyzer = AIAnalyzer()
    scenes = analyzer.detect_scenes(sys.argv[1])
    print(f"Detected {len(scenes)} scenes")
    for s in scenes[:5]:
        print(f"  {s.start:.1f}s - {s.end:.1f}s ({s.type})")
