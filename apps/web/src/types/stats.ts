export interface CountBySource {
  source: string;
  count: number;
}

export interface CountByCity {
  city: string | null;
  count: number;
}

export interface CountByCategory {
  category: string;
  count: number;
}

export interface BasicStats {
  by_source: CountBySource[];
  by_city: CountByCity[];
  by_category: CountByCategory[];
}
