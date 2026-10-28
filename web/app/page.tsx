import Link from "next/link";
import TopBar from "./TopBar";
import { requireUser } from "@/lib/supabase/server";

const OWN_SLUG = process.env.NEXT_PUBLIC_OWN_WAITLIST_SLUG || "proof-of-demand";

export default async function Home({ searchParams }: PageProps<"/">) {
  const { pro } = await searchParams;
  const { user } = await requireUser();

  return (
    <>
      <TopBar signedIn={!!user} />
      <main className="mx-auto w-full max-w-5xl px-4">
        <section className="grid items-center gap-10 py-16 md:grid-cols-2">
          <div>
            <h1 className="text-4xl font-bold leading-tight md:text-5xl">Waitlists lie. Know which signups are real.</h1>
            <p className="mt-4 text-lg text-gray-600">
              Proof of Demand checks every waitlist signup: is it a real human, do they have a specific problem, and will they pay?
            </p>
            <ul className="mt-6 space-y-3">
              <li><b>✓ Real human check.</b> A 20-second voice answer, matched against other signups to catch one person behind many emails.</li>
              <li><b>✓ Specific-pain score.</b> AI scores how concrete their problem is. &ldquo;Lost 3 hours last Tuesday&rdquo; beats &ldquo;sounds cool&rdquo;.</li>
              <li><b>✓ Refundable deposits.</b> Signups can reserve a spot with a small deposit, so you see who will pay.</li>
            </ul>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link href={user ? "/app" : "/login"} className="rounded bg-black px-5 py-3 text-white">Create your waitlist, free</Link>
              <Link href="/guide" className="rounded border border-gray-300 px-5 py-3">Add to your site in 2 minutes</Link>
            </div>
          </div>
          <div>
            <p className="mb-2 text-sm text-gray-500">Try it: this is our own waitlist, running on our own widget.</p>
            <iframe src={`/w/${OWN_SLUG}`} allow="microphone" title="Join the Proof of Demand waitlist" className="h-[540px] w-full border-0" />
          </div>
        </section>

        <section className="border-t border-gray-200 py-12">
          <p className="mx-auto max-w-2xl text-center text-gray-600">
            Your investor sees <b>&ldquo;500 signups&rdquo;</b>. Show them <b>312 signups → 214 verified humans → 88 with specific pain → 23 paid</b>,
            with a public report and badge they can check themselves.
          </p>
        </section>

        <section id="pricing" className="border-t border-gray-200 py-12">
          <h2 className="mb-6 text-center text-2xl font-semibold">Pricing</h2>
          {pro === "thanks" && <p className="mb-4 text-center text-green-700">Thanks for going Pro! We&apos;ll be in touch.</p>}
          {pro === "error" && <p className="mb-4 text-center text-red-600">Checkout couldn&apos;t start. Please try again.</p>}
          <div className="mx-auto grid max-w-3xl gap-4 md:grid-cols-2">
            <div className="rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-semibold">Free</h3>
              <div className="my-2 text-3xl font-bold">$0</div>
              <ul className="space-y-1 text-sm text-gray-700">
                <li>1 waitlist</li><li>100 signups</li><li>Voice verification + pain score</li><li>Founder dashboard</li>
              </ul>
              <Link href={user ? "/app" : "/login"} className="mt-6 block rounded border border-gray-300 px-4 py-2 text-center">Start free</Link>
            </div>
            <div className="rounded-lg border-2 border-black p-6">
              <h3 className="text-lg font-semibold">Pro</h3>
              <div className="my-2 text-3xl font-bold">$9<span className="text-base font-normal text-gray-500">/month</span></div>
              <ul className="space-y-1 text-sm text-gray-700">
                <li>Unlimited waitlists and signups</li><li>Public report + badge</li><li>Slack / email / Sheets alerts</li><li>Refundable deposits</li>
              </ul>
              <form action="/api/pro" method="post">
                <button className="mt-6 w-full rounded bg-black px-4 py-2 text-white">Go Pro</button>
              </form>
            </div>
          </div>
        </section>
      </main>
      <footer className="border-t border-gray-200 py-6 text-center text-xs text-gray-500">Proof of Demand · Hacker House Goa 2026</footer>
    </>
  );
}
