import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getReport } from "@/lib/report";
import TopBar from "../../TopBar";

export async function generateMetadata({ params }: PageProps<"/r/[slug]">): Promise<Metadata> {
  const r = await getReport((await params).slug);
  if (!r?.public) return { title: "Proof of Demand" };
  return {
    title: `${r.product_name}: ${r.humans} verified humans · Proof of Demand`,
    description: `${r.signups} signups → ${r.humans} verified real humans → ${r.pain} with specific pain → ${r.paid} paid deposits`,
  };
}

export default async function ReportPage({ params }: PageProps<"/r/[slug]">) {
  const r = await getReport((await params).slug);
  if (!r) notFound();

  return (
    <>
      <TopBar />
      <main className="mx-auto w-full max-w-3xl px-4 py-10">
        {!r.public ? (
          <div className="py-16 text-center">
            <h1 className="text-2xl font-semibold">{r.product_name}</h1>
            <p className="mt-2 text-gray-600">This report is not public.</p>
          </div>
        ) : (
          <>
            <div className="text-sm font-medium text-green-700">✓ Verified Demand report</div>
            <h1 className="mt-1 text-3xl font-semibold">{r.product_name}</h1>
            {r.product_description && <p className="mt-1 text-gray-600">{r.product_description}</p>}

            <ol className="mt-8 space-y-3">
              {([
                ["Signups", r.signups, "Everyone who joined the waitlist"],
                ["Real humans", r.humans, "Passed the voice and duplicate-person checks"],
                ["Specific pain", r.pain, "Real humans who described a concrete, recent problem"],
                ["Paid", r.paid, "Put down a refundable deposit"],
              ] as const).map(([label, n, hint]) => (
                <li key={label} className="rounded-lg border border-gray-200 p-4">
                  <div className="flex items-baseline justify-between">
                    <span className="font-medium">{label}</span>
                    <span className="text-2xl font-semibold tabular-nums">{n}</span>
                  </div>
                  <div className="mt-2 h-2 rounded bg-gray-100">
                    <div className="h-full rounded bg-black" style={{ width: `${r.signups ? (n / r.signups) * 100 : 0}%` }} />
                  </div>
                  <div className="mt-1 text-xs text-gray-500">{hint}</div>
                </li>
              ))}
            </ol>

            {r.quotes.length > 0 && (
              <section className="mt-10">
                <h2 className="mb-3 font-semibold">In their own words</h2>
                <ul className="space-y-3">
                  {r.quotes.map((q, i) => (
                    <li key={i} className="border-l-4 border-gray-300 pl-4 italic">&ldquo;{q}&rdquo;</li>
                  ))}
                </ul>
              </section>
            )}

            <section className="mt-10 rounded-lg bg-gray-50 p-5 text-sm text-gray-700">
              <h2 className="mb-2 font-semibold">How we verify</h2>
              <ul className="list-disc space-y-1 pl-5">
                <li><b>Voice check:</b> each signup answers a question out loud in about 20 seconds.</li>
                <li><b>Duplicate-person check:</b> voices, devices and networks are compared to catch one person behind many emails.</li>
                <li><b>Specific-pain score:</b> AI scores how concrete the problem is (a time, a cost, a workaround), not how enthusiastic.</li>
                <li><b>Deposits:</b> a refundable deposit shows who will actually pay.</li>
              </ul>
            </section>
            <p className="mt-4 text-xs text-gray-500">Last updated {new Date(r.updated_at).toUTCString()}. No emails are shown on this page.</p>
          </>
        )}
      </main>
    </>
  );
}
