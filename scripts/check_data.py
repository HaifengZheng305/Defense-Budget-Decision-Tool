from app.core.database import SessionLocal
from app.models.country import Country
from app.models.defense_spending import DefenseSpending

session = SessionLocal()

print("Countries:", session.query(Country).count())
print("Defense rows:", session.query(DefenseSpending).count())

# sample rows
rows = session.query(DefenseSpending).limit(5).all()
rows_country = session.query(Country).limit(5).all()

for r in rows:
    print(r.country_id, r.year, r.spending_usd)
for r in rows_country:
    print(r.id, r.name, r.iso3, r.region, r.subregion, r.nato_member)

session.close()