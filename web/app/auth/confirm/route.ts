import { NextResponse } from "next/server";
import { supabaseServer } from "@/lib/supabase/server";

// Landing page for the emailed magic link: swaps the token for a session cookie.
export async function GET(request: Request) {
  const url = new URL(request.url);
  const token_hash = url.searchParams.get("token_hash");
  if (token_hash) {
    const supabase = await supabaseServer();
    const { error } = await supabase.auth.verifyOtp({ token_hash, type: "email" });
    if (!error) return NextResponse.redirect(new URL("/app", url.origin));
  }
  return NextResponse.redirect(new URL("/login?error=link", url.origin));
}
