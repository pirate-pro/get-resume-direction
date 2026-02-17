import type { Metadata } from "next";

import { JobsListSection } from "@/features/jobs/components/jobs-list";

interface JobsPageProps {
  searchParams: Record<string, string | string[] | undefined>;
}

export function generateMetadata({ searchParams }: JobsPageProps): Metadata {
  const city = typeof searchParams.city === "string" ? searchParams.city : undefined;
  const keyword = typeof searchParams.keyword === "string" ? searchParams.keyword : undefined;

  const titleParts = [city, keyword, "职位列表"].filter(Boolean);
  const title = titleParts.join(" - ");

  const hasManyQueryParams = Object.keys(searchParams).length > 2;

  return {
    title: title || "职位列表",
    description: "按城市、薪资、学历、经验和岗位类别筛选聚合职位。",
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
        <h1 className="text-2xl font-black text-brand-700">职位列表</h1>
        <p className="text-sm text-slate-600">筛选条件与分页由 URL 驱动，便于分享与运营投放。</p>
      </header>
      <JobsListSection />
    </div>
  );
}
