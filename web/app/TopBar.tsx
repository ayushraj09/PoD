import Link from "next/link";

export default function TopBar({ signedIn }: { signedIn?: boolean }) {
  return (
    <header className="border-b border-gray-200">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
        <Link href="/" className="font-semibold">✓ Proof of Demand</Link>
        {signedIn ? (
          <form action="/auth/signout" method="post" className="flex items-center gap-4 text-sm">
            <Link href="/app" className="text-gray-600 hover:text-black">Dashboard</Link>
            <button className="rounded border border-gray-300 px-3 py-1 hover:bg-gray-50">Sign out</button>
          </form>
        ) : (
          <Link href="/login" className="text-sm text-gray-600 hover:text-black">Founder sign in</Link>
        )}
      </div>
    </header>
  );
}
