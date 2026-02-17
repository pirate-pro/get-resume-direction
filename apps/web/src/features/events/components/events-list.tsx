"use client";

import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useMemo } from "react";

import { EmptyState } from "@/components/states/empty-state";
import { ErrorState } from "@/components/states/error-state";
import { LoadingState } from "@/components/states/loading-state";
import { Pagination } from "@/components/ui/pagination";
import { formatDate } from "@/lib/utils";

import { useDebouncedValue } from "../../jobs/hooks/use-debounced-value";
import { useEventsList } from "../hooks/use-events-list";
import { buildEventsQueryString, parseEventsQueryParams } from "../lib/query";
import { EventsFilterForm } from "./events-filter-form";

const EVENT_TYPE_LABELS: Record<string, string> = {
  talk: "宣讲会",
  job_fair: "招聘会",
  interchoice: "双选会",
  company_event: "企业活动"
};

export function EventsListSection(): JSX.Element {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const queryParams = useMemo(
    () => parseEventsQueryParams(new URLSearchParams(searchParams.toString())),
    [searchParams]
  );
  const debouncedKeyword = useDebouncedValue(queryParams.keyword, 300);

  const query = useEventsList({ ...queryParams, keyword: debouncedKeyword });

  const pushQuery = (next: ReturnType<typeof parseEventsQueryParams>) => {
    const nextStr = buildEventsQueryString(next);
    router.push(`${pathname}${nextStr}`, { scroll: false });
  };

  return (
    <section className="space-y-4">
      <EventsFilterForm initial={queryParams} onApply={pushQuery} />

      {query.isLoading ? <LoadingState label="校园活动加载中..." /> : null}
      {query.isError ? <ErrorState message={query.error.message} retry={() => query.refetch()} /> : null}

      {!query.isLoading && !query.isError && query.data ? (
        <>
          {query.data.items.length === 0 ? (
            <EmptyState title="暂无活动" description="试试切换城市、学校或关键词。" />
          ) : (
            <div className="grid gap-3">
              {query.data.items.map((event) => (
                <article key={event.id} className="card transition hover:-translate-y-0.5 hover:border-brand-200">
                  <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                    <div className="space-y-1">
                      <Link href={`/events/${event.id}`} className="text-lg font-bold text-brand-700 hover:underline">
                        {event.title}
                      </Link>
                      <p className="text-sm text-slate-700">
                        {event.company_name || "未知公司"} · {event.school_name || "未知学校"}
                      </p>
                      <p className="text-sm text-slate-600">
                        {event.city || "未知城市"} · {event.venue || "地点待更新"} · {formatDate(event.starts_at)}
                      </p>
                    </div>
                    <div className="flex flex-col items-start gap-2 md:items-end">
                      <span className="rounded-full bg-brand-50 px-3 py-1 text-xs text-brand-700">
                        {EVENT_TYPE_LABELS[event.event_type] || "校园活动"}
                      </span>
                      <Link
                        href={`/orders?event_id=${event.id}&company=${encodeURIComponent(event.company_name || "")}`}
                        className="btn-primary"
                      >
                        选择并下单代投
                      </Link>
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
