#!/usr/bin/env python3
"""
AI Video Editor — REST API server.

Endpoints:
    POST /api/process      — Start video processing job
    GET  /api/jobs/<id>     — Check job status
    GET  /api/presets       — List available presets
    POST /api/upload        — Upload video file
    GET  /api/download/<id>/<filename> — Download output file
"""

import os
import sys
import threading
import time
import traceback
import uuid
from pathlib import Path

VENV_PYTHON = Path(__file__).parent / "venv" / "bin" / "python"
if Path(sys.executable).resolve() != VENV_PYTHON.resolve() and VENV_PYTHON.exists():
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON)] + sys.argv)

from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)

BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}

# In-memory job store
jobs: dict[str, dict] = {}


def _run_job(job_id: str, input_path: str, config: dict):
    """Run video processing in background thread."""
    try:
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["progress"] = 10

        from modules.preprocessor import Preprocessor
        from modules.ai_analyzer import AIAnalyzer
        from modules.editor_engine import EditorEngine
        from modules.branding import Branding
        from modules.captions import Captions
        from modules.exporter import Exporter
        from modules.presets import get_preset

        preprocessor = Preprocessor()
        analyzer = AIAnalyzer()
        engine = EditorEngine()
        branding_mod = Branding()
        captions_mod = Captions()
        exporter = Exporter()

        working_video = input_path
        job_output_dir = str(OUTPUT_DIR / job_id)
        os.makedirs(job_output_dir, exist_ok=True)

        # Load preset
        preset = None
        if config.get("preset"):
            preset = get_preset(config["preset"])

        jobs[job_id]["progress"] = 20

        # Preprocessing
        if config.get("trim_silence") or (preset and preset.trim_silence):
            working_video = preprocessor.trim_silence(working_video)

        crop = config.get("smart_crop")
        if crop:
            ratio_map = {"vertical": "9:16", "square": "1:1", "4:5": "4:5"}
            working_video = preprocessor.crop_aspect(
                working_video, ratio=ratio_map.get(crop, crop)
            )
        elif preset and preset.aspect_ratio != "16:9":
            working_video = preprocessor.crop_aspect(
                working_video, ratio=preset.aspect_ratio
            )

        jobs[job_id]["progress"] = 30

        # Transcription
        transcript = None
        caption_segments = None
        model = config.get("model", "base")
        if config.get("captions", True):
            transcript = analyzer.transcribe(working_video, model=model)

        jobs[job_id]["progress"] = 50

        # Auto-edit
        if config.get("auto_edit") or (preset and preset.auto_edit):
            if transcript:
                edit_list = engine.auto_cut(working_video, transcript)
                if edit_list.cuts:
                    working_video = engine.apply_cuts(working_video, edit_list)

        jobs[job_id]["progress"] = 60

        # Speed ramp
        if config.get("speed_ramp") or (preset and preset.speed_ramp):
            audio_path = preprocessor.extract_audio(working_video)
            energy = analyzer.analyze_energy(audio_path)
            working_video = engine.speed_ramp(working_video, energy)
            if os.path.exists(audio_path):
                os.remove(audio_path)

        # Audio
        if config.get("add_music") and os.path.exists(config["add_music"]):
            working_video = engine.duck_audio(working_video, config["add_music"])
        elif preset and preset.music_path and os.path.exists(preset.music_path):
            working_video = engine.duck_audio(working_video, preset.music_path)

        if config.get("normalize_audio"):
            working_video = engine.normalize_audio(working_video)

        jobs[job_id]["progress"] = 70

        # Captions
        if config.get("captions", True) and transcript:
            caption_style = config.get("caption_style", "tiktok")
            if preset:
                caption_style = preset.caption_style
            caption_segments = captions_mod.generate(
                working_video, style=caption_style, transcript=transcript
            )
            info = preprocessor.analyze(working_video)
            import tempfile
            ass_path = os.path.join(tempfile.gettempdir(), f"ve_{job_id}.ass")
            captions_mod.generate_ass(
                caption_segments, ass_path, style=caption_style,
                video_width=info.width, video_height=info.height
            )
            working_video = captions_mod.burn_captions(working_video, ass_path)

        jobs[job_id]["progress"] = 80

        # Branding
        if preset:
            if preset.color_grade:
                working_video = branding_mod.color_grade(working_video, preset)
            if preset.logo_path and os.path.exists(preset.logo_path):
                working_video = branding_mod.add_watermark(working_video, preset.logo_path)
            if preset.cta_text:
                working_video = branding_mod.add_cta(working_video, preset.cta_text, preset)

        jobs[job_id]["progress"] = 90

        # Export
        output_format = config.get("output_format", "tiktok")
        quality = config.get("quality", "standard")
        output_path = exporter.export(
            working_video, job_output_dir, format=output_format,
            quality=quality, filename="output"
        )

        # Thumbnail
        thumb_path = exporter.generate_thumbnail(working_video, job_output_dir)

        # Subtitles
        srt_path = None
        if caption_segments:
            srt_path = os.path.join(job_output_dir, "captions.srt")
            captions_mod.export_srt(caption_segments, srt_path)

        # Get metadata
        final_info = preprocessor.analyze(output_path)
        file_size = os.path.getsize(output_path) / (1024 * 1024)

        jobs[job_id].update({
            "status": "complete",
            "progress": 100,
            "output": f"/api/download/{job_id}/output.mp4",
            "thumbnail": f"/api/download/{job_id}/{Path(thumb_path).name}" if thumb_path else None,
            "subtitles": f"/api/download/{job_id}/captions.srt" if srt_path else None,
            "metadata": {
                "duration": final_info.duration,
                "resolution": f"{final_info.width}x{final_info.height}",
                "captions_count": len(caption_segments) if caption_segments else 0,
                "file_size_mb": round(file_size, 1),
            },
        })

    except Exception as e:
        jobs[job_id].update({
            "status": "failed",
            "error": str(e),
            "traceback": traceback.format_exc(),
        })


