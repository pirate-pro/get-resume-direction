import { httpGet } from "@/lib/http";
import {
  CampusEventDetail,
  CampusEventsListResult,
  CampusEventStats,
  EventsQueryParams
} from "@/types/events";

export async function fetchEventsList(params: EventsQueryParams): Promise<CampusEventsListResult> {
  return httpGet<CampusEventsListResult>("/api/v1/campus-events", params as Record<string, string | number | undefined>);
}

export async function fetchEventDetail(eventId: number): Promise<CampusEventDetail> {
  return httpGet<CampusEventDetail>(`/api/v1/campus-events/${eventId}`);
}

export async function fetchEventStats(): Promise<CampusEventStats> {
  return httpGet<CampusEventStats>("/api/v1/campus-events/stats/basic");
}
