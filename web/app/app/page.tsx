import Link from "next/link";
import { redirect } from "next/navigation";
import { requireUser } from "@/lib/supabase/server";
import TopBar from "../TopBar";
import NewWaitlistForm from "./NewWaitlistForm";

export default async function AppHome() {
  const { supabase, user } = await requireUser();
  if (!user) redirect("/login");
  const { data: waitlists } = await supabase
    .from("waitlists").select("id, slug, product_name, created_at").order("created_at", { ascending: false });

  return (
    <>
      <TopBar signedIn />
      <main className="mx-auto w-full max-w-5xl space-y-8 px-4 py-8">
        <section>
          <h1 className="mb-4 text-2xl font-semibold">Your waitlists</h1>
          {waitlists?.length ? (
            <ul className="divide-y divide-gray-200 rounded-lg border border-gray-200">
              {waitlists.map((w) => (
                <li key={w.id}>
                  <Link href={`/app/w/${w.slug}`} className="flex items-center justify-between px-4 py-3 hover:bg-gray-50">
                    <span className="font-medium">{w.product_name}</span>
                    <span className="text-sm text-gray-500">/w/{w.slug} →</span>
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-gray-600">No waitlists yet. Create your first one below.</p>
          )}
        </section>
        <NewWaitlistForm />
      </main>
    </>
  );
}
