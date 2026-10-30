"use client";
import { useState } from "react";
import TopBar from "../TopBar";

export default function Login() {
  const [email, setEmail] = useState("");
  const [state, setState] = useState<"idle" | "sending" | "sent" | "error">("idle");
  const [error, setError] = useState("");

  async function send(e: React.FormEvent) {
    e.preventDefault();
    setState("sending");
    const res = await fetch("/api/login", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ email }),
    }).catch(() => null);
    if (res?.ok) setState("sent");
    else {
      setError((await res?.json().catch(() => null))?.error ?? "Couldn't send the link. Try again.");
      setState("error");
    }
  }

  return (
    <>
      <TopBar />
      <main className="mx-auto w-full max-w-sm px-4 py-16">
        <h1 className="mb-2 text-2xl font-semibold">Founder sign in</h1>
        <p className="mb-6 text-sm text-gray-600">We&apos;ll email you a magic link. No password.</p>
        {state === "sent" ? (
          <p className="rounded bg-green-50 p-4 text-green-800">Check your inbox for the sign-in link.</p>
        ) : (
          <form onSubmit={send} className="space-y-3">
            <input
              type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
              placeholder="you@startup.com"
              className="w-full rounded border border-gray-300 px-3 py-2"
            />
            <button disabled={state === "sending"} className="w-full rounded bg-black px-3 py-2 text-white disabled:opacity-50">
              {state === "sending" ? "Sending…" : "Send magic link"}
            </button>
            {state === "error" && <p className="text-sm text-red-600">{error}</p>}
          </form>
        )}
      </main>
    </>
  );
}
