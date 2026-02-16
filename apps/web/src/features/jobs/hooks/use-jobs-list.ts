"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";

import { JobsQueryParams } from "@/types/jobs";

import { fetchJobsList } from "../lib/api";

export function useJobsList(params: JobsQueryParams) {
  const queryClient = useQueryClient();
  const page = params.page ?? 1;
  const pageSize = params.page_size ?? 20;

  const query = useQuery({
    queryKey: ["jobs", params],
    queryFn: () => fetchJobsList(params),
    placeholderData: (prev) => prev
  });

  useEffect(() => {
    if (!query.data) {
      return;
    }
    const totalPages = Math.max(1, Math.ceil(query.data.total / pageSize));
    const nextPage = page + 1;
    if (nextPage <= totalPages) {
      const nextParams = { ...params, page: nextPage };
      void queryClient.prefetchQuery({
        queryKey: ["jobs", nextParams],
        queryFn: () => fetchJobsList(nextParams)
      });
    }
  }, [query.data, queryClient, params, page, pageSize]);

  return query;
}
