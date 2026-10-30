import Link from "next/link";

export default function TopBar({ signedIn }: { signedIn?: boolean }) {
  return (
    <header className="border-b border-gray-200">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
        <Link href="/" aria-label="Proof of Demand home" className="flex items-center gap-2.5">
          <svg width="26" height="26" viewBox="0 0 48 48" aria-hidden="true" stroke="currentColor" strokeWidth="7" strokeLinecap="round">
            <line x1="7.5" y1="7" x2="40.5" y2="7" />
            <line x1="12.5" y1="18" x2="35.5" y2="18" />
            <line x1="17.5" y1="29" x2="30.5" y2="29" />
            <circle cx="24" cy="41" r="5" fill="currentColor" stroke="none" />
          </svg>
          <span className="text-lg font-bold leading-none tracking-[-0.055em]">
            proof <span className="font-normal text-gray-500">of</span> demand
          </span>
        </Link>
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
