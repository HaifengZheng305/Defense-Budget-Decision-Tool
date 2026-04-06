from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.country import Country
from app.models.historical_spending import HistoricalSpending


BASE_DIR = Path(__file__).resolve().parents[2]
EXCEL_PATH = BASE_DIR / "data" / "SIPRI-Milex-data-1949-2024_2.xlsx"
SOURCE_NAME = "SIPRI"

CURRENT_USD_SHEET = "Current US$"
GDP_SHARE_SHEET = "Share of GDP"
PER_CAPITA_SHEET = "Per capita"

TOP_LEVEL_REGIONS = {
    "Africa",
    "Americas",
    "Asia & Oceania",
    "Europe",
    "Middle East",
}

SUBREGIONS = {
    "North Africa",
    "sub-Saharan Africa",
    "Central America and the Caribbean",
    "North America",
    "South America",
    "Oceania",
    "South Asia",
    "East Asia",
    "South East Asia",
    "Central Asia",
    "Central Europe",
    "Eastern Europe",
    "Western Europe",
}


def normalize_year_column(col) -> int | None:
    if isinstance(col, int):
        return col

    if isinstance(col, float) and col.is_integer():
        return int(col)

    if isinstance(col, str):
        stripped = col.strip()
        if stripped.isdigit():
            return int(stripped)

    return None


def standardize_sheet_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Some SIPRI sheets come in with Unnamed:* columns even though the first row
    after skiprows=6 contains the real headers. This fixes that.
    """
    first_row = df.iloc[0].tolist()

    # If pandas did not pick up proper headers, rebuild them from the first row.
    if "Country" not in df.columns:
        df.columns = first_row
        df = df.iloc[1:].reset_index(drop=True)

    # Normalize the first two columns
    cols = list(df.columns)
    if len(cols) >= 2:
        cols[0] = "Country"
        cols[1] = "Notes"
        df.columns = cols

    return df


def clean_numeric(value):
    """
    SIPRI uses strings like "...", "xxx", etc.
    Convert usable values to float, otherwise return None.
    """
    if pd.isna(value):
        return None

    if isinstance(value, str):
        value = value.strip()
        if value in {"...", "..", ". .", "xxx", "XXXX", "nan", ""}:
            return None

    num = pd.to_numeric(value, errors="coerce")
    if pd.isna(num):
        return None

    return float(num)


def transform_metric_sheet(
    sheet_name: str,
    value_column_name: str,
) -> pd.DataFrame:
    # Read raw sheet with no assumed header
    raw_df = pd.read_excel(
        EXCEL_PATH,
        sheet_name=sheet_name,
        header=None,
        engine="openpyxl",
    )

    # Find the real header row: must contain "Country" and at least a few year-like values
    header_row_idx = None

    for idx in range(len(raw_df)):
        row_values = raw_df.iloc[idx].tolist()
        normalized = [str(v).strip() if pd.notna(v) else "" for v in row_values]

        has_country = "Country" in normalized
        year_count = sum(1 for v in row_values if normalize_year_column(v) is not None)

        if has_country and year_count >= 5:
            header_row_idx = idx
            break

    if header_row_idx is None:
        raise ValueError(f"Could not find header row in sheet: {sheet_name}")

    # Rebuild dataframe using detected header row
    df = raw_df.iloc[header_row_idx:].copy().reset_index(drop=True)
    df.columns = df.iloc[0]
    df = df.iloc[1:].reset_index(drop=True)

    df = standardize_sheet_columns(df)
    df = df.dropna(how="all")

    year_columns = [col for col in df.columns if normalize_year_column(col) is not None]
    if not year_columns:
        raise ValueError(
            f"No year columns found in sheet: {sheet_name}. "
            f"Columns seen: {list(df.columns)}"
        )

    rows = []
    current_region = None
    current_subregion = None

    for _, row in df.iterrows():
        raw_country = row.get("Country")

        if pd.isna(raw_country):
            continue

        label = str(raw_country).strip()

        if not label:
            continue

        if label in TOP_LEVEL_REGIONS:
            current_region = label
            current_subregion = None
            continue

        if label in SUBREGIONS:
            current_subregion = label
            continue

        country_name = label

        notes_value = None ##add in the future

        for year_col in year_columns:
            year = normalize_year_column(year_col)
            value = clean_numeric(row[year_col])

            if value is None:
                continue

            rows.append(
                {
                    "country": country_name,
                    "region": current_region,
                    "subregion": current_subregion,
                    "year": year,
                    value_column_name: value,
                    "source": SOURCE_NAME,
                    "notes": notes_value,
                }
            )

    result = pd.DataFrame(rows)

    if result.empty:
        raise ValueError(f"Transformation produced no usable rows for sheet: {sheet_name}")

    return result


def load_and_transform() -> pd.DataFrame:
    spending_df = transform_metric_sheet(
        sheet_name=CURRENT_USD_SHEET,
        value_column_name="spending_usd",
    )

    gdp_df = transform_metric_sheet(
        sheet_name=GDP_SHARE_SHEET,
        value_column_name="gdp_percent",
    )

    per_capita_df = transform_metric_sheet(
        sheet_name=PER_CAPITA_SHEET,
        value_column_name="per_capita",
    )

    merged = spending_df.merge(
        gdp_df[["country", "year", "gdp_percent"]],
        on=["country", "year"],
        how="left",
    ).merge(
        per_capita_df[["country", "year", "per_capita"]],
        on=["country", "year"],
        how="left",
    )

    if merged.empty:
        raise ValueError("Final merged SIPRI dataframe is empty.")

    return merged


def get_or_create_country(
    session: Session,
    name: str,
    region: str | None,
    subregion: str | None,
) -> Country:
    country = session.query(Country).filter(Country.name == name).first()

    if country:
        updated = False

        if not country.region and region:
            country.region = region
            updated = True

        if not country.subregion and subregion:
            country.subregion = subregion
            updated = True

        if updated:
            session.add(country)

        return country

    country = Country(
        name=name,
        iso3=None,
        region=region,
        subregion=subregion,
        nato_member=None,
    )
    session.add(country)
    session.flush()
    return country


def ingest() -> None:
    df_long = load_and_transform()
    print(f"Prepared {len(df_long)} historical spending rows.")

    session = SessionLocal()

    try:
        deleted = (
            session.query(HistoricalSpending)
            .filter(HistoricalSpending.source == SOURCE_NAME)
            .delete(synchronize_session=False)
        )
        print(f"Deleted {deleted} existing {SOURCE_NAME} rows.")

        country_cache: dict[str, Country] = {}

        for _, row in df_long.iterrows():
            country_name = row["country"]

            if country_name in country_cache:
                country = country_cache[country_name]
            else:
                country = get_or_create_country(
                    session=session,
                    name=country_name,
                    region=row["region"],
                    subregion=row["subregion"],
                )
                country_cache[country_name] = country

            spending = HistoricalSpending(
                country_id=country.id,
                year=int(row["year"]),
                spending_usd=float(row["spending_usd"]),
                gdp_percent=float(row["gdp_percent"]) if pd.notna(row["gdp_percent"]) else None,
                per_capita=float(row["per_capita"]) if pd.notna(row["per_capita"]) else None,
                source=row["source"],
                notes=None,
            )
            session.add(spending)

        session.commit()
        print("SIPRI ingestion complete.")
        print(f"Countries touched: {len(country_cache)}")
        print(f"Historical spending rows inserted: {len(df_long)}")

    except Exception as e:
        session.rollback()
        print("Ingestion failed:", e)
        raise

    finally:
        session.close()