import type { Metadata } from "next";

import { OrdersPanel } from "@/features/orders/components/orders-panel";

export const metadata: Metadata = {
  title: "订单中心",
  description: "创建线下代投订单，管理校园投递服务。"
};

export default function OrdersPage(): JSX.Element {
  return (
    <div className="space-y-4">
      <header>
        <h1 className="text-2xl font-black text-brand-700">订单中心</h1>
        <p className="text-sm text-slate-600">先打通下单链路，后续可接支付、履约跟踪与微信小程序。</p>
      </header>
      <OrdersPanel />
    </div>
  );
}
