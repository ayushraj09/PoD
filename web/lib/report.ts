import "server-only";
import { supabaseAdmin } from "@/lib/supabase/server";

export type Report =
  | { public: false; product_name: string }
  | {
      public: true;
      product_name: string;
      product_description: string | null;
      signups: number;
      humans: number;
      pain: number;
      paid: number;
      updated_at: string;
      quotes: string[];
    };

// Calls b_003's public_report(): counts + quotes only, never emails. null = no such waitlist.
export async function getReport(slug: string): Promise<Report | null> {
  const { data, error } = await supabaseAdmin().rpc("public_report", { p_slug: slug });
  if (error) throw error;
  return data;
}
