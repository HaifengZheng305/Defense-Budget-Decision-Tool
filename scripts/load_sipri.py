import pandas as pd
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.country import Country
from app.models.defense_spending import DefenseSpending

EXCEL_PATH = "data/SIPRI-Milex-data-1949-2024_2.xlsx"
SHEET_NAME = "Current US$"
SOURCE_NAME = "SIPRI"


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


def load_and_transform() -> pd.DataFrame:
    # Header row starts on Excel row 6, so skip first 5 rows
    df = pd.read_excel(
        EXCEL_PATH,
        sheet_name=SHEET_NAME,
        skiprows=5,
        engine="openpyxl"
    )

    # Drop fully empty rows
    df = df.dropna(how="all")

    # Keep country column name clean
    df = df.rename(columns={"Country": "country", "Notes": "notes"})

    # Identify year columns
    year_columns = [col for col in df.columns if isinstance(col, int)]

    if not year_columns:
        raise ValueError("No year columns found in the SIPRI sheet.")

    rows = []
    current_region = None
    current_subregion = None

    for _, row in df.iterrows():
        raw_country = row.get("country")

        if pd.isna(raw_country):
            continue

        label = str(raw_country).strip()

        if not label:
            continue

        # Region row
        if label in TOP_LEVEL_REGIONS:
            current_region = label
            current_subregion = None
            continue

        # Subregion row
        if label in SUBREGIONS:
            current_subregion = label
            continue

        # Actual country row
        country_name = label

        for year in year_columns:
            raw_value = row[year]

            # SIPRI uses strings like "...", "xxx"
            amount = pd.to_numeric(raw_value, errors="coerce")
            if pd.isna(amount):
                continue

            rows.append(
                {
                    "country": country_name,
                    "region": current_region,
                    "subregion": current_subregion,
                    "year": int(year),
                    "spending_usd": float(amount),
                    "source": SOURCE_NAME,
                }
            )

    result = pd.DataFrame(rows)

    if result.empty:
        raise ValueError("Transformation produced no usable rows.")

    return result


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
    session.flush()  # gets country.id
    return country


def ingest():
    df_long = load_and_transform()
    print(f"Prepared {len(df_long)} defense spending rows.")

    session = SessionLocal()

    try:
        # Optional but smart:
        # remove old SIPRI rows so reruns don't duplicate data
        deleted = session.query(DefenseSpending).filter(
            DefenseSpending.source == SOURCE_NAME
        ).delete(synchronize_session=False)
        print(f"Deleted {deleted} existing {SOURCE_NAME} rows.")

        country_cache = {}

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

            spending = DefenseSpending(
                country_id=country.id,
                year=row["year"],
                spending_usd=row["spending_usd"],
                source=row["source"],
            )
            session.add(spending)

        session.commit()
        print("SIPRI ingestion complete.")

        print(f"Countries touched: {len(country_cache)}")
        print(f"Defense spending rows inserted: {len(df_long)}")

    except Exception as e:
        session.rollback()
        print("Ingestion failed:", e)
        raise

    finally:
        session.close()


if __name__ == "__main__":
    ingest()