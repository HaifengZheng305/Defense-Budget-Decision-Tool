from typing import List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.schemas.spending import (
    MapMetricResponse,
    MapMetricItem,
    CountryLatestSignals,
    TimeSeriesPoint,
    TimeSeriesResponse,
)


ALLOWED_MAP_METRICS = {
    "spending_usd",
    "yoy_latest_pct",
    "cagr_5y_pct",
    "volatility_5y",
    "share_global_pct",
    "gdp_percent",
    "rank",
    "rank_change_5y",
}


def fetch_map_metric(session: Session, metric: str) -> MapMetricResponse:
    if metric not in ALLOWED_MAP_METRICS:
        raise ValueError(f"Unsupported metric: {metric}")

    sql = text(
        f"""
        SELECT country_id, country_name, iso3, {metric} AS value
        FROM vw_country_signal_latest
        """
    )
    rows = session.execute(sql).all()
    items = [
        MapMetricItem(
            country_id=row.country_id,
            country_name=row.country_name,
            iso3=row.iso3,
            value=row.value,
        )
        for row in rows
    ]
    return MapMetricResponse(metric=metric, items=items)


def fetch_country_latest_signals(session: Session, country_id: int) -> CountryLatestSignals:
    sql = text(
        """
        SELECT
            country_id,
            country_name,
            iso3,
            region,
            subregion,
            year,
            spending_usd,
            yoy_latest_pct,
            cagr_5y_pct,
            volatility_5y,
            share_global_pct,
            gdp_percent,
            rank,
            rank_change_5y
        FROM vw_country_signal_latest
        WHERE country_id = :country_id
        """
    )
    row = session.execute(sql, {"country_id": country_id}).one_or_none()
    if row is None:
        raise ValueError(f"Country {country_id} not found in signals view")

    return CountryLatestSignals(
        country_id=row.country_id,
        country_name=row.country_name,
        iso3=row.iso3,
        region=row.region,
        subregion=row.subregion,
        year=row.year,
        spending_usd=row.spending_usd,
        yoy_latest_pct=row.yoy_latest_pct,
        cagr_5y_pct=row.cagr_5y_pct,
        volatility_5y=row.volatility_5y,
        share_global_pct=row.share_global_pct,
        gdp_percent=row.gdp_percent,
        rank=row.rank,
        rank_change_5y=row.rank_change_5y,
    )


def flags_from_row(row) -> List[str]:
    flags: List[str] = []
    if getattr(row, "rapid_growth_flag", False):
        flags.append("rapid_growth")
    if getattr(row, "high_volatility_flag", False):
        flags.append("high_volatility")
    if getattr(row, "elevated_gdp_burden_flag", False):
        flags.append("elevated_burden_pct_gdp")
    if getattr(row, "rising_rank_flag", False):
        flags.append("rank_rising")
    if getattr(row, "declining_rank_flag", False):
        flags.append("rank_falling")
    if getattr(row, "stable_major_spender_flag", False):
        flags.append("stable_high_spender")
    return flags


def fetch_country_signal_flags(session: Session, country_id: int) -> List[str]:
    sql = text(
        """
        SELECT *
        FROM vw_country_signal_flags
        WHERE country_id = :country_id
        """
    )
    row = session.execute(sql, {"country_id": country_id}).one_or_none()
    if row is None:
        return []
    return flags_from_row(row)


def fetch_timeseries(session: Session, country_id: int) -> TimeSeriesResponse:
    sql = text(
        """
        SELECT year, spending_usd, gdp_percent, per_capita
        FROM historical_spending
        WHERE country_id = :country_id AND source = 'SIPRI'
        ORDER BY year
        """
    )
    rows = session.execute(sql, {"country_id": country_id}).all()
    points = [
        TimeSeriesPoint(
            year=row.year,
            spending_usd=row.spending_usd,
            gdp_percent=row.gdp_percent,
            per_capita=row.per_capita,
        )
        for row in rows
    ]
    return TimeSeriesResponse(country_id=country_id, points=points)
