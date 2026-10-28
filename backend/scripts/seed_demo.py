"""Seed the `demo-ring` waitlist with a striking funnel for the judges (macOS only: uses `say`).

    python -m scripts.seed_demo --owner-id <founder auth user uuid> [--reset]

Creates 3 genuine signups (different voices, specific pain), 5 signups using ONE voice with
5 emails, 2 disposable emails and 2 generic "sounds cool" answers, then scores them with the
real pipeline. Needs the backend .env (Supabase, STT and LLM keys) on this machine.
"""

import argparse
import hashlib
import subprocess
import tempfile
import uuid
from pathlib import Path

from app import db, models
from app.config import get_settings
from app.pipeline.run import process_signup

SLUG = "demo-ring"
PRODUCT = ("Invoice reconciliation tool for small Indian businesses: matches bank statements to "
           "GST invoices automatically.")
QUESTION = "When did this problem last cost you time or money? Tell us what happened."

# (voice, email, device, network, answer)
SIGNUPS = [
    ("Aman", "priya.sharma@gmail.com", "dev-g1", "net-g1",
     "Last Tuesday I spent three hours matching about two hundred bank entries against our GST "
     "invoices in Excel. We do this every month end, and we still pay our CA fifteen thousand "
     "rupees a quarter to fix the mismatches."),
    ("Moira", "arjun@kiranastores.in", "dev-g2", "net-g2",
     "In September our GST return was delayed by a week because two invoices didn't match the "
     "bank credits. We paid a late fee of about four thousand rupees, and now I keep a separate "
     "Google Sheet just to track this."),
    ("Karen", "meera.accounts@outlook.com", "dev-g3", "net-g3",
     "Every Friday my accountant and I sit for two hours ticking off UPI payments against "
     "invoices. Last Friday we found a fifty thousand rupee payment we had never invoiced."),
    # one person, five emails
    ("Daniel", "rahul.k1@gmail.com", "dev-r1", "net-r",
     "Reconciling invoices takes me hours every single month and it is really painful."),
    ("Daniel", "rahulkumar.biz@yahoo.com", "dev-r2", "net-r",
     "I waste a whole day each month on matching bank statements with invoices."),
    ("Daniel", "rk.founder@gmail.com", "dev-r2", "net-r",
     "Our books never match the bank and we lose money on late GST fees."),
    ("Daniel", "kumar.rahul99@hotmail.com", "dev-r3", "net-r",
     "Matching payments to invoices is the worst part of running my shop."),
    ("Daniel", "rahul.waitlist@proton.me", "dev-r3", "net-r",
     "I would love this, invoice matching costs me so much time every month."),
    # throwaway emails
    ("Samantha", "deal-hunter@mailinator.com", "dev-d1", "net-d1",
     "I lost about two hours last week fixing invoice mismatches for my small business."),
    ("Fred", "freebie@guerrillamail.com", "dev-d2", "net-d2",
     "Bank reconciliation took me most of Saturday because the payments did not match."),
    # curious, no real pain
    ("Ralph", "curious.cat@gmail.com", "dev-c1", "net-c1",
     "Sounds cool, I'd use it."),
    ("Kathy", "just.browsing@gmail.com", "dev-c2", "net-c2",
     "This looks like a really interesting idea. Good luck with the launch!"),
]


def tts_webm(voice: str, text: str, out: Path) -> bytes:
    aiff = out.with_suffix(".aiff")
    subprocess.run(["say", "-v", voice, "-o", str(aiff), text], check=True)
    subprocess.run([get_settings().ffmpeg_bin, "-y", "-loglevel", "error", "-i", str(aiff),
                    "-c:a", "libopus", str(out)], check=True)
    return out.read_bytes()


def ensure_waitlist(owner_id: str) -> dict:
    wl = db.get_waitlist_by_slug(SLUG)
    if wl:
        return wl
    return db.client().table("waitlists").insert({
        "owner_id": owner_id, "slug": SLUG, "product_name": "LedgerMatch (demo)",
        "product_description": PRODUCT, "question": QUESTION,
    }).execute().data[0]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--owner-id", required=True, help="founder's auth.users id (Supabase > Auth)")
    ap.add_argument("--reset", action="store_true", help="delete existing demo-ring signups first")
    args = ap.parse_args()

    wl = ensure_waitlist(args.owner_id)
    if args.reset:
        db.client().table("signups").delete().eq("waitlist_id", wl["id"]).execute()
    models.load()

    with tempfile.TemporaryDirectory() as tmp:
        for i, (voice, email, device, net, text) in enumerate(SIGNUPS):
            if db.find_signup_by_email(wl["id"], email):
                print(f"skip {email} (exists)")
                continue
            sid = str(uuid.uuid4())
            path = f"{wl['id']}/{sid}.webm"
            db.upload_audio(path, tts_webm(voice, text, Path(tmp) / f"{i}.webm"), "audio/webm")
            db.insert_signup({
                "id": sid, "waitlist_id": wl["id"], "email": email, "consent": True,
                "audio_path": path, "device_id": device, "user_agent": "seed_demo",
                "ip_hash": hashlib.sha256(f"demo-{net}".encode()).hexdigest(),
            })
            process_signup(sid)
            row = db.get_signup(sid)
            print(f"{email:32} {row['human_verdict']:>10} trust={row['trust_score']} "
                  f"pain={row['pain_score']} flags={[f['code'] for f in row['flags']]}")


if __name__ == "__main__":
    main()
