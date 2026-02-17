"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchEventStats } from "../lib/api";

export function useEventStats() {
  return useQuery({
    queryKey: ["campus-event-stats"],
    queryFn: fetchEventStats,
    staleTime: 5 * 60 * 1000
  });
}
