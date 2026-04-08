import axios from "axios";
import { CountryLatestSignals, MapMetric, MapMetricResponse } from "./types";

export async function getMapMetric(metric: MapMetric) : Promise<MapMetricResponse> {
  const res = await axios.get(`/countries/map-metric`, { params: { metric } });
  return res.data;
}

export async function getCountrySignals(countryId: number): Promise<{
  country: { id: number; name: string; iso3?: string; region?: string; subregion?: string };
  latest_signals: CountryLatestSignals;
  signal_flags: string[];
}> {
  const res = await axios.get(`/countries/${countryId}/signals`);
  return res.data;
}

export async function getAllCountrySignals(): Promise<{
  items: { latest_signals: CountryLatestSignals; signal_flags: string[] }[];
}> {
  const res = await axios.get(`/countries/signals-all`);
  return res.data;
}
