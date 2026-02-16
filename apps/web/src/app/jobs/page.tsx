import type { Metadata } from "next";

import { JobsListSection } from "@/features/jobs/components/jobs-list";

interface JobsPageProps {
  searchParams: Record<string, string | string[] | undefined>;
}

export function generateMetadata({ searchParams }: JobsPageProps): Metadata {
  const city = typeof searchParams.city === "string" ? searchParams.city : undefined;
  const keyword = typeof searchParams.keyword === "string" ? searchParams.keyword : undefined;

  const titleParts = [city, keyword, "Jobs"].filter(Boolean);
  const title = titleParts.join(" - ");

  const hasManyQueryParams = Object.keys(searchParams).length > 2;

  return {
    title: title || "Jobs",
    description: "Search aggregated job listings with city, salary, education and category filters.",
    alternates: {
      canonical: "/jobs"
    },
    robots: hasManyQueryParams
      ? {
          index: false,
          follow: true
        }
      : {
          index: true,
          follow: true
        }
  };
}

export default function JobsPage(): JSX.Element {
  return (
    <div className="space-y-4">
      <header>
        <h1 className="text-2xl font-black text-brand-700">Job List</h1>
        <p className="text-sm text-slate-600">URL-driven filters for shareable links and SEO-friendly pages.</p>
      </header>
      <JobsListSection />
    </div>
  );
}
