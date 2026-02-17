import { RecommendationItem } from "@/types/recommendation";

export const mockRecommendations: RecommendationItem[] = [
  {
    id: 1024,
    title: "后端开发工程师",
    company_name: "星海数据",
    city: "上海",
    reason: "岗位方向与城市偏好匹配，技能命中：Python/FastAPI/PostgreSQL。",
    score: 0.92
  },
  {
    id: 2048,
    title: "数据平台工程师",
    company_name: "辰析科技",
    city: "北京",
    reason: "经验与薪资区间匹配，技能命中：ETL/Airflow。",
    score: 0.88
  }
];
