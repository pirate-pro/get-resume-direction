import { RecommendationItem } from "@/types/recommendation";

export const mockRecommendations: RecommendationItem[] = [
  {
    id: 1024,
    title: "Backend Engineer",
    company_name: "NovaData",
    city: "Shanghai",
    reason: "Role and city preference match; skill overlap: Python/FastAPI/PostgreSQL.",
    score: 0.92
  },
  {
    id: 2048,
    title: "Data Platform Engineer",
    company_name: "Aster Analytics",
    city: "Beijing",
    reason: "Experience and salary range fit; skill overlap: ETL/Airflow.",
    score: 0.88
  }
];
