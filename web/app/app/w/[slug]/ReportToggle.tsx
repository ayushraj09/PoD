"use client";
import { useTransition } from "react";
import { setReportPublic } from "../../actions";

export default function ReportToggle({ waitlistId, slug, isPublic }: { waitlistId: string; slug: string; isPublic: boolean }) {
  const [pending, start] = useTransition();
  return (
    <label className="flex items-center gap-2 text-sm">
      <input type="checkbox" checked={isPublic} disabled={pending}
        onChange={(e) => start(() => setReportPublic(waitlistId, slug, e.target.checked))} />
      Report is public {pending && "…"}
    </label>
  );
}
