import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import { requireUser } from "@/lib/supabase/server";
import { SITE, badgeCode, embedCode } from "@/lib/site";
import { CodeBox } from "../../../CopyButton";
import TopBar from "../../../TopBar";
import Dashboard from "./Dashboard";
import ReportToggle from "./ReportToggle";

const COLS = "id, email, status, pain_score, pain_quote, human_verdict, flags, deposit_status, deposit_payment_id, created_at";

export default async function WaitlistDashboard({ params, searchParams }: PageProps<"/app/w/[slug]">) {
  const { slug } = await params;
  const { created } = await searchParams;
  const { supabase, user } = await requireUser();
  if (!user) redirect("/login");

  // RLS: returns nothing unless this founder owns it.
  const { data: w } = await supabase.from("waitlists").select("*").eq("slug", slug).maybeSingle();
  if (!w) notFound();
  const { data: signups } = await supabase
    .from("signups").select(COLS).eq("waitlist_id", w.id).order("created_at", { ascending: false }).limit(1000);

  return (
    <>
      <TopBar signedIn />
      <main className="mx-auto w-full max-w-6xl space-y-8 px-4 py-8">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <div>
            <Link href="/app" className="text-sm text-gray-500">← All waitlists</Link>
            <h1 className="text-2xl font-semibold">{w.product_name}</h1>
          </div>
          <a href={`/w/${w.slug}`} target="_blank" className="text-sm underline">Open signup page ↗</a>
        </div>

        {created && (
          <p className="rounded bg-green-50 p-3 text-sm text-green-800">Waitlist created. Paste the embed code below on your landing page.</p>
        )}

        <Dashboard waitlistId={w.id} initial={signups ?? []} />

        <section className="grid gap-6 md:grid-cols-2">
          <div className="space-y-3 rounded-lg border border-gray-200 p-5">
            <h2 className="font-semibold">Add to your site</h2>
            <CodeBox label="Embed code (paste where the form should appear)" code={embedCode(w.slug)} />
            <CodeBox label="No website, or the embed can't use the mic (e.g. Wix)? Share this link" code={`${SITE}/w/${w.slug}`} />
          </div>
          <div className="space-y-3 rounded-lg border border-gray-200 p-5">
            <h2 className="font-semibold">Public report + badge</h2>
            <ReportToggle waitlistId={w.id} slug={w.slug} isPublic={w.report_public} />
            <CodeBox label="Report link" code={`${SITE}/r/${w.slug}`} />
            <CodeBox label="Badge embed code" code={badgeCode(w.slug)} />
            {w.report_public && (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={`/badge/${w.slug}.svg`} alt="badge preview" />
            )}
          </div>
          <div className="space-y-2 rounded-lg border border-gray-200 p-5 md:col-span-2">
            <h2 className="font-semibold">Alerts</h2>
            <p className="text-sm text-gray-600">
              Each scored signup is sent through viaSocket: verified signups post a message to Slack or email
              (&ldquo;New verified signup: pain 82, &lsquo;…quote…&rsquo;&rdquo;) and add a row to a Google Sheet with
              the masked email, verdict, pain score and quote. Ask us to connect your Slack channel or Sheet.
            </p>
          </div>
        </section>
      </main>
    </>
  );
}
