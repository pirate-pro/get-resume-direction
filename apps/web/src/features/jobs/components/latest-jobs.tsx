"use client";

import Link from "next/link";
import { useMemo } from "react";

import { EmptyState } from "@/components/states/empty-state";
import { LoadingState } from "@/components/states/loading-state";
import { formatSalary } from "@/lib/utils";

import { useJobsList } from "../hooks/use-jobs-list";

export function LatestJobs(): JSX.Element {
  const params = useMemo(() => ({ page: 1, page_size: 6, sort_by: "time" as const }), []);
  const query = useJobsList(params);

  if (query.isLoading) {
    return <LoadingState label="最新职位加载中..." />;
  }

  if (!query.data || query.data.items.length === 0) {
    return <EmptyState title="暂时没有最新职位" description="请先触发爬取任务生成数据。" />;
  }

  return (
    <div className="grid gap-3 md:grid-cols-2">
      {query.data.items.map((job) => (
        <Link key={job.id} href={`/jobs/${job.id}`} className="card transition hover:-translate-y-0.5 hover:border-brand-200">
          <h3 className="text-base font-bold text-brand-700">{job.title}</h3>
          <p className="mt-1 text-sm text-slate-600">
            {job.company_name} · {job.city || "未知城市"}
          </p>
          <p className="mt-2 text-sm text-slate-700">
            {formatSalary(job.salary_min, job.salary_max, job.salary_currency || "CNY", job.salary_period || "month")}
          </p>
        </Link>
      ))}
    </div>
  );
}
