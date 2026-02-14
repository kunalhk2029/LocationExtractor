import base64
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from django.conf import settings

from .models import ReelJob


@dataclass
class LocationResult:
    city: str
    country: str
    confidence: Optional[float]
    reasoning: str
    raw_text: str


class ProcessingError(RuntimeError):
    pass


def _run_ffmpeg(args: List[str]) -> None:
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        raise ProcessingError(f"ffmpeg failed: {result.stderr.strip()}")


def _run_ffprobe(args: List[str]) -> str:
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        raise ProcessingError(f"ffprobe failed: {result.stderr.strip()}")
    return result.stdout


def _has_audio_stream(video_path: Path) -> bool:
    args = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "a:0",
        "-show_entries",
        "stream=codec_type",
        "-of",
        "default=nw=1:nk=1",
        str(video_path),
    ]
    try:
        output = _run_ffprobe(args)
    except FileNotFoundError as exc:
        raise ProcessingError("ffprobe is required to inspect audio streams but was not found in PATH.") from exc
    return bool(output.strip())


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def extract_audio(video_path: Path, work_dir: Path) -> Optional[Path]:
    if not _has_audio_stream(video_path):
        return None
    audio_path = work_dir / "audio.wav"
    args = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        str(audio_path),
    ]
    try:
        _run_ffmpeg(args)
    except FileNotFoundError as exc:
        raise ProcessingError("ffmpeg is required to extract audio but was not found in PATH.") from exc
    return audio_path if audio_path.exists() else None


def extract_frames(video_path: Path, work_dir: Path, fps: float, max_frames: int) -> List[Path]:
    frames_dir = _ensure_dir(work_dir / "frames")
    pattern = frames_dir / "frame_%03d.jpg"
    args = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-vf",
        f"fps={fps}",
    ]
    if max_frames > 0:
        args += ["-frames:v", str(max_frames)]
    args.append(str(pattern))
    try:
        _run_ffmpeg(args)
    except FileNotFoundError as exc:
        raise ProcessingError("ffmpeg is required to extract frames but was not found in PATH.") from exc

    frames = sorted(frames_dir.glob("frame_*.jpg"))
    if max_frames > 0:
        frames = frames[:max_frames]
    return frames


def _encode_image(path: Path) -> str:
    data = path.read_bytes()
    return base64.b64encode(data).decode("utf-8")


def transcribe_audio(audio_path: Path) -> str:
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        raise ProcessingError("OPENAI_API_KEY is not set.")

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise ProcessingError("openai package is not installed.") from exc

    client = OpenAI(api_key=api_key)
    with audio_path.open("rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model=settings.OPENAI_TRANSCRIPTION_MODEL,
            file=audio_file,
        )
    return transcription.text or ""


def _extract_json_blob(text: str) -> Optional[str]:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    return text[start : end + 1]


def infer_location(frames: List[Path], transcript: str) -> LocationResult:
    api_key = settings.OPENAI_API_KEY
    if not api_key:
     raise ProcessingError("OPENAI_API_KEY is not set.")

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise ProcessingError("openai package is not installed.") from exc

    client = OpenAI(api_key=api_key)

    prompt = (
        "You are a location inference assistant. Use visual cues from the frames and the "
        "audio transcript to infer the city and country shown or referenced in the reel. "
        "Return JSON with keys: city, country, confidence (0-1), reasoning. "
        "If you are unsure, use null for city or country and lower confidence."
    )

    content = [{"type": "input_text", "text": f"{prompt}\n\nTranscript:\n{transcript}"}]

    for frame in frames:
        base64_image = _encode_image(frame)
        content.append(
            {
                "type": "input_image",
                "image_url": f"data:image/jpeg;base64,{base64_image}",
            }
        )

    response = client.responses.create(
        model=settings.OPENAI_MODEL,
        input=[{"role": "user", "content": content}],
    )

    output_text = response.output_text or ""
    json_blob = _extract_json_blob(output_text)

    city = ""
    country = ""
    confidence = None
    reasoning = output_text.strip()

    if json_blob:
        try:
            data = json.loads(json_blob)
            city = data.get("city") or ""
            country = data.get("country") or ""
            confidence = data.get("confidence")
            reasoning = data.get("reasoning") or reasoning
        except json.JSONDecodeError:
            pass

    return LocationResult(
        city=city,
        country=country,
        confidence=confidence,
        reasoning=reasoning,
        raw_text=output_text,
    )


def process_job(job: ReelJob) -> Tuple[ReelJob, LocationResult]:
    job.status = ReelJob.Status.PROCESSING
    job.error_message = ""
    job.save(update_fields=["status", "error_message", "updated_at"])

    video_path = Path(job.video_file.path)
    work_dir = _ensure_dir(Path(settings.MEDIA_ROOT) / "reels" / "jobs" / str(job.id))

    try:
        frames = extract_frames(
            video_path=video_path,
            work_dir=work_dir,
            fps=settings.REELS_FRAME_FPS,
            max_frames=settings.REELS_MAX_FRAMES,
        )
        if not frames:
            raise ProcessingError("No frames were extracted from the video.")
        media_root = Path(settings.MEDIA_ROOT)
        frames_meta = [
            {"path": str(frame.relative_to(media_root)), "size": frame.stat().st_size}
            for frame in frames
        ]

        audio_path = extract_audio(video_path=video_path, work_dir=work_dir)
        transcript = ""
        if audio_path and audio_path.exists():
            transcript = transcribe_audio(audio_path)

        result = infer_location(frames=frames, transcript=transcript)

        job.status = ReelJob.Status.DONE
        job.result_city = result.city
        job.result_country = result.country
        job.confidence = result.confidence
        job.reasoning = result.reasoning
        job.audio_transcript = transcript
        job.raw_response = result.raw_text
        job.frames_meta = frames_meta
        job.save()
        return job, result
    except Exception as exc:  # noqa: BLE001
        job.status = ReelJob.Status.ERROR
        job.error_message = str(exc)
        job.save(update_fields=["status", "error_message", "updated_at"])
        raise
