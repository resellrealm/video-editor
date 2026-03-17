# Video Captioning Tool

## Usage
- `python caption.py input/video.mp4 --title "POV text" --endcard "Download App" --trim-silence`
- `python caption.py input/video.mp4 --vertical` — 9:16 crop for TikTok/Reels
- `python web.py` — web UI at http://localhost:8080
- Uses faster-whisper (local, free) + ffmpeg
- Venv at ./venv/

## Key Files
- caption.py — main pipeline script
- web.py — Flask web UI for uploads
- input/ — drop videos here
- output/ — captioned videos go here
