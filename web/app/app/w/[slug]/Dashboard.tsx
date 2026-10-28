"use client";
import { useEffect, useMemo, useState, useTransition } from "react";
import { supabaseBrowser } from "@/lib/supabase/client";
import { VERDICT_STYLE, flagText, funnel, maskEmail, painLevel, type Signup } from "@/lib/flags";
import { refundDeposit } from "../../actions";

export default function Dashboard({ waitlistId, initial }: { waitlistId: string; initial: Signup[] }) {
  const [rows, setRows] = useState<Signup[]>(initial);
  const [humansOnly, setHumansOnly] = useState(false);
  const [highPainOnly, setHighPainOnly] = useState(false);
  const [live, setLive] = useState(false);

  useEffect(() => {
    const supabase = supabaseBrowser();
    const channel = supabase
      .channel(`signups-${waitlistId}`)
      .on(
        "postgres_changes",
        { event: "*", schema: "public", table: "signups", filter: `waitlist_id=eq.${waitlistId}` },
        (payload) => {
          if (payload.eventType === "DELETE") {
            setRows((r) => r.filter((x) => x.id !== (payload.old as Signup).id));
            return;
          }
          const row = payload.new as Signup;
          setRows((r) => {
            const rest = r.filter((x) => x.id !== row.id);
            return [row, ...rest].sort((a, b) => b.created_at.localeCompare(a.created_at));
          });
        },
      )
      .subscribe((status) => setLive(status === "SUBSCRIBED"));
    return () => { supabase.removeChannel(channel); };
  }, [waitlistId]);

  const f = funnel(rows);
  const steps = [
    ["Signups", f.signups],
    ["Real humans", f.humans],
    ["Specific pain", f.pain],
    ["Paid", f.paid],
  ] as const;

  const shown = rows.filter(
    (r) => (!humansOnly || r.human_verdict === "verified") && (!highPainOnly || (r.pain_score ?? 0) >= 70),
  );
  const topQuotes = useMemo(
    () => rows
      .filter((r) => r.human_verdict === "verified" && r.pain_quote)
      .sort((a, b) => (b.pain_score ?? 0) - (a.pain_score ?? 0))
      .slice(0, 5),
    [rows],
  );

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {steps.map(([label, n]) => (
          <div key={label} className="rounded-lg border border-gray-200 p-4">
            <div className="text-sm text-gray-600">{label}</div>
            <div className="text-3xl font-semibold tabular-nums">{n}</div>
            <div className="text-xs text-gray-500">{f.signups ? Math.round((n / f.signups) * 100) : 0}% of signups</div>
            <div className="mt-2 h-1.5 rounded bg-gray-100">
              <div className="h-full rounded bg-black" style={{ width: `${f.signups ? (n / f.signups) * 100 : 0}%` }} />
            </div>
          </div>
        ))}
      </div>

      {topQuotes.length > 0 && (
        <section className="rounded-lg border border-gray-200 p-5">
          <h2 className="mb-3 font-semibold">Top quotes from verified humans</h2>
          <ul className="space-y-2">
            {topQuotes.map((r) => (
              <li key={r.id} className="flex gap-3">
                <span className="w-8 shrink-0 text-right font-semibold tabular-nums">{r.pain_score}</span>
                <span className="italic">&ldquo;{r.pain_quote}&rdquo;</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      <section>
        <div className="mb-2 flex flex-wrap items-center gap-4 text-sm">
          <h2 className="mr-auto font-semibold">
            Signups <span className={`ml-2 text-xs ${live ? "text-green-600" : "text-gray-400"}`}>{live ? "● live" : "○ connecting"}</span>
          </h2>
          <label className="flex items-center gap-1"><input type="checkbox" checked={humansOnly} onChange={(e) => setHumansOnly(e.target.checked)} /> Real humans only</label>
          <label className="flex items-center gap-1"><input type="checkbox" checked={highPainOnly} onChange={(e) => setHighPainOnly(e.target.checked)} /> High pain only</label>
        </div>
        <div className="overflow-x-auto rounded-lg border border-gray-200">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 text-xs text-gray-600">
              <tr>{["Email", "Verdict", "Pain", "Quote", "Warnings", "Deposit", "Time"].map((h) => <th key={h} className="px-3 py-2 font-medium">{h}</th>)}</tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {shown.length === 0 && (
                <tr><td colSpan={7} className="px-3 py-6 text-center text-gray-500">No signups yet.</td></tr>
              )}
              {shown.map((r) => <Row key={r.id} r={r} />)}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function Row({ r }: { r: Signup }) {
  const busy = r.status === "pending" || r.status === "processing";
  const level = painLevel(r.pain_score);
  return (
    <tr className="align-top">
      <td className="px-3 py-2 font-mono text-xs">{maskEmail(r.email)}</td>
      <td className="px-3 py-2">
        {busy ? (
          <span className="inline-flex items-center gap-1 text-xs text-gray-500">
            <span className="h-3 w-3 animate-spin rounded-full border-2 border-gray-300 border-t-gray-700" /> scoring
          </span>
        ) : (
          <span className={`rounded px-2 py-0.5 text-xs font-medium ${VERDICT_STYLE[r.human_verdict ?? "unverified"] ?? VERDICT_STYLE.unverified}`}>
            {r.human_verdict ?? "unverified"}
          </span>
        )}
      </td>
      <td className="px-3 py-2 whitespace-nowrap">{r.pain_score != null ? `${r.pain_score} · ${level}` : "—"}</td>
      <td className="max-w-xs px-3 py-2 italic">{r.pain_quote ? `“${r.pain_quote}”` : ""}</td>
      <td className="px-3 py-2 text-xs text-amber-800">
        {(r.flags ?? []).map((f, i) => <div key={i}>⚠ {flagText(f)}</div>)}
      </td>
      <td className="px-3 py-2 text-xs"><Deposit r={r} /></td>
      <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-500">{new Date(r.created_at).toLocaleString()}</td>
    </tr>
  );
}

function Deposit({ r }: { r: Signup }) {
  const [pending, start] = useTransition();
  const [msg, setMsg] = useState("");
  if (r.deposit_status !== "paid") return <span className="text-gray-500">{r.deposit_status}</span>;
  return (
    <div>
      <span className="font-medium text-green-700">paid</span>
      <button
        disabled={pending || msg === "refund requested"}
        onClick={() => start(async () => {
          if (!confirm("Refund this deposit in full?")) return;
          const res = await refundDeposit(r.id);
          setMsg(res.error ?? "refund requested");
        })}
        className="ml-2 underline disabled:opacity-50"
      >
        Refund
      </button>
      {msg && <div className="text-gray-500">{msg}</div>}
    </div>
  );
}
