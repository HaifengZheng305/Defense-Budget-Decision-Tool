from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class MapMetricItem(BaseModel):
    country_id: int
    country_name: str
    iso3: Optional[str] = None
    value: Optional[float] = None


class MapMetricResponse(BaseModel):
    metric: Literal[
        "spending_usd",
        "yoy_latest_pct",
        "cagr_5y_pct",
        "volatility_5y",
        "share_global_pct",
        "gdp_percent",
        "rank",
        "rank_change_5y",
    ]
    items: List[MapMetricItem]


class CountryLatestSignals(BaseModel):
    country_id: int
    country_name: str
    iso3: Optional[str] = None
    region: Optional[str] = None
    subregion: Optional[str] = None
    year: int
    spending_usd: Optional[float] = None
    yoy_latest_pct: Optional[float] = None
    cagr_5y_pct: Optional[float] = None
    volatility_5y: Optional[float] = None
    share_global_pct: Optional[float] = None
    gdp_percent: Optional[float] = None
    rank: Optional[int] = None
    rank_change_5y: Optional[int] = None
    trend_classification: Optional[str] = Field(default=None)  # placeholder for future


class CountrySignalFlags(BaseModel):
    rapid_growth: bool
    high_volatility: bool
    elevated_gdp_burden: bool
    rising_rank: bool
    declining_rank: bool
    stable_major_spender: bool


class CountryPanelResponse(BaseModel):
    country: dict
    latest_signals: CountryLatestSignals
    signal_flags: List[str]


class CountrySignalsItem(BaseModel):
    latest_signals: CountryLatestSignals
    signal_flags: List[str]


class CountrySignalsAllResponse(BaseModel):
    items: List[CountrySignalsItem]


class TimeSeriesPoint(BaseModel):
    year: int
    spending_usd: Optional[float] = None
    gdp_percent: Optional[float] = None
    per_capita: Optional[float] = None


class TimeSeriesResponse(BaseModel):
    country_id: int
    points: List[TimeSeriesPoint]


class ArticleItem(BaseModel):
    id: int
    title: str
    source_name: Optional[str] = None
    source_url: str
    published_at: Optional[str] = None
    summary: Optional[str] = None
    topic_cluster: Optional[str] = None


class ArticlesResponse(BaseModel):
    country_id: int
    items: List[ArticleItem]


class SummaryResponse(BaseModel):
    country_id: int
    summary: str
