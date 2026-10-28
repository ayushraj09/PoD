import hashlib
import logging
import uuid
from pathlib import PurePath

from fastapi import APIRouter, BackgroundTasks, File, Form, Request, UploadFile
from fastapi.responses import JSONResponse

from app import db
from app.config import get_settings
from app.pipeline.checks import InvalidEmail, normalize_email
from app.pipeline.run import process_signup

log = logging.getLogger("pod.intake")
router = APIRouter()

# extension -> content type stored in the bucket
AUDIO_TYPES = {
    "webm": "audio/webm",
    "ogg": "audio/ogg",
    "mp4": "audio/mp4",
    "m4a": "audio/mp4",
    "wav": "audio/wav",
}
MIME_TO_EXT = {"audio/webm": "webm", "video/webm": "webm", "audio/ogg": "ogg",
               "audio/mp4": "mp4", "video/mp4": "mp4", "audio/x-m4a": "m4a",
               "audio/wav": "wav", "audio/x-wav": "wav", "audio/wave": "wav"}


def error(status: int, code: str, **extra) -> JSONResponse:
    return JSONResponse({"error": code, **extra}, status_code=status)


def client_ip(request: Request) -> str:
    # Render appends to X-Forwarded-For without clearing it, so trust the
    # Cloudflare headers first and only then the first X-Forwarded-For entry.
    h = request.headers
    for name in ("true-client-ip", "cf-connecting-ip"):
        if h.get(name):
            return h[name].strip()
    if h.get("x-forwarded-for"):
        return h["x-forwarded-for"].split(",")[0].strip()
    return request.client.host if request.client else ""


def hash_ip(ip: str) -> str:
    return hashlib.sha256((get_settings().ip_hash_salt + ip).encode()).hexdigest()


def audio_ext(upload: UploadFile) -> str | None:
    suffix = PurePath(upload.filename or "").suffix.lstrip(".").lower()
    if suffix in AUDIO_TYPES:
        return suffix
    mime = (upload.content_type or "").split(";")[0].strip().lower()
    return MIME_TO_EXT.get(mime)


def is_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False


@router.post("/v1/signups")
async def create_signup(
    request: Request,
    background_tasks: BackgroundTasks,
    waitlist_slug: str = Form(""),
    email: str = Form(""),
    consent: str = Form(""),
    device_id: str = Form(""),
    audio: UploadFile | None = File(None),
):
    settings = get_settings()

    try:
        email = normalize_email(email, check_dns=settings.check_email_dns)
    except InvalidEmail:
        return error(400, "invalid_email")
    if consent.strip().lower() != "true":
        return error(400, "no_consent")

    audio_bytes, ext = None, None
    if audio is not None and audio.filename:
        ext = audio_ext(audio)
        audio_bytes = await audio.read(settings.max_audio_bytes + 1)
        if ext is None or not audio_bytes or len(audio_bytes) > settings.max_audio_bytes:
            return error(400, "bad_audio")

    waitlist = db.get_waitlist_by_slug(waitlist_slug.strip())
    if not waitlist:
        return error(404, "waitlist_not_found")

    existing = db.find_signup_by_email(waitlist["id"], email)
    if existing:
        return error(409, "already_signed_up", signup_id=existing["id"])

    ip_hash = hash_ip(client_ip(request))
    if db.count_recent_by_ip(waitlist["id"], ip_hash) >= settings.rate_limit_per_hour:
        return error(429, "rate_limited")

    signup_id = str(uuid.uuid4())
    audio_path = None
    if audio_bytes:
        audio_path = f"{waitlist['id']}/{signup_id}.{ext}"
        db.upload_audio(audio_path, audio_bytes, AUDIO_TYPES[ext])

    try:
        db.insert_signup({
            "id": signup_id,
            "waitlist_id": waitlist["id"],
            "email": email,
            "consent": True,
            "audio_path": audio_path,
            "device_id": device_id.strip() or None,
            "ip_hash": ip_hash,
            "user_agent": (request.headers.get("user-agent") or "")[:500] or None,
            "status": "pending",
        })
    except db.DuplicateSignup:
        existing = db.find_signup_by_email(waitlist["id"], email)
        return error(409, "already_signed_up", signup_id=existing["id"] if existing else None)

    log.info("signup %s accepted waitlist=%s audio=%s", signup_id, waitlist_slug, bool(audio_path))
    background_tasks.add_task(process_signup, signup_id)
    return JSONResponse({"signup_id": signup_id, "status": "pending"}, status_code=201)


@router.get("/v1/signups/{signup_id}/status")
def signup_status(signup_id: str):
    row = db.get_signup(signup_id) if is_uuid(signup_id) else None
    if not row:
        return error(404, "signup_not_found")
    return {
        "status": row["status"],
        "human_verdict": row["human_verdict"],
        "pain_score": row["pain_score"],
    }
