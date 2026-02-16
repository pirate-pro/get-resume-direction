"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchStats } from "@/features/jobs/lib/api";

export function useStats() {
  return useQuery({
    queryKey: ["stats-basic"],
    queryFn: fetchStats
  });
}
