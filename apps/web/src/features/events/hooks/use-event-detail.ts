"use client";

import { useQuery } from "@tanstack/react-query";

import { CampusEventDetail } from "@/types/events";

import { fetchEventDetail } from "../lib/api";

export function useEventDetail(eventId: number, initialData?: CampusEventDetail) {
  return useQuery({
    queryKey: ["campus-event-detail", eventId],
    queryFn: () => fetchEventDetail(eventId),
    initialData,
    staleTime: 2 * 60 * 1000
  });
}
