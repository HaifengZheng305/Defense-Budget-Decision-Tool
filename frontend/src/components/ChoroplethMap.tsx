import { useEffect, useMemo, useRef, useState } from "react";
import { ComposableMap, Geographies, Geography } from "react-simple-maps";
import { scaleSequential } from "d3-scale";
import { interpolateBlues } from "d3-scale-chromatic";
import { getAllCountrySignals, getMapMetric } from "../api";
import { CountryLatestSignals, MapMetric, MapMetricItem, MapMetricResponse } from "../types";

const GEO_URL = "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json";

type HoverInfo = {
  x: number;
  y: number;
  countryId: number;
  iso3?: string | null;
  name: string;
  value?: number | null;
  signals?: CountryLatestSignals;
  flags?: string[];
};

export default function ChoroplethMap() {
  const [metric, setMetric] = useState<MapMetric>("cagr_5y_pct");
  const [data, setData] = useState<MapMetricResponse | null>(null);
  const [hover, setHover] = useState<HoverInfo | null>(null);
  const [debugLast, setDebugLast] = useState<string>("(none)");
  const cacheRef = useRef<Map<number, { signals: CountryLatestSignals; flags: string[] }>>(new Map());
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [allLoaded, setAllLoaded] = useState<boolean>(false);

  useEffect(() => {
    getMapMetric(metric).then(setData).catch(console.error);
  }, [metric]);

  useEffect(() => {
    getAllCountrySignals()
      .then((resp) => {
        resp.items.forEach((it) => {
          cacheRef.current.set(it.latest_signals.country_id, {
            signals: it.latest_signals,
            flags: it.signal_flags
          });
        });
        setAllLoaded(true);
      })
      .catch((e) => {
        console.error(e);
        setAllLoaded(false);
      });
  }, []);

  function normalizeName(s: string): string {
    const base = s
      .toLowerCase()
      .replace(/&/g, "and")
      .replace(/\./g, "")
      .replace(/,/g, "")
      .replace(/'/g, "")
      .replace(/\s+/g, " ")
      .trim();

    const aliases: Record<string, string> = {
      "united states of america": "united states",
      "russian federation": "russia",
      "iran (islamic republic of)": "iran",
      "viet nam": "vietnam",
      "bolivia (plurinational state of)": "bolivia",
      "venezuela (bolivarian republic of)": "venezuela",
      "tanzania united republic of": "tanzania",
      "democratic republic of the congo": "congo, dem rep",
      "republic of the congo": "congo",
      "syrian arab republic": "syria",
      "lao peoples democratic republic": "laos",
      "korea republic of": "south korea",
      "korea democratic peoples republic of": "north korea"
    };

    return aliases[base] ?? base;
  }

  function pickIso3(props: any): string | undefined {
    const candidates = [
      props?.ISO_A3,
      props?.ADM0_A3,
      props?.iso_a3,
      props?.adm0_a3,
      props?.SOV_A3
    ].filter(Boolean) as string[];

    const iso = candidates.find((c) => c && c !== "-99");
    return iso;
  }

  const { isoToItem, nameToItem } = useMemo(() => {
    const isoMap = new Map<string, MapMetricItem>();
    const nameMap = new Map<string, MapMetricItem>();

    data?.items.forEach((it) => {
      if (it.iso3) {
        isoMap.set(it.iso3.toUpperCase(), it);
      }
      nameMap.set(normalizeName(it.country_name), it);
    });

    return { isoToItem: isoMap, nameToItem: nameMap };
  }, [data]);

  const values = useMemo(
    () => (data?.items.map((i) => i.value ?? 0).filter((v) => v != null) as number[]) || [],
    [data]
  );

  const [min, max] = useMemo(() => {
    if (!values.length) return [0, 0];
    const vmin = Math.min(...values);
    const vmax = Math.max(...values);
    return [vmin, vmax];
  }, [values]);

  const colorScale = useMemo(() => scaleSequential(interpolateBlues).domain([min, max]), [min, max]);

  function resolveCountryMatch(geo: any): MapMetricItem | undefined {
    const props = geo?.properties ?? {};
    const geoName = (props.name ?? props.NAME) as string | undefined;
    const iso = pickIso3(props)?.toUpperCase();

    if (iso && isoToItem.has(iso)) {
      return isoToItem.get(iso);
    }

    if (geoName) {
      return nameToItem.get(normalizeName(geoName));
    }

    return undefined;
  }

  function toContainerCoords(evt: React.MouseEvent): { x: number; y: number } {
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return { x: evt.clientX, y: evt.clientY };
    return { x: evt.clientX - rect.left, y: evt.clientY - rect.top };
  }

  function handleHover(evt: React.MouseEvent, geo: any) {
    const geoName = (geo?.properties?.name ?? geo?.properties?.NAME ?? "(unknown)") as string;

    if (normalizeName(geoName) === "antarctica") {
      setDebugLast("Antarctica ignored");
      setHover(null);
      return;
    }

    const item = resolveCountryMatch(geo);
    const iso = pickIso3(geo?.properties);

    setDebugLast(`${geoName} | iso=${iso ?? "none"} | ${item ? "matched" : "no-match"}`);

    const p = toContainerCoords(evt);

    if (!item) {
      setHover({
        x: p.x,
        y: p.y,
        countryId: -1,
        iso3: iso ?? null,
        name: geoName,
        value: undefined
      });
      return;
    }

    const cached = cacheRef.current.get(item.country_id);

    setHover({
      x: p.x,
      y: p.y,
      countryId: item.country_id,
      iso3: item.iso3 ?? iso ?? null,
      name: item.country_name,
      value: item.value,
      signals: cached?.signals,
      flags: cached?.flags
    });
  }

  function handleLeave() {
    setHover(null);
  }

  return (
    <div className="map-container" ref={containerRef}>
      <div className="controls">
        <label>
          Metric:
          <select value={metric} onChange={(e) => setMetric(e.target.value as MapMetric)}>
            <option value="cagr_5y_pct">5Y CAGR (%)</option>
            <option value="yoy_latest_pct">YoY growth (%)</option>
            <option value="spending_usd">Spending (USD)</option>
            <option value="share_global_pct">Share of global (%)</option>
            <option value="gdp_percent">Spending as % GDP</option>
            <option value="volatility_5y">Volatility (5Y YoY% stddev)</option>
            <option value="rank">Rank (latest)</option>
            <option value="rank_change_5y">Rank change (5Y)</option>
          </select>
        </label>

        <div className="legend">
          <span>Low</span>
          <div className="gradient" />
          <span>High</span>
        </div>
      </div>

      <ComposableMap projectionConfig={{ scale: 145 }}>
        <Geographies geography={GEO_URL}>
          {({ geographies }: { geographies: any[] }) =>
            geographies.map((geo: any) => {
              const item = resolveCountryMatch(geo);
              const fill = item && typeof item.value === "number" ? colorScale(item.value) : "#EEE";

              return (
                <Geography
                  key={geo.rsmKey}
                  geography={geo}
                  onMouseEnter={(evt: any) => handleHover(evt, geo)}
                  onMouseMove={(evt: any) => handleHover(evt, geo)}
                  onMouseLeave={handleLeave}
                  style={{
                    default: { fill, outline: "none" },
                    hover: { fill, outline: "none", stroke: "#222", strokeWidth: 0.6 },
                    pressed: { fill, outline: "none" }
                  }}
                />
              );
            })
          }
        </Geographies>
      </ComposableMap>

      <div className="debug-bar">data: {allLoaded ? "loaded" : "loading…"} | hover: {debugLast}</div>

      {hover && (
        <div className="tooltip" style={{ left: hover.x + 12, top: hover.y + 12 }}>
          <div className="tt-title">{hover.name}</div>

          {typeof hover.value === "number" && (
            <div className="tt-row">
              <span className="k">Map metric</span>
              <span className="v">
                {hover.value.toLocaleString(undefined, { maximumFractionDigits: 2 })}
              </span>
            </div>
          )}

          {hover.iso3 && (
            <div className="tt-row">
              <span className="k">ISO3</span>
              <span className="v">{hover.iso3}</span>
            </div>
          )}

          {hover.signals && (
            <>
              <div className="tt-row">
                <span className="k">Year</span>
                <span className="v">{hover.signals.year}</span>
              </div>

              <div className="tt-row">
                <span className="k">Spending (USD, millions)</span>
                <span className="v">
                  {typeof hover.signals.spending_usd === "number"
                    ? hover.signals.spending_usd.toLocaleString(undefined, {
                        maximumFractionDigits: 0
                      })
                    : ""}
                </span>
              </div>

              <div className="tt-row">
                <span className="k">YoY %</span>
                <span className="v">
                  {typeof hover.signals.yoy_latest_pct === "number"
                    ? hover.signals.yoy_latest_pct.toFixed(1)
                    : ""}
                </span>
              </div>

              <div className="tt-row">
                <span className="k">5Y CAGR %</span>
                <span className="v">
                  {typeof hover.signals.cagr_5y_pct === "number"
                    ? hover.signals.cagr_5y_pct.toFixed(1)
                    : ""}
                </span>
              </div>

              <div className="tt-row">
                <span className="k">% GDP</span>
                <span className="v">
                  {typeof hover.signals.gdp_percent === "number"
                    ? hover.signals.gdp_percent.toFixed(1)
                    : ""}
                </span>
              </div>

              <div className="tt-row">
                <span className="k">Share global %</span>
                <span className="v">
                  {typeof hover.signals.share_global_pct === "number"
                    ? hover.signals.share_global_pct.toFixed(2)
                    : ""}
                </span>
              </div>

              <div className="tt-row">
                <span className="k">Rank</span>
                <span className="v">
                  {hover.signals.rank}
                  {" ("}
                  {hover.signals.rank_change_5y != null
                    ? `${hover.signals.rank_change_5y > 0 ? "+" : ""}${hover.signals.rank_change_5y}`
                    : ""}
                  {")"}
                </span>
              </div>

              {!!hover.flags?.length && (
                <div className="tt-flags">
                  {hover.flags.map((f) => (
                    <span className="flag" key={f}>
                      {f.replace(/_/g, " ")}
                    </span>
                  ))}
                </div>
              )}
            </>
          )}

          {!hover.signals && <div className="muted">Loading signals…</div>}
        </div>
      )}
    </div>
  );
}