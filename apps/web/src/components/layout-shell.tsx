import Link from "next/link";
import { ReactNode } from "react";

const NAV_ITEMS = [
  { href: "/jobs", label: "Jobs" },
  { href: "/stats", label: "Stats" },
  { href: "/resume", label: "Resume" },
  { href: "/recommendations", label: "Recommendations" }
];

export function LayoutShell({ children }: { children: ReactNode }): JSX.Element {
  return (
    <div className="min-h-screen pb-10">
      <header className="border-b border-brand-100 bg-white/85 backdrop-blur">
        <div className="container-page flex h-16 items-center justify-between">
          <Link href="/" className="text-lg font-bold tracking-tight text-brand-700">
            Job Aggregation Platform
          </Link>
          <nav className="flex items-center gap-2">
            {NAV_ITEMS.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="rounded-md px-3 py-2 text-sm font-medium text-slate-700 transition hover:bg-brand-50 hover:text-brand-700"
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>
      <main className="container-page mt-8">{children}</main>
    </div>
  );
}
