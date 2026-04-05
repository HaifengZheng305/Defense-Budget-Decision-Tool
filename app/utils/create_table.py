from app.core.database import Base, engine
from app.models.country import Country
from app.models.defense_spending import DefenseSpending

def init_db():
    Base.metadata.create_all(bind=engine)
    print("Tables created.")

if __name__ == "__main__":
    init_db()