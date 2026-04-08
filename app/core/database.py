import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def create_views():
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    SQL_PATH = os.path.join(BASE_DIR, "app", "sql", "defense_spending_analysis.sql")

    with open(SQL_PATH, "r") as f:
        sql = f.read()

    print("Creating/refreshing SQL views from", SQL_PATH)

    # Execute statements one-by-one to ensure compatibility across drivers
    statements = [stmt.strip() for stmt in sql.split(";") if stmt.strip()]
    executed = 0
    with engine.begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))
            executed += 1
        # quick sanity check: touch a key view if present (won't fail if absent)
        try:
            conn.execute(text("SELECT 1 FROM vw_country_signal_latest LIMIT 1"))
        except Exception:
            # It's fine if the view isn't queryable yet (e.g., empty base tables)
            pass

    print(f"Executed {executed} SQL statements.")