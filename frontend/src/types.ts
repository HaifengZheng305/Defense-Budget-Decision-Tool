export type MapMetric =
  | "spending_usd"
  | "yoy_latest_pct"
  | "cagr_5y_pct"
  | "volatility_5y"
  | "share_global_pct"
  | "gdp_percent"
  | "rank"
  | "rank_change_5y";

export interface MapMetricItem {
  country_id: number;
  country_name: string;
  iso3?: string | null;
  value?: number | null;
}

export interface MapMetricResponse {
  metric: MapMetric;
  items: MapMetricItem[];
}

export interface CountryLatestSignals {
  country_id: number;
  country_name: string;
  iso3?: string | null;
  region?: string | null;
  subregion?: string | null;
  year: number;
  spending_usd?: number | null;
  yoy_latest_pct?: number | null;
  cagr_5y_pct?: number | null;
  volatility_5y?: number | null;
  share_global_pct?: number | null;
  gdp_percent?: number | null;
  rank?: number | null;
  rank_change_5y?: number | null;
}
