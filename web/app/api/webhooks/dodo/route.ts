import { Webhook } from "standardwebhooks";
import { supabaseAdmin } from "@/lib/supabase/server";

type Event = { type: string; data: { payment_id?: string; metadata?: Record<string, string>; object?: { metadata?: Record<string, string> } } };

export async function POST(req: Request) {
  const raw = await req.text(); // raw body is needed for the signature
  let event: Event;
  try {
    event = new Webhook(process.env.DODO_WEBHOOK_SECRET!).verify(raw, {
      "webhook-id": req.headers.get("webhook-id") ?? "",
      "webhook-signature": req.headers.get("webhook-signature") ?? "",
      "webhook-timestamp": req.headers.get("webhook-timestamp") ?? "",
    }) as Event;
  } catch {
    return new Response("bad signature", { status: 401 });
  }

  // Dodo examples disagree on where metadata sits; SDK types say data.metadata.
  const meta = event.data?.metadata ?? event.data?.object?.metadata ?? {};
  const db = supabaseAdmin();

  if (event.type === "payment.succeeded" && meta.signup_id) {
    console.log("dodo payment.succeeded", JSON.stringify(event.data).slice(0, 2000));
    await db.from("signups")
      .update({ deposit_status: "paid", deposit_payment_id: event.data.payment_id })
      .eq("id", meta.signup_id);
  }
  if (event.type === "refund.succeeded" && event.data.payment_id) {
    await db.from("signups").update({ deposit_status: "refunded" }).eq("deposit_payment_id", event.data.payment_id);
  }
  // ponytail: Pro payments (metadata.plan = "pro") are only recorded in Dodo; add a plans table when limits are enforced.
  return new Response("ok");
}
