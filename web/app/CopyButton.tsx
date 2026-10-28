"use client";
import { useState } from "react";

export default function CopyButton({ text }: { text: string }) {
  const [done, setDone] = useState(false);
  return (
    <button
      type="button"
      onClick={() => navigator.clipboard.writeText(text).then(() => { setDone(true); setTimeout(() => setDone(false), 1500); })}
      className="shrink-0 rounded border border-gray-300 bg-white px-2 py-1 text-xs hover:bg-gray-50"
    >
      {done ? "Copied ✓" : "Copy"}
    </button>
  );
}

export function CodeBox({ label, code }: { label: string; code: string }) {
  return (
    <div>
      <div className="mb-1 text-xs font-medium text-gray-600">{label}</div>
      <div className="flex items-start gap-2 rounded bg-gray-50 p-2">
        <code className="flex-1 break-all text-xs">{code}</code>
        <CopyButton text={code} />
      </div>
    </div>
  );
}
