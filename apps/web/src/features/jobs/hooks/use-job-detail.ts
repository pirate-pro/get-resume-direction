"use client";

import { useQuery } from "@tanstack/react-query";

import { JobDetail } from "@/types/jobs";

import { fetchJobDetail } from "../lib/api";

export function useJobDetail(jobId: number, initialData?: JobDetail) {
  return useQuery({
    queryKey: ["job-detail", jobId],
    queryFn: () => fetchJobDetail(jobId),
    initialData,
    staleTime: 2 * 60 * 1000
  });
}
