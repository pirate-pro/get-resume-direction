"use client";

import { EmptyState } from "@/components/states/empty-state";
import { ErrorState } from "@/components/states/error-state";
import { LoadingState } from "@/components/states/loading-state";
import { useEventStats } from "@/features/events/hooks/use-event-stats";

import { useStats } from "@/features/jobs/hooks/use-stats";

function listBlock(title: string, rows: Array<{ name: string; value: number }>): JSX.Element {
  return (
    <section className="card">
      <h2 className="text-lg font-bold text-brand-700">{title}</h2>
      <ul className="mt-3 space-y-2">
        {rows.map((row) => (
          <li key={`${title}-${row.name}`} className="flex items-center justify-between rounded-md bg-slate-50 px-3 py-2">
            <span className="text-sm text-slate-700">{row.name}</span>
            <span className="rounded-md bg-brand-100 px-2 py-1 text-xs font-semibold text-brand-700">{row.value}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}

export function StatsBoard(): JSX.Element {
  const jobsQuery = useStats();
  const eventsQuery = useEventStats();

  if (jobsQuery.isLoading || eventsQuery.isLoading) {
    return <LoadingState label="统计数据加载中..." />;
  }

  if (jobsQuery.isError) {
    return <ErrorState message={jobsQuery.error.message} retry={() => jobsQuery.refetch()} />;
  }

  if (eventsQuery.isError) {
    return <ErrorState message={eventsQuery.error.message} retry={() => eventsQuery.refetch()} />;
  }

  if (!jobsQuery.data || !eventsQuery.data) {
    return <EmptyState title="暂无统计数据" description="请先运行爬取任务生成统计信息。" />;
  }

  return (
    <div className="grid gap-4 lg:grid-cols-3">
      {listBlock(
        "职位按来源统计",
        jobsQuery.data.by_source.map((item) => ({ name: item.source, value: item.count }))
      )}
      {listBlock(
        "职位按城市统计",
        jobsQuery.data.by_city.map((item) => ({ name: item.city ?? "未知", value: item.count }))
      )}
      {listBlock(
        "职位按类别统计",
        jobsQuery.data.by_category.map((item) => ({ name: item.category, value: item.count }))
      )}
      {listBlock(
        "活动按来源统计",
        eventsQuery.data.by_source.map((item) => ({ name: item.source, value: item.count }))
      )}
      {listBlock(
        "活动按城市统计",
        eventsQuery.data.by_city.map((item) => ({ name: item.city, value: item.count }))
      )}
      {listBlock(
        "活动按学校统计",
        eventsQuery.data.by_school.map((item) => ({ name: item.school, value: item.count }))
      )}
    </div>
  );
}