@app.route("/api/process", methods=["POST"])
def process():
    """Start a video processing job."""
    data = request.get_json()
    if not data or "input" not in data:
        return jsonify({"error": "Missing 'input' field"}), 400

    input_path = data["input"]
    if not os.path.exists(input_path):
        return jsonify({"error": f"File not found: {input_path}"}), 404

    job_id = uuid.uuid4().hex[:12]
    config = data.get("options", {})
    if "preset" in data:
        config["preset"] = data["preset"]

    jobs[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "progress": 0,
        "input": input_path,
        "config": config,
        "created_at": time.time(),
    }

    thread = threading.Thread(target=_run_job, args=(job_id, input_path, config), daemon=True)
    thread.start()

    return jsonify({
        "job_id": job_id,
        "status": "processing",
        "status_url": f"/api/jobs/{job_id}",
    }), 202


@app.route("/api/jobs/<job_id>")
def get_job(job_id):
    """Get job status."""
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    # Return safe subset
    safe_fields = ["job_id", "status", "progress", "output", "thumbnail",
                   "subtitles", "metadata", "error"]
    return jsonify({k: job.get(k) for k in safe_fields if k in job})


@app.route("/api/presets")
def get_presets():
    """List available presets."""
    from modules.presets import list_presets
    return jsonify({"presets": list_presets()})


@app.route("/api/upload", methods=["POST"])
def upload():
    """Upload a video file."""
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "No filename"}), 400

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({"error": f"Unsupported format: {ext}"}), 400

    safe_name = f"{uuid.uuid4().hex[:8]}_{secure_filename(file.filename)}"
    upload_path = str(UPLOAD_DIR / safe_name)
    file.save(upload_path)

    return jsonify({
        "path": upload_path,
        "filename": safe_name,
        "size_mb": round(os.path.getsize(upload_path) / (1024 * 1024), 1),
    })


@app.route("/api/download/<job_id>/<filename>")
def download(job_id, filename):
    """Download an output file."""
    job_dir = OUTPUT_DIR / job_id
    if not job_dir.exists():
        return jsonify({"error": "Job output not found"}), 404
    return send_from_directory(str(job_dir), filename, as_attachment=True)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="AI Video Editor API")
    parser.add_argument("--port", type=int, default=8081)
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()
    print(f"API server at http://{args.host}:{args.port}")
    print(f"Docs: POST /api/process, GET /api/jobs/<id>, GET /api/presets")
    app.run(host=args.host, port=args.port, debug=False)
