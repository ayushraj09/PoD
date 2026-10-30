import { supabaseAdmin } from "@/lib/supabase/server";
import { SITE } from "@/lib/site";

// Magic link via EmailJS instead of Supabase's mailer (2 emails/hour).
// Supabase makes the token without sending anything; we email the link ourselves.
export async function POST(req: Request) {
  const { email } = await req.json().catch(() => ({}));
  if (typeof email !== "string" || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return Response.json({ error: "Enter a valid email." }, { status: 400 });
  }

  // magiclink also creates the user on first sign-in.
  const { data, error } = await supabaseAdmin().auth.admin.generateLink({ type: "magiclink", email });
  if (error) {
    console.error("generateLink failed", error);
    return Response.json({ error: "Couldn't create the link. Try again." }, { status: 500 });
  }

  // SITE, not the request's Host header, so nobody can make us email a link to their own domain.
  const link = `${SITE}/auth/confirm?token_hash=${data.properties.hashed_token}`;
  const res = await fetch("https://api.emailjs.com/api/v1.0/email/send", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      service_id: process.env.EMAILJS_SERVICE_ID,
      template_id: process.env.EMAILJS_TEMPLATE_ID,
      user_id: process.env.EMAILJS_PUBLIC_KEY,
      accessToken: process.env.EMAILJS_PRIVATE_KEY,
      template_params: { to_email: email, link },
    }),
  });
  if (!res.ok) {
    console.error("emailjs failed", res.status, await res.text());
    return Response.json({ error: "Couldn't send the email. Try again." }, { status: 502 });
  }
  return Response.json({ ok: true });
}
