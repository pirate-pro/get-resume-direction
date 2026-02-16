import { JobsQueryParams } from "@/types/jobs";

export function parseJobsQueryParams(searchParams: URLSearchParams): JobsQueryParams {
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
    sort_by: (searchParams.get("sort_by") as JobsQueryParams["sort_by"]) ?? "time",
    keyword: searchParams.get("keyword") ?? undefined,
    province: searchParams.get("province") ?? undefined,
    city: searchParams.get("city") ?? undefined,
    district: searchParams.get("district") ?? undefined,
    category: searchParams.get("category") ?? undefined,
    education: searchParams.get("education") ?? undefined,
    experience_min: toNumber(searchParams.get("experience_min")),
    salary_min: toNumber(searchParams.get("salary_min")),
    salary_max: toNumber(searchParams.get("salary_max")),
    industry: searchParams.get("industry") ?? undefined,
    source: searchParams.get("source") ?? undefined
  };
}

export function buildJobsQueryString(params: JobsQueryParams): string {
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
