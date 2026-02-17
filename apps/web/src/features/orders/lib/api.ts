import { httpGet, httpPost } from "@/lib/http";
import {
  CreateOrderRequest,
  CreateOrderResult,
  OrdersListResult,
  OrdersQueryParams
} from "@/types/orders";

export async function createOrder(payload: CreateOrderRequest): Promise<CreateOrderResult> {
  return httpPost<CreateOrderResult, CreateOrderRequest>("/api/v1/orders", payload);
}

export async function fetchOrders(params: OrdersQueryParams): Promise<OrdersListResult> {
  return httpGet<OrdersListResult>("/api/v1/orders", params as Record<string, string | number | undefined>);
}
