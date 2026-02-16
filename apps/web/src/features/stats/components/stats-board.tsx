"use client";

import { EmptyState } from "@/components/states/empty-state";
import { ErrorState } from "@/components/states/error-state";
import { LoadingState } from "@/components/states/loading-state";

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
  const query = useStats();

  if (query.isLoading) {
    return <LoadingState label="Loading stats..." />;
  }

  if (query.isError) {
    return <ErrorState message={query.error.message} retry={() => query.refetch()} />;
  }

  if (!query.data) {
    return <EmptyState title="No stats yet" description="Run crawler jobs to generate stats." />;
  }

  return (
    <div className="grid gap-4 lg:grid-cols-3">
      {listBlock(
        "By Source",
        query.data.by_source.map((item) => ({ name: item.source, value: item.count }))
      )}
      {listBlock(
        "By City",
        query.data.by_city.map((item) => ({ name: item.city ?? "unknown", value: item.count }))
      )}
      {listBlock(
        "By Category",
        query.data.by_category.map((item) => ({ name: item.category, value: item.count }))
      )}
    </div>
  );
}
