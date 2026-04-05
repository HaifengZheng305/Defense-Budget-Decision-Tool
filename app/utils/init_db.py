from app.core.database import Base, engine, create_views
from app.models.country import Country
from app.models.defense_spending import DefenseSpending
from app.utils.scripts.load_sipri import ingest

def init_db():
    Base.metadata.create_all(bind=engine)
    ingest()
    create_views()
    print("Tables created.")

if __name__ == "__main__":
    init_db()