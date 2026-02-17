export interface EventsQueryParams {
  page?: number;
  page_size?: number;
  sort_by?: "time" | "recent";
  keyword?: string;
  city?: string;
  school?: string;
  company?: string;
  event_type?: string;
  source?: string;
}

export interface CampusEventListItem {
  id: number;
  title: string;
  company_name?: string | null;
  school_name?: string | null;
  city?: string | null;
  venue?: string | null;
  starts_at?: string | null;
  event_type: string;
  event_status: string;
  source_code: string;
  source_url: string;
}

export interface CampusEventsListResult {
  items: CampusEventListItem[];
  page: number;
  page_size: number;
  total: number;
}

export interface CampusEventDetail extends CampusEventListItem {
  province?: string | null;
  ends_at?: string | null;
  description?: string | null;
  tags: string[];
  registration_url?: string | null;
}

export interface CampusEventStats {
  by_source: Array<{ source: string; count: number }>;
  by_city: Array<{ city: string; count: number }>;
  by_school: Array<{ school: string; count: number }>;
}
