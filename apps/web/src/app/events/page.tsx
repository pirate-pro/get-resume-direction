import type { Metadata } from "next";

import { EventsListSection } from "@/features/events/components/events-list";

interface EventsPageProps {
  searchParams: Record<string, string | string[] | undefined>;
}

export function generateMetadata({ searchParams }: EventsPageProps): Metadata {
  const city = typeof searchParams.city === "string" ? searchParams.city : undefined;
  const keyword = typeof searchParams.keyword === "string" ? searchParams.keyword : undefined;
  const title = [city, keyword, "校园活动"].filter(Boolean).join(" - ");

  return {
    title: title || "校园活动",
    description: "查看校园宣讲会、双选会和招聘会，支持按学校与城市筛选。",
    alternates: { canonical: "/events" }
  };
}

export default function EventsPage(): JSX.Element {
  return (
    <div className="space-y-4">
      <header>
        <h1 className="text-2xl font-black text-brand-700">校园活动</h1>
        <p className="text-sm text-slate-600">聚合宣讲会/双选会信息，支持筛选并直接创建代投订单。</p>
      </header>
      <EventsListSection />
    </div>
  );
}
