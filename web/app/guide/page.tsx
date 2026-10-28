import Link from "next/link";
import TopBar from "../TopBar";
import { SITE } from "@/lib/site";

export default function Guide() {
  return (
    <>
      <TopBar />
      <main className="mx-auto w-full max-w-2xl px-4 py-10">
        <h1 className="text-3xl font-semibold">Add Proof of Demand to your site in 2 minutes</h1>
        <ol className="mt-8 space-y-8">
          <li>
            <h2 className="font-semibold">1. Sign in and create a waitlist</h2>
            <p className="mt-1 text-gray-600">
              <Link href="/login" className="underline">Sign in</Link> with your email, then fill in your product name, a one-line
              description and the voice question. The default question works well for most products.
            </p>
          </li>
          <li>
            <h2 className="font-semibold">2. Paste the embed code</h2>
            <p className="mt-1 text-gray-600">Copy the code from your dashboard and paste it where the signup form should appear:</p>
            <pre className="mt-2 overflow-x-auto rounded bg-gray-50 p-3 text-xs">{`<script src="${SITE}/embed.js" data-waitlist="your-slug" async></script>`}</pre>
            <p className="mt-2 text-sm text-gray-500">
              Works on plain HTML, Next.js, Framer, Webflow and Carrd custom code blocks. Some builders (e.g. Wix) block the
              microphone inside embeds; share your direct link <code>{SITE}/w/your-slug</code> instead.
            </p>
          </li>
          <li>
            <h2 className="font-semibold">3. Watch real signups arrive</h2>
            <p className="mt-1 text-gray-600">
              Your dashboard updates live with each signup&apos;s verdict, pain score and quote. Turn on the public report to get a
              shareable link and badge for investors.
            </p>
          </li>
        </ol>
      </main>
    </>
  );
}
