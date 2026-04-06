from app.core.database import Base, engine

# Import all models so Base knows about them
from app.models import (
    HistoricalSpending,
    BudgetCategory,
    StrategicScenario,
    ScenarioAssumption,
    AllocationPlanRun,
    AllocationPlanItem,
    Country,
)

from app.utils.scripts.seed_budget_categories import seed_budget_categories
from app.utils.scripts.seed_scenarios import seed_scenarios
from app.utils.scripts.ingest_sipri import ingest as ingest_sipri
from app.utils.scripts.data_clean_validate import clean_validate_data

def init_db(run_ingestion: bool = False):
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)

    print("Seeding budget categories...")
    seed_budget_categories()

    print("Seeding strategic scenarios...")
    seed_scenarios()

    if run_ingestion:
        print("Running SIPRI ingestion...")
        ingest_sipri()

    print("Cleaning and validating data...")
    clean_validate_data()

    print("Initialization complete.")


if __name__ == "__main__":
    # Set to True ONLY if you want to load SIPRI data
    init_db(run_ingestion=True)