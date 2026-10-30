import Link from "next/link";
import TopBar from "./TopBar";
import { CrowdCanvas } from "@/components/ui/crowd-canvas";
import { requireUser } from "@/lib/supabase/server";

const OWN_SLUG = process.env.NEXT_PUBLIC_OWN_WAITLIST_SLUG || "proof-of-demand";

export default async function Home({ searchParams }: PageProps<"/">) {
  const { pro } = await searchParams;
  const { user } = await requireUser();

  return (
    <>
      <TopBar signedIn={!!user} />
      <section className="relative isolate h-[calc(100svh-53px)] min-h-[680px] overflow-hidden bg-white">
        <div className="relative z-10 mx-auto flex max-w-3xl flex-col items-center px-4 pt-16 text-center md:pt-24">
          <span className="text-xs uppercase tracking-[0.2em] text-gray-400">Proof of Demand</span>
          <h1 className="mt-4 text-5xl font-bold leading-[1.05] tracking-tight md:text-7xl">Waitlists lie.</h1>
          <p className="mt-4 text-balance text-xl text-gray-600 md:text-2xl">Know which of these people are real, have the problem, and will pay.</p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <Link href={user ? "/app" : "/login"} className="rounded bg-black px-5 py-3 text-white">Create your waitlist, free</Link>
            <a href="#try" className="rounded border border-gray-300 bg-white/80 px-5 py-3 backdrop-blur">Try the widget ↓</a>
          </div>
        </div>
        <CrowdCanvas src="/peeps.png" className="absolute inset-x-0 bottom-0 h-[65%] w-full" />
      </section>

      <main className="mx-auto w-full max-w-5xl px-4">
        <section id="try" className="grid scroll-mt-4 items-center gap-10 py-16 md:grid-cols-2">
          <div>
            <h2 className="text-3xl font-bold leading-tight md:text-4xl">Every signup, checked three ways.</h2>
            <ul className="mt-6 space-y-3">
              <li><b>✓ Real human check.</b> A 20-second voice answer, matched against other signups to catch one person behind many emails.</li>
              <li><b>✓ Specific-pain score.</b> AI scores how concrete their problem is. &ldquo;Lost 3 hours last Tuesday&rdquo; beats &ldquo;sounds cool&rdquo;.</li>
              <li><b>✓ Refundable deposits.</b> Signups can reserve a spot with a small deposit, so you see who will pay.</li>
            </ul>
            <Link href="/guide" className="mt-8 inline-block rounded border border-gray-300 px-5 py-3">Add to your site in 2 minutes</Link>
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
      <footer className="border-t border-gray-200 py-6 text-center text-xs text-gray-500">
        Proof of Demand · Hacker House Goa 2026 · Crowd by <a href="https://skiper-ui.com" className="underline">Skiper UI</a>, illustrations by <a href="https://www.openpeeps.com" className="underline">Open Peeps</a>
      </footer>
    </>
  );
}
