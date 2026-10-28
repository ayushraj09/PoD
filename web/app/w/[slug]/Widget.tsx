"use client";
import { useEffect, useRef, useState } from "react";

type Waitlist = {
  slug: string;
  product_name: string;
  question: string;
  deposit_enabled: boolean;
  deposit_amount_cents: number;
  deposit_currency: string;
};

const MAX_SECONDS = 20;
const FORMATS: [string, string][] = [
  ["audio/webm;codecs=opus", "webm"],
  ["audio/mp4", "mp4"],
  ["audio/ogg;codecs=opus", "ogg"],
];
const ERRORS: Record<string, string> = {
  invalid_email: "That email doesn't look right.",
  no_consent: "Please tick the consent box.",
  bad_audio: "We couldn't read that recording. Re-record or skip voice.",
  waitlist_not_found: "This waitlist no longer exists.",
  rate_limited: "Too many signups from your network. Try again in an hour.",
};
const BACKEND = (process.env.NEXT_PUBLIC_BACKEND_URL ?? "").replace(/\/$/, "");

const money = (cents: number, cur: string) =>
  new Intl.NumberFormat("en", { style: "currency", currency: cur }).format(cents / 100);

async function deviceId() {
  try {
    const FingerprintJS = (await import("@fingerprintjs/fingerprintjs")).default;
    const fp = await FingerprintJS.load();
    return (await fp.get()).visitorId;
  } catch {
    return "unknown"; // ad blockers etc. Weak signal anyway.
  }
}

