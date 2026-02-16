"use client";

import { QueryCache, QueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

let client: QueryClient | undefined;

export function getQueryClient(): QueryClient {
  if (!client) {
    client = new QueryClient({
      defaultOptions: {
        queries: {
          staleTime: 60 * 1000,
          gcTime: 5 * 60 * 1000,
          retry: 1,
          refetchOnWindowFocus: false
        }
      },
      queryCache: new QueryCache({
        onError: (error) => {
          const message = error instanceof Error ? error.message : "Unknown request error";
          toast.error(message);
        }
      })
    });
  }
  return client;
}
