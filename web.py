#!/usr/bin/env python3
"""Enhanced web UI for the AI Video Editor — upload, preset selection, progress, download, history."""

import json
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

from flask import Flask, request, render_template_string, send_from_directory, redirect, url_for, jsonify
from caption import process_video as caption_process_video, OUTPUT_DIR as CAPTION_OUTPUT_DIR

app = Flask(__name__)

UPLOAD_DIR = Path(__file__).parent / "input"
OUTPUT_DIR = Path(__file__).parent / "output"
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}

# In-memory job tracking
web_jobs: dict[str, dict] = {}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Video Editor</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f0f0f;
            color: #e0e0e0;
            min-height: 100vh;
        }
        .container { max-width: 800px; margin: 0 auto; padding: 40px 20px; }
        h1 {
            font-size: 2rem; margin-bottom: 8px;
            background: linear-gradient(135deg, #ff6b6b, #ffa500);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        .subtitle { color: #888; margin-bottom: 32px; }
        .card {
            background: #1a1a1a; border: 1px solid #333;
            border-radius: 12px; padding: 28px; margin-bottom: 24px;
        }
        label {
            display: block; font-weight: 600; margin-bottom: 6px;
            font-size: 0.9rem; color: #ccc;
        }
        input[type="text"], select {
            width: 100%; padding: 10px 14px;
            border: 1px solid #444; border-radius: 8px;
            background: #222; color: #e0e0e0;
            font-size: 0.95rem; margin-bottom: 16px;
        }
        input[type="file"] {
            width: 100%; padding: 12px;
            border: 2px dashed #444; border-radius: 8px;
            background: #181818; color: #aaa;
            cursor: pointer; margin-bottom: 16px;
        }
        input[type="file"]:hover { border-color: #ff6b6b; }
        .checkbox-row { display: flex; gap: 24px; margin-bottom: 16px; flex-wrap: wrap; }
        .checkbox-row label {
            display: flex; align-items: center; gap: 8px;
            font-weight: 400; cursor: pointer;
        }
        input[type="checkbox"] { width: 18px; height: 18px; accent-color: #ff6b6b; }
        button[type="submit"], .btn {
            width: 100%; padding: 14px;
            background: linear-gradient(135deg, #ff6b6b, #ff8e53);
            border: none; border-radius: 8px;
            color: white; font-size: 1.1rem; font-weight: 700;
            cursor: pointer; transition: opacity 0.2s;
            text-align: center; text-decoration: none; display: block;
        }
        button[type="submit"]:hover, .btn:hover { opacity: 0.9; }
        button[type="submit"]:disabled { opacity: 0.5; cursor: wait; }

        /* Preset cards */
        .preset-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 16px; }
        .preset-card {
            background: #222; border: 2px solid #333; border-radius: 10px;
            padding: 14px; cursor: pointer; text-align: center;
            transition: border-color 0.2s, transform 0.1s;
        }
        .preset-card:hover { border-color: #ff6b6b; transform: scale(1.02); }
        .preset-card.selected { border-color: #ff6b6b; background: #2a1515; }
        .preset-card .name { font-weight: 700; font-size: 0.85rem; margin-bottom: 4px; }
        .preset-card .desc { font-size: 0.75rem; color: #888; }
        .preset-card .swatch {
            width: 24px; height: 24px; border-radius: 50%;
            display: inline-block; margin: 4px 2px;
        }

        /* Progress */
        .progress-container { margin: 24px 0; }
        .progress-bar {
            width: 100%; height: 8px; background: #333;
            border-radius: 4px; overflow: hidden;
        }
        .progress-fill {
            height: 100%; background: linear-gradient(90deg, #ff6b6b, #ffa500);
            border-radius: 4px; transition: width 0.3s;
        }
        .progress-text { text-align: center; margin-top: 8px; color: #888; font-size: 0.9rem; }

        /* Results */
        .result {
            background: #0d2818; border: 1px solid #1a5c30;
            border-radius: 12px; padding: 24px; margin-bottom: 24px;
        }
        .result h2 { color: #4ade80; margin-bottom: 12px; }
        .result a {
            display: inline-block; padding: 10px 20px;
            background: #4ade80; color: #000;
            text-decoration: none; border-radius: 8px;
            font-weight: 600; margin-top: 8px; margin-right: 8px;
        }
        .result a:hover { opacity: 0.8; }
        .error {
            background: #2d0f0f; border: 1px solid #5c1a1a;
            border-radius: 12px; padding: 24px; margin-bottom: 24px;
        }
        .error h2 { color: #f87171; }
        .meta { color: #888; font-size: 0.85rem; margin-top: 8px; }

        /* History */
        .history { margin-top: 32px; }
        .history h2 { margin-bottom: 16px; color: #ccc; }
        .history-item {
            display: flex; justify-content: space-between; align-items: center;
            padding: 12px 16px; background: #1a1a1a; border: 1px solid #333;
            border-radius: 8px; margin-bottom: 8px;
        }
        .history-item .info { flex: 1; }
        .history-item .info .name { font-weight: 600; }
        .history-item .info .meta { font-size: 0.8rem; color: #888; }
        .history-item a {
            padding: 6px 14px; background: #333; color: #e0e0e0;
            text-decoration: none; border-radius: 6px; font-size: 0.85rem;
        }
        .history-item a:hover { background: #444; }

        .tabs { display: flex; gap: 0; margin-bottom: 24px; }
        .tab {
            padding: 10px 24px; background: #1a1a1a; border: 1px solid #333;
            cursor: pointer; color: #888; font-weight: 600; text-decoration: none;
        }
        .tab:first-child { border-radius: 8px 0 0 8px; }
        .tab:last-child { border-radius: 0 8px 8px 0; }
        .tab.active { background: #333; color: #e0e0e0; }

        @media (max-width: 600px) {
            .preset-grid { grid-template-columns: repeat(2, 1fr); }
            .checkbox-row { flex-direction: column; gap: 8px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>AI Video Editor</h1>
        <p class="subtitle">Process, edit, and produce polished videos</p>

        <div class="tabs">
            <a class="tab {{ 'active' if tab == 'editor' else '' }}" href="/">Editor</a>
            <a class="tab {{ 'active' if tab == 'caption' else '' }}" href="/caption">Caption Only</a>
            <a class="tab {{ 'active' if tab == 'history' else '' }}" href="/history">History</a>
        </div>

        {% if result %}
        <div class="result">
            <h2>Done!</h2>
            <p>{{ result.get('captions', 0) }} captions &bull; {{ result.get('size', '?') }} &bull; {{ result.get('preset', 'custom') }}</p>
            {% if result.get('vertical') %}<p class="meta">Format: 9:16 vertical</p>{% endif %}
            <a href="/download/{{ result.filename }}">Download Video</a>
            {% if result.get('srt') %}<a href="/download/{{ result.srt }}">Download SRT</a>{% endif %}
        </div>
        {% endif %}

        {% if error %}
        <div class="error">
            <h2>Error</h2>
            <p>{{ error }}</p>
        </div>
        {% endif %}

        {% if job_id %}
        <div class="card" id="progressCard">
            <h3 style="margin-bottom: 12px;">Processing...</h3>
            <div class="progress-container">
                <div class="progress-bar"><div class="progress-fill" id="progressFill" style="width: 0%"></div></div>
                <div class="progress-text" id="progressText">Starting...</div>
            </div>
        </div>
        <script>
            const jobId = "{{ job_id }}";
            function pollJob() {
                fetch("/api/job-status/" + jobId)
                    .then(r => r.json())
                    .then(data => {
                        document.getElementById("progressFill").style.width = data.progress + "%";
                        document.getElementById("progressText").textContent = data.status + " (" + data.progress + "%)";
                        if (data.status === "complete") {
                            window.location.href = "/?result=" + jobId;
                        } else if (data.status === "failed") {
                            document.getElementById("progressText").textContent = "Failed: " + (data.error || "Unknown error");
                            document.getElementById("progressFill").style.background = "#f87171";
                        } else {
                            setTimeout(pollJob, 2000);
                        }
                    })
                    .catch(() => setTimeout(pollJob, 3000));
            }
            pollJob();
        </script>
        {% endif %}

        {% if not job_id %}
        <form method="POST" enctype="multipart/form-data" id="uploadForm">
            <div class="card">
                <label for="video">Upload Video</label>
                <input type="file" name="video" id="video" accept="video/*" required>

                <label>Preset</label>
                <div class="preset-grid">
                    <div class="preset-card" data-preset="" onclick="selectPreset(this)">
                        <div class="name">None</div>
                        <div class="desc">Custom settings</div>
                    </div>
                    <div class="preset-card" data-preset="park-it-ad" onclick="selectPreset(this)">
                        <div><span class="swatch" style="background:#111827"></span><span class="swatch" style="background:#3B82F6"></span></div>
                        <div class="name">Park-It</div>
                        <div class="desc">Monochrome, clean</div>
                    </div>
                    <div class="preset-card" data-preset="surve-ad" onclick="selectPreset(this)">
                        <div><span class="swatch" style="background:#7C3AED"></span><span class="swatch" style="background:#FCD34D"></span></div>
                        <div class="name">Surve</div>
                        <div class="desc">Colorful, friendly</div>
                    </div>
                    <div class="preset-card" data-preset="nutrio-ad" onclick="selectPreset(this)">
                        <div><span class="swatch" style="background:#065F46"></span><span class="swatch" style="background:#F59E0B"></span></div>
                        <div class="name">Nutrio+</div>
                        <div class="desc">Health, green tones</div>
                    </div>
                    <div class="preset-card" data-preset="tiktok-viral" onclick="selectPreset(this)">
                        <div class="name">TikTok Viral</div>
                        <div class="desc">Fast cuts, zoom</div>
                    </div>
                    <div class="preset-card" data-preset="youtube-short" onclick="selectPreset(this)">
                        <div class="name">YouTube Short</div>
                        <div class="desc">Clean, centered</div>
                    </div>
                    <div class="preset-card" data-preset="instagram-reel" onclick="selectPreset(this)">
                        <div class="name">IG Reel</div>
                        <div class="desc">Sleek, minimal</div>
                    </div>
                </div>
                <input type="hidden" name="preset" id="presetInput" value="">

                <label for="caption_style">Caption Style</label>
                <select name="caption_style" id="caption_style">
                    <option value="tiktok" selected>TikTok (bold, word highlight)</option>
                    <option value="instagram">Instagram (sleek, pink)</option>
                    <option value="youtube">YouTube (clean, centered)</option>
                    <option value="minimal">Minimal (subtle)</option>
                    <option value="bold">Bold (large, green)</option>
                    <option value="karaoke">Karaoke (word-by-word)</option>
                </select>

                <div class="checkbox-row">
                    <label><input type="checkbox" name="auto_edit"> Auto-Edit</label>
                    <label><input type="checkbox" name="trim_silence"> Trim Silence</label>
                    <label><input type="checkbox" name="speed_ramp"> Speed Ramp</label>
                    <label><input type="checkbox" name="smart_crop" value="vertical"> 9:16 Vertical</label>
                    <label><input type="checkbox" name="no_captions"> No Captions</label>
                    <label><input type="checkbox" name="normalize_audio"> Normalize Audio</label>
                </div>

                <label for="title">Title Overlay (optional)</label>
                <input type="text" name="title" id="title" placeholder="Your video title">

                <label for="endcard">End Card Text (optional)</label>
                <input type="text" name="endcard" id="endcard" placeholder="Download Our App">

                <label for="quality">Quality</label>
                <select name="quality" id="quality">
                    <option value="draft">Draft (fast)</option>
                    <option value="standard" selected>Standard</option>
                    <option value="high">High (slow)</option>
                </select>

                <label for="model">Whisper Model</label>
                <select name="model" id="model">
                    <option value="tiny">Tiny (fastest)</option>
                    <option value="base" selected>Base (recommended)</option>
                    <option value="small">Small (more accurate)</option>
                </select>
            </div>

            <button type="submit" id="submitBtn">
                <span>Process Video</span>
            </button>
        </form>
        {% endif %}

        {% if history %}
        <div class="history">
            <h2>Recent Outputs</h2>
            {% for item in history %}
            <div class="history-item">
                <div class="info">
                    <div class="name">{{ item.name }}</div>
                    <div class="meta">{{ item.size }} &bull; {{ item.date }}</div>
                </div>
                <a href="/download/{{ item.name }}">Download</a>
            </div>
            {% endfor %}
        </div>
        {% endif %}
    </div>
    <script>
        function selectPreset(el) {
            document.querySelectorAll('.preset-card').forEach(c => c.classList.remove('selected'));
            el.classList.add('selected');
            document.getElementById('presetInput').value = el.dataset.preset;
        }
        document.getElementById('uploadForm')?.addEventListener('submit', function() {
            document.getElementById('submitBtn').disabled = true;
            document.getElementById('submitBtn').textContent = 'Uploading & processing...';
        });
    </script>
</body>
</html>
"""


def _get_history():
    """Get list of output files for history display."""
    history = []
    if OUTPUT_DIR.exists():
        for f in sorted(OUTPUT_DIR.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
            if f.is_file() and f.suffix == ".mp4":
                stat = f.stat()
                size_mb = stat.st_size / (1024 * 1024)
                import datetime
                date = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                history.append({
                    "name": f.name,
                    "size": f"{size_mb:.1f} MB",
                    "date": date,
                })
        history = history[:20]  # Limit to 20 most recent
    return history


def _process_web_job(job_id: str, upload_path: str, form_data: dict):
    """Background processing for web UI."""
    try:
        web_jobs[job_id]["status"] = "processing"
        web_jobs[job_id]["progress"] = 5

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

        working_video = upload_path
        preset = None
        preset_name = form_data.get("preset", "")

        if preset_name:
            preset = get_preset(preset_name)

        web_jobs[job_id]["progress"] = 15

        # Preprocess
        if form_data.get("trim_silence"):
            working_video = preprocessor.trim_silence(working_video)

        if form_data.get("smart_crop"):
            working_video = preprocessor.crop_aspect(working_video, ratio="9:16")
        elif preset and preset.aspect_ratio != "16:9":
            working_video = preprocessor.crop_aspect(working_video, ratio=preset.aspect_ratio)

        web_jobs[job_id]["progress"] = 30

        # Transcribe
        transcript = None
        caption_segments = None
        model = form_data.get("model", "base")
        no_captions = form_data.get("no_captions", False)

        if not no_captions:
            transcript = analyzer.transcribe(working_video, model=model)

        web_jobs[job_id]["progress"] = 50

        # Auto-edit
        if form_data.get("auto_edit") or (preset and preset.auto_edit):
            if transcript:
                edit_list = engine.auto_cut(working_video, transcript)
                if edit_list.cuts:
                    working_video = engine.apply_cuts(working_video, edit_list)

        web_jobs[job_id]["progress"] = 60

        # Speed ramp
        if form_data.get("speed_ramp") or (preset and preset.speed_ramp):
            audio_path = preprocessor.extract_audio(working_video)
            energy_segs = analyzer.analyze_energy(audio_path)
            working_video = engine.speed_ramp(working_video, energy_segs)
            if os.path.exists(audio_path):
                os.remove(audio_path)

        # Normalize audio
        if form_data.get("normalize_audio"):
            working_video = engine.normalize_audio(working_video)

        web_jobs[job_id]["progress"] = 70

        # Captions
        if not no_captions and transcript:
            caption_style = form_data.get("caption_style", "tiktok")
            if preset:
                caption_style = preset.caption_style
            caption_segments = captions_mod.generate(
                working_video, style=caption_style, transcript=transcript
            )
            info = preprocessor.analyze(working_video)
            import tempfile
            ass_path = os.path.join(tempfile.gettempdir(), f"ve_web_{job_id}.ass")
            captions_mod.generate_ass(
                caption_segments, ass_path, style=caption_style,
                video_width=info.width, video_height=info.height
            )
            working_video = captions_mod.burn_captions(working_video, ass_path)

        web_jobs[job_id]["progress"] = 80

        # Branding
        if preset:
            if preset.color_grade:
                working_video = branding_mod.color_grade(working_video, preset)
            if preset.logo_path and os.path.exists(preset.logo_path):
                working_video = branding_mod.add_watermark(working_video, preset.logo_path)

        # Title/endcard
        title = form_data.get("title")
        endcard = form_data.get("endcard")
        if title or endcard:
            from editor import _apply_text_overlays
            working_video = _apply_text_overlays(working_video, title, endcard)

        web_jobs[job_id]["progress"] = 90

        # Export
        stem = Path(upload_path).stem
        suffix = f"_{preset_name}" if preset_name else "_edited"
        output_filename = f"{stem}{suffix}"

        quality = form_data.get("quality", "standard")
        output_path = exporter.export(
            working_video, str(OUTPUT_DIR), format="tiktok",
            quality=quality, filename=output_filename
        )

        # Also export SRT
        srt_filename = None
        if caption_segments:
            srt_path = str(OUTPUT_DIR / f"{output_filename}.srt")
            captions_mod.export_srt(caption_segments, srt_path)
            srt_filename = f"{output_filename}.srt"

        file_size = os.path.getsize(output_path) / (1024 * 1024)

        web_jobs[job_id].update({
            "status": "complete",
            "progress": 100,
            "result": {
                "filename": Path(output_path).name,
                "size": f"{file_size:.1f} MB",
                "captions": len(caption_segments) if caption_segments else 0,
                "preset": preset_name or "custom",
                "vertical": bool(form_data.get("smart_crop")),
                "srt": srt_filename,
            },
        })

    except Exception as e:
        web_jobs[job_id].update({
            "status": "failed",
            "error": str(e),
        })


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error = None
    job_id = None

    # Check if returning from completed job
    result_job = request.args.get("result")
    if result_job and result_job in web_jobs:
        job = web_jobs[result_job]
        if job["status"] == "complete":
            result = job.get("result")
        elif job["status"] == "failed":
            error = job.get("error", "Processing failed")

    if request.method == "POST":
        file = request.files.get("video")
        if not file or not file.filename:
            error = "Please select a video file."
        else:
            ext = Path(file.filename).suffix.lower()
            if ext not in ALLOWED_EXTENSIONS:
                error = f"Unsupported file type: {ext}"
            else:
                unique_id = uuid.uuid4().hex[:8]
                stem = Path(file.filename).stem
                safe_name = f"{stem}_{unique_id}{ext}"
                upload_path = str(UPLOAD_DIR / safe_name)
                file.save(upload_path)

                job_id = unique_id
                form_data = {
                    "preset": request.form.get("preset", ""),
                    "caption_style": request.form.get("caption_style", "tiktok"),
                    "auto_edit": "auto_edit" in request.form,
                    "trim_silence": "trim_silence" in request.form,
                    "speed_ramp": "speed_ramp" in request.form,
                    "smart_crop": "smart_crop" in request.form,
                    "no_captions": "no_captions" in request.form,
                    "normalize_audio": "normalize_audio" in request.form,
                    "title": request.form.get("title", "").strip() or None,
                    "endcard": request.form.get("endcard", "").strip() or None,
                    "quality": request.form.get("quality", "standard"),
                    "model": request.form.get("model", "base"),
                }

                web_jobs[job_id] = {"status": "queued", "progress": 0}
                thread = threading.Thread(
                    target=_process_web_job,
                    args=(job_id, upload_path, form_data),
                    daemon=True,
                )
                thread.start()

    history = _get_history()
    return render_template_string(HTML_TEMPLATE, tab="editor", result=result, error=error,
                                  job_id=job_id, history=history[:5])


@app.route("/caption", methods=["GET", "POST"])
def caption_only():
    """Original caption-only mode (backwards compatible with old web.py)."""
    result = None
    error = None

    if request.method == "POST":
        file = request.files.get("video")
        if not file or not file.filename:
            error = "Please select a video file."
            return render_template_string(HTML_TEMPLATE, tab="caption", result=result, error=error,
                                          job_id=None, history=[])

        ext = Path(file.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            error = f"Unsupported file type: {ext}"
            return render_template_string(HTML_TEMPLATE, tab="caption", result=result, error=error,
                                          job_id=None, history=[])

        unique_id = uuid.uuid4().hex[:8]
        stem = Path(file.filename).stem
        safe_name = f"{stem}_{unique_id}{ext}"
        upload_path = str(UPLOAD_DIR / safe_name)
        file.save(upload_path)

        title = request.form.get("title", "").strip() or None
        endcard = request.form.get("endcard", "").strip() or None
        vertical = "vertical" in request.form
        trim_silence = "trim_silence" in request.form
        model = request.form.get("model", "base")

        try:
            output_path = caption_process_video(
                upload_path, title=title, endcard=endcard,
                do_trim=trim_silence, vertical=vertical, model_size=model,
            )
            if output_path:
                filename = Path(output_path).name
                size_mb = os.path.getsize(output_path) / (1024 * 1024)
                result = {
                    "filename": filename,
                    "size": f"{size_mb:.1f} MB",
                    "captions": 0,
                    "vertical": vertical,
                    "preset": "caption-only",
                }
            else:
                error = "No output produced."
        except Exception as e:
            error = str(e)

    return render_template_string(HTML_TEMPLATE, tab="caption", result=result, error=error,
                                  job_id=None, history=[])


@app.route("/history")
def history_page():
    history = _get_history()
    return render_template_string(HTML_TEMPLATE, tab="history", result=None, error=None,
                                  job_id=None, history=history)


@app.route("/api/job-status/<job_id>")
def job_status(job_id):
    """Poll endpoint for job progress."""
    job = web_jobs.get(job_id)
    if not job:
        return jsonify({"status": "unknown", "progress": 0})
    return jsonify({
        "status": job.get("status", "unknown"),
        "progress": job.get("progress", 0),
        "error": job.get("error"),
    })


@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(str(OUTPUT_DIR), filename, as_attachment=True)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()
    print(f"AI Video Editor Web UI at http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=False)
