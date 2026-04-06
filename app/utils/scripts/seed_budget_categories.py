from app.core.database import SessionLocal
from app.models.budget_category import BudgetCategory


BUDGET_CATEGORIES = [
    {
        "category_name": "Personnel",
        "description": "Military pay, benefits, and personnel-related costs.",
    },
    {
        "category_name": "Procurement",
        "description": "Acquisition of equipment, platforms, weapons, and systems.",
    },
    {
        "category_name": "Operations",
        "description": "Day-to-day operational costs, sustainment, logistics, and support.",
    },
    {
        "category_name": "R&D",
        "description": "Research, development, testing, and evaluation for future capabilities.",
    },
    {
        "category_name": "Readiness",
        "description": "Training, maintenance, force preparedness, and deployment readiness.",
    },
    {
        "category_name": "Cyber",
        "description": "Cybersecurity, cyber defense, offensive cyber capability, and resilience.",
    },
    {
        "category_name": "Space",
        "description": "Space-based defense systems, surveillance, communications, and resilience.",
    },
    {
        "category_name": "Missile Defense",
        "description": "Missile detection, tracking, interception, and defense architecture.",
    },
]


def seed_budget_categories() -> None:
    session = SessionLocal()

    try:
        inserted = 0
        updated = 0

        for item in BUDGET_CATEGORIES:
            existing = (
                session.query(BudgetCategory)
                .filter(BudgetCategory.category_name == item["category_name"])
                .first()
            )

            if existing:
                changed = False

                if existing.description != item["description"]:
                    existing.description = item["description"]
                    changed = True

                if existing.is_active is not True:
                    existing.is_active = True
                    changed = True

                if changed:
                    session.add(existing)
                    updated += 1

                continue

            category = BudgetCategory(
                category_name=item["category_name"],
                description=item["description"],
                is_active=True,
            )
            session.add(category)
            inserted += 1

        session.commit()
        print(f"Budget categories seeded. Inserted={inserted}, Updated={updated}")

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()