// Labels from contracts/scoring.md. Keep in sync with that file.
export const FLAG_TEXT: Record<string, string> = {
  disposable_email: "Uses a throwaway email address",
  repeat_device: "Same device already signed up to this waitlist",
  repeat_ip: "Many signups from the same network",
  same_voice: "Voice matches another signup",
  possible_ai_voice: "Voice may be AI-generated",
  no_speech: "Recording has no clear speech",
  too_short: "Answer under 3 seconds",
  ring_member: "Part of a connected group of suspicious signups",
  processing_error: "Scoring failed; will show as unverified",
};

export type Flag = { code: string; detail?: string };

export const flagText = (f: Flag) => FLAG_TEXT[f.code] ?? f.code;

export const VERDICT_STYLE: Record<string, string> = {
  verified: "bg-green-100 text-green-800",
  suspicious: "bg-amber-100 text-amber-800",
  fake: "bg-red-100 text-red-800",
  unverified: "bg-gray-100 text-gray-700",
};

export const painLevel = (s: number | null) =>
  s == null ? null : s >= 70 ? "high" : s >= 40 ? "medium" : "low";

export function maskEmail(email: string) {
  const [user, domain] = email.split("@");
  return `${user.slice(0, 2)}***@${domain ?? ""}`;
}

export type Signup = {
  id: string;
  email: string;
  status: string;
  pain_score: number | null;
  pain_quote: string | null;
  human_verdict: string | null;
  flags: Flag[];
  deposit_status: string;
  deposit_payment_id: string | null;
  created_at: string;
};

// Funnel definitions from contracts/scoring.md.
export function funnel(rows: Pick<Signup, "human_verdict" | "pain_score" | "deposit_status">[]) {
  const humans = rows.filter((r) => r.human_verdict === "verified");
  return {
    signups: rows.length,
    humans: humans.length,
    pain: humans.filter((r) => (r.pain_score ?? 0) >= 70).length,
    paid: rows.filter((r) => r.deposit_status === "paid").length,
  };
}

export const slugify = (s: string) =>
  s.toLowerCase().trim().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 40);
