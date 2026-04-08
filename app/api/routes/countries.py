from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import SessionLocal
from app.services.spending_service import (
    fetch_map_metric,
    fetch_country_latest_signals,
    fetch_country_signal_flags,
    fetch_timeseries,
    flags_from_row,
)
from app.schemas.spending import (
    MapMetricResponse,
    CountryPanelResponse,
    CountrySignalsAllResponse,
    CountrySignalsItem,
    CountryLatestSignals,
    TimeSeriesResponse,
    ArticlesResponse,
    ArticleItem,
    SummaryResponse,
)


router = APIRouter(prefix="/countries", tags=["countries"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/map-metric", response_model=MapMetricResponse)
def get_map_metric(metric: str = Query(...), db: Session = Depends(get_db)):
    try:
        return fetch_map_metric(db, metric)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/signals-all", response_model=CountrySignalsAllResponse)
def get_all_country_signals(db: Session = Depends(get_db)):
    # Single load for frontend: latest signals + flags for all countries
    signals_rows = db.execute(
        text(
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
            """
        )
    ).all()

    flags_rows = db.execute(text("SELECT * FROM vw_country_signal_flags")).all()
    flags_by_country = {r.country_id: flags_from_row(r) for r in flags_rows}

    items = []
    for r in signals_rows:
        latest = CountryLatestSignals(
            country_id=r.country_id,
            country_name=r.country_name,
            iso3=r.iso3,
            region=r.region,
            subregion=r.subregion,
            year=r.year,
            spending_usd=r.spending_usd,
            yoy_latest_pct=r.yoy_latest_pct,
            cagr_5y_pct=r.cagr_5y_pct,
            volatility_5y=r.volatility_5y,
            share_global_pct=r.share_global_pct,
            gdp_percent=r.gdp_percent,
            rank=r.rank,
            rank_change_5y=r.rank_change_5y,
        )
        items.append(
            CountrySignalsItem(
                latest_signals=latest,
                signal_flags=flags_by_country.get(r.country_id, []),
            )
        )

    return CountrySignalsAllResponse(items=items)


@router.get("/{country_id}/signals", response_model=CountryPanelResponse)
def get_country_signals(country_id: int, db: Session = Depends(get_db)):
    latest = fetch_country_latest_signals(db, country_id)
    flags = fetch_country_signal_flags(db, country_id)
    return CountryPanelResponse(
        country={
            "id": latest.country_id,
            "name": latest.country_name,
            "iso3": latest.iso3,
            "region": latest.region,
            "subregion": latest.subregion,
        },
        latest_signals=latest,
        signal_flags=flags,
    )


@router.get("/{country_id}/timeseries", response_model=TimeSeriesResponse)
def get_country_timeseries(country_id: int, db: Session = Depends(get_db)):
    return fetch_timeseries(db, country_id)


@router.get("/{country_id}/articles", response_model=ArticlesResponse)
def get_country_articles(country_id: int, db: Session = Depends(get_db)):
    sql = text(
        """
        SELECT a.id, a.title, a.source_name, a.source_url, a.published_at, a.summary, a.topic_cluster
        FROM news_articles a
        JOIN article_country_mentions m ON m.article_id = a.id
        WHERE m.country_id = :country_id
        ORDER BY a.published_at DESC NULLS LAST, a.id DESC
        LIMIT 25
        """
    )
    rows = db.execute(sql, {"country_id": country_id}).all()
    items = [
        ArticleItem(
            id=row.id,
            title=row.title,
            source_name=row.source_name,
            source_url=row.source_url,
            published_at=row.published_at.isoformat() if row.published_at else None,
            summary=row.summary,
            topic_cluster=row.topic_cluster,
        )
        for row in rows
    ]
    return ArticlesResponse(country_id=country_id, items=items)


@router.get("/{country_id}/summary", response_model=SummaryResponse)
def get_country_summary(country_id: int, db: Session = Depends(get_db)):
    # Placeholder: Will be replaced by grounded AI summary using structured signals + retrieved articles
    latest = fetch_country_latest_signals(db, country_id)
    summary = (
        f"{latest.country_name} defense spending in {latest.year} was {latest.spending_usd:.0f} USD (millions)."
        if latest.spending_usd is not None
        else f"No recent spending data available for {latest.country_name}."
    )
    return SummaryResponse(country_id=country_id, summary=summary)
