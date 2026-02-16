import type { Metadata } from "next";
import { Manrope, Space_Grotesk } from "next/font/google";

import { ErrorBoundary } from "@/components/error-boundary";
import { LayoutShell } from "@/components/layout-shell";
import { Providers } from "@/components/providers";
import "@/styles/globals.css";

const headingFont = Space_Grotesk({ subsets: ["latin"], variable: "--font-heading" });
const bodyFont = Manrope({ subsets: ["latin"], variable: "--font-body" });

export const metadata: Metadata = {
  title: {
    default: "China Job Aggregation Platform",
    template: "%s | Job Aggregation Platform"
  },
  description: "Campus and experienced hiring aggregation with searchable structured job data.",
  metadataBase: new URL("https://example.com")
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>): JSX.Element {
  return (
    <html lang="en" className={`${headingFont.variable} ${bodyFont.variable}`}>
      <body className="font-[var(--font-body)] antialiased">
        <Providers>
          <ErrorBoundary>
            <LayoutShell>{children}</LayoutShell>
          </ErrorBoundary>
        </Providers>
      </body>
    </html>
  );
}
