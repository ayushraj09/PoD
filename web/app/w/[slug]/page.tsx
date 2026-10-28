import { notFound } from "next/navigation";
import { supabaseAdmin } from "@/lib/supabase/server";
import Widget from "./Widget";

export default async function WidgetPage({ params, searchParams }: PageProps<"/w/[slug]">) {
  const { slug } = await params;
  const { deposit } = await searchParams;
  // Service key, so select ONLY public fields.
  const { data: w } = await supabaseAdmin()
    .from("waitlists")
    .select("slug, product_name, question, deposit_enabled, deposit_amount_cents, deposit_currency")
    .eq("slug", slug)
    .maybeSingle();
  if (!w) notFound();

  return (
    <main className="mx-auto w-full max-w-md p-4">
      <Widget waitlist={w} depositDone={deposit === "done"} />
    </main>
  );
}
