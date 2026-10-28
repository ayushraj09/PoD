"use client";
import { useActionState, useState } from "react";
import { createWaitlist } from "./actions";
import { slugify } from "@/lib/flags";

const DEFAULT_Q = "When did this problem last cost you time or money? Tell us what happened.";
const input = "w-full rounded border border-gray-300 px-3 py-2";

export default function NewWaitlistForm() {
  const [state, action, pending] = useActionState(createWaitlist, {});
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [slugEdited, setSlugEdited] = useState(false);
  const [deposit, setDeposit] = useState(false);

  return (
    <form action={action} className="space-y-4 rounded-lg border border-gray-200 p-5">
      <h2 className="text-lg font-semibold">New waitlist</h2>
      <label className="block">
        <span className="text-sm font-medium">Product name</span>
        <input name="product_name" required className={input} value={name}
          onChange={(e) => { setName(e.target.value); if (!slugEdited) setSlug(slugify(e.target.value)); }} />
      </label>
      <label className="block">
        <span className="text-sm font-medium">One-line description</span>
        <input name="product_description" className={input} placeholder="Invoice reconciliation for small agencies" />
        <span className="text-xs text-gray-500">The AI uses this to judge whether an answer is about your problem.</span>
      </label>
      <label className="block">
        <span className="text-sm font-medium">Voice question</span>
        <textarea name="question" required rows={2} className={input} defaultValue={DEFAULT_Q} />
        <span className="text-xs text-gray-500">Ask for a concrete story. Specific answers score high.</span>
      </label>
      <label className="block">
        <span className="text-sm font-medium">Slug</span>
        <input name="slug" required className={input} value={slug}
          onChange={(e) => { setSlug(e.target.value); setSlugEdited(true); }} />
        <span className="text-xs text-gray-500">Your signup link: /w/{slugify(slug) || "…"}</span>
      </label>
      <div className="flex flex-wrap items-center gap-4">
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" name="deposit_enabled" checked={deposit} onChange={(e) => setDeposit(e.target.checked)} />
          Ask for a refundable deposit
        </label>
        {deposit && (
          <label className="flex items-center gap-2 text-sm">
            Amount (USD)
            <input name="deposit_amount" type="number" min="0.5" step="0.5" defaultValue="1" className="w-20 rounded border border-gray-300 px-2 py-1" />
          </label>
        )}
      </div>
      {state.error && <p className="text-sm text-red-600">{state.error}</p>}
      <button disabled={pending} className="rounded bg-black px-4 py-2 text-white disabled:opacity-50">
        {pending ? "Creating…" : "Create waitlist"}
      </button>
    </form>
  );
}
