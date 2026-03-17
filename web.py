#!/usr/bin/env python3
"""Simple web UI for the video captioning tool."""

import os
import sys
import uuid
from pathlib import Path

VENV_PYTHON = Path(__file__).parent / "venv" / "bin" / "python"
if Path(sys.executable).resolve() != VENV_PYTHON.resolve() and VENV_PYTHON.exists():
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON)] + sys.argv)

from flask import Flask, request, render_template_string, send_from_directory, redirect, url_for
from caption import process_video, OUTPUT_DIR

app = Flask(__name__)

UPLOAD_DIR = Path(__file__).parent / "input"
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Video Captioner</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f0f0f;
            color: #e0e0e0;
            min-height: 100vh;
        }
        .container {
            max-width: 700px;
            margin: 0 auto;
            padding: 40px 20px;
        }
        h1 {
            font-size: 2rem;
            margin-bottom: 8px;
            background: linear-gradient(135deg, #ff6b6b, #ffa500);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .subtitle { color: #888; margin-bottom: 32px; }
        .card {
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 12px;
            padding: 28px;
            margin-bottom: 24px;
        }
        label {
            display: block;
            font-weight: 600;
            margin-bottom: 6px;
            font-size: 0.9rem;
            color: #ccc;
        }
        input[type="text"], select {
            width: 100%;
            padding: 10px 14px;
            border: 1px solid #444;
            border-radius: 8px;
            background: #222;
            color: #e0e0e0;
            font-size: 0.95rem;
            margin-bottom: 16px;
        }
        input[type="file"] {
            width: 100%;
            padding: 12px;
            border: 2px dashed #444;
            border-radius: 8px;
            background: #181818;
            color: #aaa;
            cursor: pointer;
            margin-bottom: 16px;
        }
        input[type="file"]:hover { border-color: #ff6b6b; }
        .checkbox-row {
            display: flex;
            gap: 24px;
            margin-bottom: 16px;
        }
        .checkbox-row label {
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: 400;
            cursor: pointer;
        }
        input[type="checkbox"] {
            width: 18px;
            height: 18px;
            accent-color: #ff6b6b;
        }
        button[type="submit"] {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #ff6b6b, #ff8e53);
            border: none;
            border-radius: 8px;
            color: white;
            font-size: 1.1rem;
            font-weight: 700;
            cursor: pointer;
            transition: opacity 0.2s;
        }
        button[type="submit"]:hover { opacity: 0.9; }
        button[type="submit"]:disabled { opacity: 0.5; cursor: wait; }
        .result {
            background: #0d2818;
            border: 1px solid #1a5c30;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
        }
        .result h2 { color: #4ade80; margin-bottom: 12px; }
        .result a {
            display: inline-block;
            padding: 10px 20px;
            background: #4ade80;
            color: #000;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
            margin-top: 8px;
        }
        .result a:hover { opacity: 0.8; }
        .error {
            background: #2d0f0f;
            border: 1px solid #5c1a1a;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
        }
        .error h2 { color: #f87171; }
        .meta { color: #888; font-size: 0.85rem; margin-top: 8px; }
        .spinner { display: none; }
        form.loading .spinner { display: inline-block; }
        form.loading button[type="submit"] span { display: none; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Video Captioner</h1>
        <p class="subtitle">Auto-caption videos with TikTok/Reels style subtitles</p>

        {% if result %}
        <div class="result">
            <h2>Done!</h2>
            <p>{{ result.captions }} caption segments &bull; {{ result.size }}</p>
            {% if result.vertical %}<p class="meta">Format: 9:16 vertical</p>{% endif %}
            <a href="/download/{{ result.filename }}">Download Video</a>
        </div>
        {% endif %}

        {% if error %}
        <div class="error">
            <h2>Error</h2>
            <p>{{ error }}</p>
        </div>
        {% endif %}

        <form method="POST" enctype="multipart/form-data" id="uploadForm">
            <div class="card">
                <label for="video">Upload Video</label>
                <input type="file" name="video" id="video" accept="video/*" required>

                <label for="title">Title Overlay (optional)</label>
                <input type="text" name="title" id="title" placeholder="POV you meal prep from home">

                <label for="endcard">End Card Text (optional)</label>
                <input type="text" name="endcard" id="endcard" placeholder="Download Our App">

                <div class="checkbox-row">
                    <label><input type="checkbox" name="vertical"> 9:16 Vertical (TikTok/Reels)</label>
                    <label><input type="checkbox" name="trim_silence"> Trim Silence</label>
                </div>

                <label for="model">Whisper Model</label>
                <select name="model" id="model">
                    <option value="tiny">Tiny (fastest)</option>
                    <option value="base" selected>Base (recommended)</option>
                    <option value="small">Small (more accurate)</option>
                    <option value="medium">Medium (most accurate)</option>
                </select>
            </div>

            <button type="submit" id="submitBtn">
                <span>Caption Video</span>
                <span class="spinner">Processing... (this may take a minute)</span>
            </button>
        </form>
    </div>
    <script>
        document.getElementById('uploadForm').addEventListener('submit', function() {
            this.classList.add('loading');
            document.getElementById('submitBtn').disabled = true;
        });
    </script>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error = None

    if request.method == "POST":
        file = request.files.get("video")
        if not file or not file.filename:
            error = "Please select a video file."
            return render_template_string(HTML_TEMPLATE, result=result, error=error)

        ext = Path(file.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            error = f"Unsupported file type: {ext}. Use: {', '.join(ALLOWED_EXTENSIONS)}"
            return render_template_string(HTML_TEMPLATE, result=result, error=error)

        # Save uploaded file with unique name to avoid collisions
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
            output_path = process_video(
                upload_path,
                title=title,
                endcard=endcard,
                do_trim=trim_silence,
                vertical=vertical,
                model_size=model,
            )
            if output_path:
                filename = Path(output_path).name
                size_mb = os.path.getsize(output_path) / (1024 * 1024)
                # Count captions from the ASS file
                suffix = "_vertical" if vertical else ""
                ass_path = OUTPUT_DIR / f"{Path(upload_path).stem}{suffix}.ass"
                caption_count = 0
                if ass_path.exists():
                    with open(ass_path) as f:
                        caption_count = sum(1 for line in f if line.startswith("Dialogue:"))
                result = {
                    "filename": filename,
                    "size": f"{size_mb:.1f} MB",
                    "captions": caption_count,
                    "vertical": vertical,
                }
            else:
                error = "No output produced. Video may have no speech and no title/endcard set."
        except Exception as e:
            error = str(e)

    return render_template_string(HTML_TEMPLATE, result=result, error=error)


@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(str(OUTPUT_DIR), filename, as_attachment=True)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()
    print(f"🌐 Starting web UI at http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=False)
