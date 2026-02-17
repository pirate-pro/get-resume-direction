export interface CreateOrderRequest {
  user_name: string;
  phone: string;
  wechat_id?: string;
  school_name?: string;
  major?: string;
  graduation_year?: number;
  resume_url?: string;
  target_job_id?: number;
  target_event_id?: number;
  target_company_name?: string;
  target_source_url?: string;
  delivery_type?: "onsite_resume_delivery" | "online_apply_guidance";
  quantity?: number;
  note?: string;
  amount_cents?: number;
  currency?: string;
}

export interface CreateOrderResult {
  id: number;
  order_no: string;
  status: string;
  created_at: string;
}

export interface OrdersQueryParams {
  page?: number;
  page_size?: number;
  phone?: string;
}

export interface OrderListItem {
  id: number;
  order_no: string;
  user_name: string;
  phone: string;
  status: string;
  delivery_type: string;
  target_job_id?: number | null;
  target_event_id?: number | null;
  target_company_name?: string | null;
  amount_cents?: number | null;
  currency: string;
  created_at: string;
}

export interface OrdersListResult {
  items: OrderListItem[];
  page: number;
  page_size: number;
  total: number;
}
