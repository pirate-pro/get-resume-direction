"use client";

import Link from "next/link";

import { ErrorState } from "@/components/states/error-state";
import { LoadingState } from "@/components/states/loading-state";
import { formatDate } from "@/lib/utils";
import { CampusEventDetail } from "@/types/events";

import { useEventDetail } from "../hooks/use-event-detail";

const EVENT_TYPE_LABELS: Record<string, string> = {
  talk: "宣讲会",
  job_fair: "招聘会",
  interchoice: "双选会",
  company_event: "企业活动"
};

const EVENT_STATUS_LABELS: Record<string, string> = {
  upcoming: "进行中/待开始",
  done: "已结束"
};

interface EventDetailProps {
  eventId: number;
  initialData?: CampusEventDetail;
}

export function EventDetailSection({ eventId, initialData }: EventDetailProps): JSX.Element {
  const query = useEventDetail(eventId, initialData);

  if (query.isLoading) {
    return <LoadingState label="活动详情加载中..." />;
  }

  if (query.isError) {
    return <ErrorState message={query.error.message} retry={() => query.refetch()} />;
  }

  if (!query.data) {
    return <ErrorState message="活动详情不可用" />;
  }

  const event = query.data;
  return (
    <article className="space-y-4">
      <section className="card">
        <h1 className="text-2xl font-bold text-brand-700">{event.title}</h1>
        <p className="mt-1 text-sm text-slate-700">
          {event.company_name || "未知公司"} · {event.school_name || "未知学校"}
        </p>
        <p className="mt-1 text-sm text-slate-600">
          {event.city || "未知城市"} · {event.venue || "地点待更新"}
        </p>
        <p className="mt-1 text-sm text-slate-600">
          活动时间: {formatDate(event.starts_at)}
          {event.ends_at ? ` - ${formatDate(event.ends_at)}` : ""}
        </p>
        <p className="mt-1 text-sm text-slate-600">
          活动类型: {EVENT_TYPE_LABELS[event.event_type] || "校园活动"} · 状态:{" "}
          {EVENT_STATUS_LABELS[event.event_status] || event.event_status}
        </p>
        <p className="mt-1 text-sm text-slate-600">来源平台: {event.source_code}</p>
        <div className="mt-3 flex flex-wrap gap-2">
          {event.tags.map((tag) => (
            <span key={tag} className="rounded-full bg-brand-50 px-3 py-1 text-xs text-brand-700">
              {tag}
            </span>
          ))}
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          <a
            href={event.registration_url || event.source_url}
            target="_blank"
            rel="noopener noreferrer nofollow"
            className="btn-secondary"
          >
            查看来源活动页
          </a>
          <Link
            href={`/orders?event_id=${event.id}&company=${encodeURIComponent(event.company_name || "")}&source_url=${encodeURIComponent(
              event.registration_url || event.source_url
            )}`}
            className="btn-primary"
          >
            选择该活动并下单代投
          </Link>
        </div>
      </section>

      <section className="card">
        <h2 className="text-lg font-semibold">活动说明</h2>
        <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-700">{event.description || "暂无详情说明"}</p>
      </section>
    </article>
  );
}
