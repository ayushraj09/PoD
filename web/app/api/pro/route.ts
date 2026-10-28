import { dodo } from "@/lib/dodo";
import { SITE } from "@/lib/site";
import { requireUser } from "@/lib/supabase/server";

// Pro plan checkout. Homepage form POSTs here; we redirect to Dodo.
export async function POST() {
  const { user } = await requireUser();
  try {
    const session = await dodo().checkoutSessions.create({
      product_cart: [{ product_id: process.env.DODO_PRO_PRODUCT_ID!, quantity: 1 }],
      ...(user?.email ? { customer: { email: user.email } } : {}),
      return_url: `${SITE}/?pro=thanks`,
      metadata: { plan: "pro", ...(user ? { owner_id: user.id } : {}) },
    });
    return Response.redirect(session.checkout_url!, 303);
  } catch (e) {
    console.error("dodo pro checkout failed", e);
    return Response.redirect(`${SITE}/?pro=error#pricing`, 303);
  }
}
