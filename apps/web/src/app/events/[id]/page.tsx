import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { EventDetailSection } from "@/features/events/components/event-detail";
import { ApiResponse } from "@/types/api";
import { CampusEventDetail } from "@/types/events";

interface EventDetailPageProps {
  params: { id: string };
}

const REVALIDATE_SECONDS = 300;

async function fetchEventDetailServer(eventId: number): Promise<CampusEventDetail | null> {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  const res = await fetch(`${base.replace(/\/$/, "")}/api/v1/campus-events/${eventId}`, {
    next: { revalidate: REVALIDATE_SECONDS }
  });
  if (!res.ok) {
    return null;
  }
  const payload = (await res.json()) as ApiResponse<CampusEventDetail>;
  if (payload.code !== 0) {
    return null;
  }
  return payload.data;
}

export async function generateMetadata({ params }: EventDetailPageProps): Promise<Metadata> {
  const eventId = Number(params.id);
  if (Number.isNaN(eventId)) {
    return { title: "活动详情" };
  }

  const detail = await fetchEventDetailServer(eventId);
  if (!detail) {
    return { title: "活动详情" };
  }

  const title = `${detail.title}${detail.school_name ? ` | ${detail.school_name}` : ""}`;
  return {
    title,
    description: `${detail.company_name || "企业"} 校园活动详情，来源：${detail.source_code}。`,
    alternates: { canonical: `/events/${eventId}` }
  };
}

export default async function EventDetailPage({ params }: EventDetailPageProps): Promise<JSX.Element> {
  const eventId = Number(params.id);
  if (Number.isNaN(eventId)) {
    notFound();
  }

  const detail = await fetchEventDetailServer(eventId);
  if (!detail) {
    notFound();
  }

  return (
    <div className="space-y-4">
      <EventDetailSection eventId={eventId} initialData={detail} />
    </div>
  );
}
