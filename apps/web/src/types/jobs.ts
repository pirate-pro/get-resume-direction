export interface JobsQueryParams {
  page?: number;
  page_size?: number;
  sort_by?: "time" | "salary" | "relevance";
  keyword?: string;
  province?: string;
  city?: string;
  district?: string;
  category?: string;
  education?: string;
  experience_min?: number;
  salary_min?: number;
  salary_max?: number;
  industry?: string;
  source?: string;
}

export interface JobListItem {
  id: number;
  title: string;
  company_name: string;
  city?: string | null;
  salary_min?: number | null;
  salary_max?: number | null;
  salary_currency?: string | null;
  salary_period?: string | null;
  education_requirement?: string | null;
  published_at?: string | null;
  source_code: string;
}

export interface JobsListResult {
  items: JobListItem[];
  page: number;
  page_size: number;
  total: number;
}

export interface JobDetail extends JobListItem {
  source_url: string;
  job_category?: string | null;
  seniority?: string | null;
  responsibilities?: string | null;
  qualifications?: string | null;
  tags: string[];
  benefits: string[];
}
