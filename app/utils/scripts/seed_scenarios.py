from app.core.database import SessionLocal
from app.models.strategic_scenario import StrategicScenario, ScenarioAssumption


SCENARIOS = [
    {
        "name": "Peer Conflict",
        "description": "High-intensity competition and potential conflict against a near-peer adversary.",
        "threat_assumptions": (
            "Assumes elevated risk of major-power conflict, contested logistics, "
            "accelerated force modernization, and the need for high-end deterrence."
        ),
        "planning_horizon_years": 5,
        "budget_growth_assumption": 0.04,
        "assumptions": {
            "inflation_rate": 0.025,
            "baseline_budget_growth": 0.04,
            "threat_weight": 0.95,
            "modernization_weight": 0.90,
            "readiness_weight": 0.85,
            "procurement_delay_risk": 0.40,
            "personnel_cost_growth": 0.03,
            "notes": "Prioritizes deterrence, survivability, advanced procurement, and force readiness.",
        },
    },
    {
        "name": "Indo-Pacific Deterrence",
        "description": "Focuses on distributed posture, maritime resilience, and long-range deterrence in the Indo-Pacific.",
        "threat_assumptions": (
            "Assumes sustained regional competition, emphasis on maritime and air superiority, "
            "missile threats, and alliance interoperability."
        ),
        "planning_horizon_years": 7,
        "budget_growth_assumption": 0.035,
        "assumptions": {
            "inflation_rate": 0.025,
            "baseline_budget_growth": 0.035,
            "threat_weight": 0.85,
            "modernization_weight": 0.88,
            "readiness_weight": 0.80,
            "procurement_delay_risk": 0.35,
            "personnel_cost_growth": 0.028,
            "notes": "Bias toward naval, missile defense, cyber, space, and forward readiness investment.",
        },
    },
    {
        "name": "Budget-Constrained Readiness",
        "description": "Protects core readiness under tight fiscal conditions and limited topline growth.",
        "threat_assumptions": (
            "Assumes moderate threat environment but severe budget pressure, forcing hard tradeoffs "
            "between near-term readiness and long-term modernization."
        ),
        "planning_horizon_years": 5,
        "budget_growth_assumption": 0.01,
        "assumptions": {
            "inflation_rate": 0.025,
            "baseline_budget_growth": 0.01,
            "threat_weight": 0.65,
            "modernization_weight": 0.45,
            "readiness_weight": 0.95,
            "procurement_delay_risk": 0.55,
            "personnel_cost_growth": 0.03,
            "notes": "Protects sustainment and readiness first; modernization is slower and more selective.",
        },
    },
    {
        "name": "Rapid Modernization",
        "description": "Aggressively shifts resources toward next-generation capability development and procurement.",
        "threat_assumptions": (
            "Assumes adversary capability growth is outpacing legacy force structure, requiring accelerated "
            "investment in advanced technologies and force redesign."
        ),
        "planning_horizon_years": 8,
        "budget_growth_assumption": 0.05,
        "assumptions": {
            "inflation_rate": 0.025,
            "baseline_budget_growth": 0.05,
            "threat_weight": 0.80,
            "modernization_weight": 1.00,
            "readiness_weight": 0.70,
            "procurement_delay_risk": 0.45,
            "personnel_cost_growth": 0.027,
            "notes": "Accepts some near-term friction in exchange for faster capability transition.",
        },
    },
]


def upsert_scenario(session, scenario_data: dict) -> None:
    scenario = (
        session.query(StrategicScenario)
        .filter(StrategicScenario.name == scenario_data["name"])
        .first()
    )

    if scenario is None:
        scenario = StrategicScenario(
            name=scenario_data["name"],
            description=scenario_data["description"],
            threat_assumptions=scenario_data["threat_assumptions"],
            planning_horizon_years=scenario_data["planning_horizon_years"],
            budget_growth_assumption=scenario_data["budget_growth_assumption"],
        )
        session.add(scenario)
        session.flush()
    else:
        scenario.description = scenario_data["description"]
        scenario.threat_assumptions = scenario_data["threat_assumptions"]
        scenario.planning_horizon_years = scenario_data["planning_horizon_years"]
        scenario.budget_growth_assumption = scenario_data["budget_growth_assumption"]

    assumptions_data = scenario_data["assumptions"]

    if scenario.assumptions is None:
        scenario.assumptions = ScenarioAssumption(
            inflation_rate=assumptions_data["inflation_rate"],
            baseline_budget_growth=assumptions_data["baseline_budget_growth"],
            threat_weight=assumptions_data["threat_weight"],
            modernization_weight=assumptions_data["modernization_weight"],
            readiness_weight=assumptions_data["readiness_weight"],
            procurement_delay_risk=assumptions_data["procurement_delay_risk"],
            personnel_cost_growth=assumptions_data["personnel_cost_growth"],
            notes=assumptions_data["notes"],
        )
    else:
        scenario.assumptions.inflation_rate = assumptions_data["inflation_rate"]
        scenario.assumptions.baseline_budget_growth = assumptions_data["baseline_budget_growth"]
        scenario.assumptions.threat_weight = assumptions_data["threat_weight"]
        scenario.assumptions.modernization_weight = assumptions_data["modernization_weight"]
        scenario.assumptions.readiness_weight = assumptions_data["readiness_weight"]
        scenario.assumptions.procurement_delay_risk = assumptions_data["procurement_delay_risk"]
        scenario.assumptions.personnel_cost_growth = assumptions_data["personnel_cost_growth"]
        scenario.assumptions.notes = assumptions_data["notes"]


def seed_scenarios() -> None:
    session = SessionLocal()

    try:
        for scenario_data in SCENARIOS:
            upsert_scenario(session, scenario_data)

        session.commit()
        print(f"Seeded {len(SCENARIOS)} scenarios successfully.")

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()
