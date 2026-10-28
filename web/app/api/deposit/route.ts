import { supabaseAdmin } from "@/lib/supabase/server";
import { dodo } from "@/lib/dodo";
import { SITE } from "@/lib/site";

export async function POST(req: Request) {
  const { signup_id } = await req.json().catch(() => ({}));
  if (typeof signup_id !== "string") return Response.json({ error: "Missing signup." }, { status: 400 });

  const db = supabaseAdmin();
  const { data: s } = await db
    .from("signups")
    .select("id, email, deposit_status, waitlists(slug, deposit_enabled, deposit_amount_cents)")
    .eq("id", signup_id)
    .maybeSingle();
  const w = s?.waitlists as unknown as { slug: string; deposit_enabled: boolean; deposit_amount_cents: number } | null;
  if (!s || !w?.deposit_enabled) return Response.json({ error: "Deposits aren't enabled here." }, { status: 404 });
  if (s.deposit_status === "paid") return Response.json({ error: "You've already paid. Thank you!" }, { status: 409 });

  try {
    const session = await dodo().checkoutSessions.create({
      // amount applies when the Dodo product is "pay what you want"; otherwise the product price is used
      product_cart: [{ product_id: process.env.DODO_DEPOSIT_PRODUCT_ID!, quantity: 1, amount: w.deposit_amount_cents }],
      customer: { email: s.email },
      return_url: `${SITE}/w/${w.slug}?deposit=done`,
      metadata: { signup_id: s.id },
    });
    await db.from("signups").update({ deposit_status: "pending" }).eq("id", s.id).neq("deposit_status", "paid");
    return Response.json({ checkout_url: session.checkout_url });
  } catch (e) {
    console.error("dodo checkout failed", e);
    return Response.json({ error: "Couldn't start checkout. Try again." }, { status: 502 });
  }
}
