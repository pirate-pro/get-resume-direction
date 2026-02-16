import { httpGet } from "@/lib/http";
import { JobDetail, JobsListResult, JobsQueryParams } from "@/types/jobs";
import { BasicStats } from "@/types/stats";

export async function fetchJobsList(params: JobsQueryParams): Promise<JobsListResult> {
  return httpGet<JobsListResult>("/api/v1/jobs", params as Record<string, string | number | undefined>);
}

export async function fetchJobDetail(jobId: number): Promise<JobDetail> {
  return httpGet<JobDetail>(`/api/v1/jobs/${jobId}`);
}

export async function fetchStats(): Promise<BasicStats> {
  return httpGet<BasicStats>("/api/v1/stats/basic");
}
