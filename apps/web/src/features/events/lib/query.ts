import { EventsQueryParams } from "@/types/events";

export function parseEventsQueryParams(searchParams: URLSearchParams): EventsQueryParams {
  const toNumber = (value: string | null): number | undefined => {
    if (!value) {
      return undefined;
    }
    const parsed = Number(value);
    return Number.isNaN(parsed) ? undefined : parsed;
  };

  return {
    page: toNumber(searchParams.get("page")) ?? 1,
    page_size: toNumber(searchParams.get("page_size")) ?? 20,
    sort_by: (searchParams.get("sort_by") as EventsQueryParams["sort_by"]) ?? "time",
    keyword: searchParams.get("keyword") ?? undefined,
    city: searchParams.get("city") ?? undefined,
    school: searchParams.get("school") ?? undefined,
    company: searchParams.get("company") ?? undefined,
    event_type: searchParams.get("event_type") ?? undefined,
    source: searchParams.get("source") ?? undefined
  };
}

export function buildEventsQueryString(params: EventsQueryParams): string {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === "") {
      return;
    }
    search.set(key, String(value));
  });
  const query = search.toString();
  return query ? `?${query}` : "";
}
