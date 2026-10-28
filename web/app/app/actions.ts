"use server";
import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";
import { requireUser } from "@/lib/supabase/server";
import { slugify } from "@/lib/flags";
import { dodo } from "@/lib/dodo";

export type FormState = { error?: string };

export async function createWaitlist(_: FormState, form: FormData): Promise<FormState> {
  const { supabase, user } = await requireUser();
  if (!user) redirect("/login");

  const product_name = String(form.get("product_name") ?? "").trim();
  const question = String(form.get("question") ?? "").trim();
  const slug = slugify(String(form.get("slug") || product_name));
  const amount = Math.round(Number(form.get("deposit_amount") || 1) * 100);
  if (!product_name || !question) return { error: "Product name and question are required." };
  if (!slug) return { error: "Slug must contain letters or numbers." };
  if (!(amount >= 50 && amount <= 100000)) return { error: "Deposit must be between 0.50 and 1000." };

  const { error } = await supabase.from("waitlists").insert({
    owner_id: user.id,
    slug,
    product_name,
    product_description: String(form.get("product_description") ?? "").trim() || null,
    question,
    deposit_enabled: form.get("deposit_enabled") === "on",
    deposit_amount_cents: amount,
  });
  if (error) return { error: error.code === "23505" ? `The slug "${slug}" is taken. Pick another.` : error.message };
  redirect(`/app/w/${slug}?created=1`);
}

export async function setReportPublic(waitlistId: string, slug: string, value: boolean) {
  const { supabase, user } = await requireUser();
  if (!user) redirect("/login");
  await supabase.from("waitlists").update({ report_public: value }).eq("id", waitlistId);
  revalidatePath(`/app/w/${slug}`);
}

export async function refundDeposit(signupId: string) {
  const { supabase, user } = await requireUser();
  if (!user) redirect("/login");
  // RLS: this only returns the row if the founder owns its waitlist.
  const { data } = await supabase.from("signups").select("deposit_payment_id, deposit_status").eq("id", signupId).single();
  if (!data?.deposit_payment_id || data.deposit_status !== "paid") return { error: "Nothing to refund." };
  try {
    await dodo().refunds.create({ payment_id: data.deposit_payment_id, reason: "Waitlist deposit refund" });
  } catch (e) {
    return { error: e instanceof Error ? e.message : "Refund failed." };
  }
  // deposit_status flips to "refunded" when Dodo sends refund.succeeded.
  return {};
}
