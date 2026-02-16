"use client";

import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useMemo } from "react";

import { EmptyState } from "@/components/states/empty-state";
import { ErrorState } from "@/components/states/error-state";
import { LoadingState } from "@/components/states/loading-state";
import { Pagination } from "@/components/ui/pagination";
import { formatDate, formatSalary } from "@/lib/utils";

import { useDebouncedValue } from "../hooks/use-debounced-value";
import { useJobsList } from "../hooks/use-jobs-list";
import { buildJobsQueryString, parseJobsQueryParams } from "../lib/query";
import { JobsFilterForm } from "./jobs-filter-form";

export function JobsListSection(): JSX.Element {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const queryParams = useMemo(
    () => parseJobsQueryParams(new URLSearchParams(searchParams.toString())),
    [searchParams]
  );
  const debouncedKeyword = useDebouncedValue(queryParams.keyword, 300);

  const query = useJobsList({ ...queryParams, keyword: debouncedKeyword });

  const pushQuery = (nextParams: ReturnType<typeof parseJobsQueryParams>) => {
    const next = buildJobsQueryString(nextParams);
    router.push(`${pathname}${next}`, { scroll: false });
  };

  return (
    <section className="space-y-4">
      <JobsFilterForm initial={queryParams} onApply={pushQuery} />

      {query.isLoading ? <LoadingState label="Loading jobs..." /> : null}
      {query.isError ? (
        <ErrorState message={query.error.message} retry={() => query.refetch()} />
      ) : null}

      {!query.isLoading && !query.isError && query.data ? (
        <>
          {query.data.items.length === 0 ? (
            <EmptyState title="No jobs found" description="Try adjusting filters or keyword." />
          ) : (
            <div className="grid gap-3">
              {query.data.items.map((job) => (
                <article key={job.id} className="card transition hover:-translate-y-0.5 hover:border-brand-200">
                  <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
                    <div>
                      <Link href={`/jobs/${job.id}`} className="text-lg font-bold text-brand-700 hover:underline">
                        {job.title}
                      </Link>
                      <p className="text-sm text-slate-600">
                        {job.company_name} · {job.city || "Unknown city"}
                      </p>
                      <p className="mt-1 text-sm text-slate-700">
                        {formatSalary(job.salary_min, job.salary_max, job.salary_currency || "CNY", job.salary_period || "month")}
                      </p>
                    </div>
                    <div className="text-right text-xs text-slate-500">
                      <p>Source: {job.source_code}</p>
                      <p>Published: {formatDate(job.published_at)}</p>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}

          <Pagination
            page={query.data.page}
            pageSize={query.data.page_size}
            total={query.data.total}
            onPageChange={(page) => pushQuery({ ...queryParams, page })}
          />
        </>
      ) : null}
    </section>
  );
}
