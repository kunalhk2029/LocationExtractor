# Reel Locator (Django)

This project uploads a reel video file, extracts frames + audio, transcribes speech, and uses OpenAI to infer a city and country from visual/audio cues.

## Why no direct Instagram download?
Instagram restricts automated scraping and downloading of public reels without authorization. This project intentionally **does not** download from Instagram directly. Upload a video file you own or have permission to use. If you later obtain approved access (e.g., through official APIs), you can add a downloader module to feed files into the same pipeline.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set environment variables:

```bash
export OPENAI_API_KEY="..."
export OPENAI_MODEL="gpt-4o-mini"
export OPENAI_TRANSCRIPTION_MODEL="gpt-4o-mini-transcribe"
```

FFmpeg is required to extract frames and audio:

```bash
brew install ffmpeg  # macOS
# or: sudo apt-get install ffmpeg
```

Run migrations and start the server:

```bash
python manage.py migrate
python manage.py runserver
```

Open `http://127.0.0.1:8000/` and upload a reel video.

## Processing

From the UI, click **Process Now** on a job, or run:

```bash
python manage.py process_reel <job_id>
```

## Notes
- The pipeline samples frames at `REELS_FRAME_FPS` (default 0.5 fps) and caps at `REELS_MAX_FRAMES` (default 12). Adjust via environment variables if needed.
- Location inference is best-effort; if there are no strong cues, it may return empty values.

## Deploy (Render Free)
This repo includes a `render.yaml` for a simple free deploy. It uses a Docker build so `ffmpeg` can be installed reliably.

1) Push this repo to GitHub.
2) Create a new Web Service on Render and pick this repo.
3) Set env vars in Render:
   - `OPENAI_API_KEY` (required)
   - `DJANGO_SECRET_KEY` (auto-generated if you keep `render.yaml`)
   - `DJANGO_DEBUG=0`
   - `DJANGO_ALLOWED_HOSTS=<your-service>.onrender.com`
   - `DJANGO_SERVE_MEDIA=1` (temporary for free testing)
4) Deploy. The Dockerfile runs `collectstatic` at build time and starts Gunicorn + migrations on boot.

Notes:
- Render free services use **ephemeral disk**. Uploaded videos and the SQLite DB will be lost on redeploy or if the service spins down. For persistence, use a paid disk or move uploads to object storage.
- `ffmpeg` is installed during the Render build step so processing works out of the box.
- Serving media from Django is for testing only. For production, serve media from object storage or a CDN.