export default function Widget({ waitlist, depositDone }: { waitlist: Waitlist; depositDone: boolean }) {
  const [rec, setRec] = useState<"idle" | "recording" | "done">("idle");
  const [seconds, setSeconds] = useState(0);
  const [audio, setAudio] = useState<{ blob: Blob; ext: string; url: string } | null>(null);
  const [skipVoice, setSkipVoice] = useState(false);
  const [email, setEmail] = useState("");
  const [consent, setConsent] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [signupId, setSignupId] = useState<string | null>(null);
  const [already, setAlready] = useState(false);
  const [verdict, setVerdict] = useState<string | null>(null);
  const [depositError, setDepositError] = useState("");
  const [checkoutUrl, setCheckoutUrl] = useState("");
  const recorder = useRef<MediaRecorder | null>(null);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => () => { if (timer.current) clearInterval(timer.current); }, []);

  async function startRecording() {
    setError("");
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
      setError("Recording isn't supported here. Open this page directly in your browser, or skip voice.");
      return;
    }
    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      setError("Microphone blocked. Allow mic access, open the direct link, or skip voice.");
      return;
    }
    const [mimeType, ext] = FORMATS.find(([t]) => MediaRecorder.isTypeSupported(t)) ?? ["", "webm"];
    const r = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
    const chunks: Blob[] = [];
    r.ondataavailable = (e) => e.data.size && chunks.push(e.data);
    r.onstop = () => {
      stream.getTracks().forEach((t) => t.stop());
      if (timer.current) clearInterval(timer.current);
      const blob = new Blob(chunks, { type: r.mimeType || mimeType || "audio/webm" });
      setAudio((old) => { if (old) URL.revokeObjectURL(old.url); return { blob, ext, url: URL.createObjectURL(blob) }; });
      setRec("done");
    };
    recorder.current = r;
    r.start();
    setRec("recording");
    setSeconds(0);
    const started = Date.now();
    timer.current = setInterval(() => {
      const s = Math.floor((Date.now() - started) / 1000);
      setSeconds(s);
      if (s >= MAX_SECONDS && r.state === "recording") r.stop();
    }, 250);
  }

  const stopRecording = () => recorder.current?.state === "recording" && recorder.current.stop();

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!consent) return setError(ERRORS.no_consent);
    if (!skipVoice && !audio) return setError("Record your answer first, or skip voice.");
    setSubmitting(true);
    setError("");
    try {
      const body = new FormData();
      body.set("waitlist_slug", waitlist.slug);
      body.set("email", email.trim());
      body.set("consent", "true");
      body.set("device_id", await deviceId());
      if (!skipVoice && audio) body.set("audio", audio.blob, `answer.${audio.ext}`);
      const res = await fetch(`${BACKEND}/v1/signups`, { method: "POST", body });
      const json = await res.json().catch(() => ({}));
      if (res.status === 201) setSignupId(json.signup_id);
      else if (res.status === 409) { setAlready(true); setSignupId(json.signup_id ?? null); }
      else setError(ERRORS[json.error] ?? "Something went wrong. Please try again.");
    } catch {
      setError("Couldn't reach the server. Check your connection and try again.");
    } finally {
      setSubmitting(false);
    }
  }

  // Poll verification for up to 20 s after a fresh signup with voice.
  useEffect(() => {
    if (!signupId || already || skipVoice) return;
    let tries = 0;
    const id = setInterval(async () => {
      tries++;
      try {
        const res = await fetch(`${BACKEND}/v1/signups/${signupId}/status`);
        const json = await res.json();
        if (json.status === "scored" || json.status === "failed") {
          setVerdict(json.human_verdict);
          clearInterval(id);
        }
      } catch { /* keep polling */ }
      if (tries >= 10) clearInterval(id);
    }, 2000);
    return () => clearInterval(id);
  }, [signupId, already, skipVoice]);

  async function reserve() {
    setDepositError("");
    // Open the tab synchronously so popup blockers allow it, then point it at checkout.
    const tab = window.open("", "_blank");
    try {
      const res = await fetch("/api/deposit", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ signup_id: signupId }),
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error ?? "Couldn't start checkout.");
      setCheckoutUrl(json.checkout_url);
      if (tab) tab.location.href = json.checkout_url;
    } catch (e) {
      tab?.close();
      setDepositError(e instanceof Error ? e.message : "Couldn't start checkout.");
    }
  }

  const amount = money(waitlist.deposit_amount_cents, waitlist.deposit_currency);
  const refundNote = `Fully refundable: the founder refunds your ${amount} if you ask, or if the product doesn't launch. Refunds go back to your card.`;

  if (depositDone) {
    return (
      <Card>
        <h1 className="text-xl font-semibold">Deposit received ✓</h1>
        <p className="mt-2 text-gray-600">Your spot on the {waitlist.product_name} list is reserved. {refundNote}</p>
      </Card>
    );
  }

  if (signupId || already) {
    return (
      <Card>
        <h1 className="text-xl font-semibold">{already ? "You're already on the list." : "You're on the list."}</h1>
        {!already && !skipVoice && (
          <p className="mt-2 text-sm">
            {verdict === "verified" ? (
              <span className="rounded bg-green-100 px-2 py-1 font-medium text-green-800">Verified ✓</span>
            ) : verdict ? (
              <span className="text-gray-600">Thanks for your answer.</span>
            ) : (
              <span className="text-gray-500">Checking your answer…</span>
            )}
          </p>
        )}
        {waitlist.deposit_enabled && signupId && (
          <div className="mt-6 rounded-lg bg-gray-50 p-4">
            <p className="font-medium">Reserve your spot with a refundable {amount} deposit.</p>
            <p className="mt-1 text-xs text-gray-600">{refundNote}</p>
            <button onClick={reserve} className="mt-3 w-full rounded bg-black px-4 py-2 text-white">Reserve for {amount}</button>
            {checkoutUrl && (
              <a href={checkoutUrl} target="_blank" rel="noopener" className="mt-2 block text-center text-xs underline">
                Checkout didn&apos;t open? Click here.
              </a>
            )}
            {depositError && <p className="mt-2 text-sm text-red-600">{depositError}</p>}
          </div>
        )}
      </Card>
    );
  }

  return (
    <Card>
      <form onSubmit={submit} className="space-y-4">
        <div>
          <div className="text-xs uppercase tracking-wide text-gray-500">{waitlist.product_name} waitlist</div>
          <h1 className="mt-1 text-lg font-semibold leading-snug">{skipVoice ? "Join the waitlist" : waitlist.question}</h1>
        </div>

        {!skipVoice && (
          <div className="rounded-lg border border-gray-200 p-4 text-center">
            {rec === "recording" ? (
              <>
                <div className="text-3xl font-mono tabular-nums">0:{String(Math.min(seconds, MAX_SECONDS)).padStart(2, "0")} / 0:{MAX_SECONDS}</div>
                <div className="mx-auto mt-2 h-1.5 w-full overflow-hidden rounded bg-gray-200">
                  <div className="h-full bg-red-500 transition-all" style={{ width: `${(Math.min(seconds, MAX_SECONDS) / MAX_SECONDS) * 100}%` }} />
                </div>
                <button type="button" onClick={stopRecording} className="mt-3 rounded-full bg-red-600 px-5 py-2 text-white">■ Stop</button>
              </>
            ) : rec === "done" && audio ? (
              <>
                <audio src={audio.url} controls className="w-full" />
                <button type="button" onClick={startRecording} className="mt-2 text-sm underline">Re-record</button>
              </>
            ) : (
              <>
                <button type="button" onClick={startRecording} className="rounded-full bg-red-600 px-5 py-2 text-white">● Record answer</button>
                <p className="mt-2 text-xs text-gray-500">Up to {MAX_SECONDS} seconds. Be specific: when, what happened, what it cost.</p>
              </>
            )}
          </div>
        )}

        <input
          type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
          placeholder="you@email.com" autoComplete="email"
          className="w-full rounded border border-gray-300 px-3 py-2"
        />
        <label className="flex items-start gap-2 text-xs text-gray-600">
          <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} className="mt-0.5" />
          I agree my voice answer is stored and analysed to verify my signup.
        </label>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button disabled={submitting || rec === "recording"} className="w-full rounded bg-black px-4 py-2 text-white disabled:opacity-50">
          {submitting ? "Joining…" : "Join waitlist"}
        </button>
        <button type="button" onClick={() => { setSkipVoice(!skipVoice); setError(""); }} className="block w-full text-center text-xs text-gray-500 underline">
          {skipVoice ? "Answer with voice instead (get verified)" : "Skip voice (your signup won't be verified)"}
        </button>
      </form>
      <p className="mt-4 text-center text-[10px] text-gray-400">
        <a href="/" target="_blank" rel="noopener">Verified by Proof of Demand</a>
      </p>
    </Card>
  );
}

function Card({ children }: { children: React.ReactNode }) {
  return <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">{children}</div>;
}
