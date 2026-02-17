"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { CreateOrderRequest, OrdersQueryParams } from "@/types/orders";

import { createOrder, fetchOrders } from "../lib/api";

export function useOrders(params: OrdersQueryParams) {
  return useQuery({
    queryKey: ["orders", params],
    queryFn: () => fetchOrders(params),
    staleTime: 60 * 1000
  });
}

export function useCreateOrder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateOrderRequest) => createOrder(payload),
    onSuccess: (data) => {
      toast.success(`订单已创建：${data.order_no}`);
      void queryClient.invalidateQueries({ queryKey: ["orders"] });
    }
  });
}
