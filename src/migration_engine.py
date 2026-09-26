"""
QuantumShield v2 — Migration Planner (§8) & What-If Simulator (§13)

Per-asset migration planning with 11 phases.
What-If scenario comparison engine.
"""

from typing import Dict, Any, List
import random
from src.crypto_inventory import classify_algorithm
from src.risk_model import compute_risk_score, compute_agility_score


# §8.4 — Migration phases
MIGRATION_PHASES = {
    1: "Discover",
    2: "Classify",
    3: "Prioritize",
    4: "Test",
    5: "Deploy hybrid protection",
    6: "Rotate keys",
    7: "Re-encrypt data",
    8: "Migrate digital signatures",
    9: "Validate interoperability",
    10: "Retire legacy algorithms",
    11: "Monitor continuously",
}


def generate_migration_tasks(assets: List[Dict], seed: int = 42) -> List[Dict[str, Any]]:
    """
    Generate migration task records for all vulnerable assets (§8.3).
    """
    rng = random.Random(seed + 5000)
    tasks = []

    for idx, asset in enumerate(assets):
        algo = asset.get("algorithm", "Unknown")
        algo_info = classify_algorithm(algo)
        mig_status = asset.get("migration_status", "not-started")
        mig_target = asset.get("migration_target")

        # Only create tasks for assets that need migration
        if algo_info["category"] == "quantum-resilient" and mig_status == "completed":
            continue
        if not mig_target and algo_info["category"] == "quantum-resilient":
            continue

        task_id = f"mig-{len(tasks) + 1:04d}"

        # Determine phase based on migration status
        if mig_status == "completed":
            phase = 11
        elif mig_status == "deploying":
            phase = rng.choice([5, 6, 7, 8])
        elif mig_status == "testing":
            phase = 4
        elif mig_status == "planning":
            phase = rng.choice([2, 3])
        else:
            phase = 1

        # Dependencies
        deps = []
        if asset.get("asset_type") == "api":
            # APIs typically depend on their certificate/key store
            dep_count = rng.randint(0, 3)
            for d in range(dep_count):
                dep_idx = rng.randint(0, len(assets) - 1)
                deps.append(assets[dep_idx].get("asset_id", f"asset-{dep_idx:03d}"))

        # Compatibility risk
        complexity = asset.get("migration_complexity", "medium")
        compat_risk = {
            "low": rng.choice(["low", "low", "medium"]),
            "medium": rng.choice(["medium", "medium", "high"]),
            "high": rng.choice(["high", "high", "critical"]),
            "critical": "critical",
        }.get(complexity, "medium")

        # Testing requirements
        role = asset.get("algorithm_role", "unknown")
        testing = _generate_testing_requirements(role, algo, mig_target)

        # Rollback plan
        rollback = (
            f"Revert to {algo} configuration. "
            f"Restore from pre-migration backup. "
            f"Verify service continuity within 1 hour."
        )

        # Progress
        progress_map = {
            1: rng.uniform(0, 5),
            2: rng.uniform(5, 20),
            3: rng.uniform(20, 35),
            4: rng.uniform(35, 55),
            5: rng.uniform(55, 70),
            6: rng.uniform(70, 80),
            7: rng.uniform(80, 85),
            8: rng.uniform(85, 90),
            9: rng.uniform(90, 95),
            10: rng.uniform(95, 99),
            11: 100,
        }

        task = {
            "task_id": task_id,
            "asset_id": asset.get("asset_id"),
            "dataset_profile": asset.get("dataset_profile", "A"),
            "current_algorithm": algo,
            "recommended_target": mig_target or "TBD — requires expert review",
            "migration_phase": phase,
            "phase_name": MIGRATION_PHASES.get(phase, "Unknown"),
            "migration_owner": asset.get("owner", "Unassigned"),
            "dependencies": deps,
            "compatibility_risk": compat_risk,
            "estimated_cost": asset.get("estimated_migration_cost", 0),
            "estimated_downtime_hours": asset.get("estimated_downtime_hours", 0),
            "testing_requirements": testing,
            "rollback_plan": rollback,
            "approval_required": asset.get("owner_approval_required", True),
            "approval_status": "approved" if phase >= 5 else "pending",
            "progress_percent": round(progress_map.get(phase, 0), 1),
            "validation_status": "passed" if phase >= 9 else ("in-progress" if phase >= 4 else "not-started"),
        }
        tasks.append(task)

    return tasks


def _generate_testing_requirements(role: str, current_algo: str, target: str) -> str:
    """Generate testing requirements based on algorithm role."""
    parts = [f"Verify {target or 'target'} interoperability with existing systems."]

    if role == "key-establishment":
        parts.append("Test key exchange handshake with all connected clients.")
        parts.append("Measure key generation and encapsulation performance.")
        parts.append("Verify backward compatibility in hybrid mode.")
    elif role == "digital-signature":
        parts.append("Verify signature generation and verification across all document types.")
        parts.append("Test certificate chain validation.")
        parts.append("Measure signature size impact on bandwidth.")
    elif role == "encryption":
        parts.append("Test encryption/decryption round-trip for all data formats.")
        parts.append("Verify performance meets SLA requirements.")
    elif role == "hashing":
        parts.append("Verify hash output compatibility with downstream systems.")
        parts.append("Update all hardcoded hash length expectations.")

    parts.append("Run full regression test suite.")
    parts.append("Validate in staging environment for 72 hours minimum.")
    return " ".join(parts)


# ─── What-If Simulator (§13) ──────────────────────────────────────────────

def run_whatif_simulation(
    assets: List[Dict],
    quantum_capability: float = 0.5,
    logical_qubits: int = 4000,
    error_correction_maturity: float = 0.5,
    pct_legacy: float = None,
    pct_hybrid: float = None,
    pct_pqc: float = None,
    data_lifetime_override: int = None,
    migration_budget: float = None,
    migration_speed: float = 1.0,
    third_party_deps: int = None,
    key_rotation_freq_days: int = None,
) -> Dict[str, Any]:
    """
    Run a What-If simulation (§13).

    Controls: quantum capability, logical qubits, error correction, asset mix,
    data lifetime, budget, speed, dependencies, rotation frequency.

    Returns: risk analysis, cost estimate, comparison data.
    """
    # Apply overrides to create scenario-modified assets
    scenario_assets = []
    for asset in assets:
        mod = dict(asset)  # shallow copy

        if data_lifetime_override is not None:
            mod["data_lifetime_years"] = data_lifetime_override

        if key_rotation_freq_days is not None:
            mod["key_rotation_days"] = key_rotation_freq_days

        scenario_assets.append(mod)

    # Compute risk scores for scenario
    total_risk = 0
    critical_count = 0
    high_count = 0
    vulnerable_sigs = 0
    exposed_data_records = 0

    for asset in scenario_assets:
        algo_info = classify_algorithm(asset.get("algorithm", ""))
        risk = compute_risk_score(asset)
        total_risk += risk["score"]

        if risk["band"] == "Critical":
            critical_count += 1
        elif risk["band"] == "High":
            high_count += 1

        if asset.get("algorithm_role") == "digital-signature" and algo_info["category"] == "quantum-broken":
            vulnerable_sigs += 1

        if algo_info["category"] in ("quantum-broken", "classically-broken"):
            type_records = {
                "database": 50000, "api": 10000, "backup": 100000,
                "application": 5000, "certificate": 100, "key_store": 500,
            }
            exposed_data_records += type_records.get(asset.get("asset_type", "application"), 5000)

    avg_risk = total_risk / max(len(scenario_assets), 1)
    total_cost = sum(a.get("estimated_migration_cost", 0) for a in scenario_assets if a.get("migration_status") != "completed")
    total_downtime = sum(a.get("estimated_downtime_hours", 0) for a in scenario_assets if a.get("migration_status") != "completed")

    # Apply budget constraint
    if migration_budget is not None and total_cost > migration_budget:
        budget_coverage = migration_budget / max(total_cost, 1)
    else:
        budget_coverage = 1.0

    # Agility score for scenario
    agility = compute_agility_score(scenario_assets)

    # Expert review count
    expert_review_needed = sum(
        1 for a in scenario_assets
        if a.get("confidence") in ("low", "unknown") or a.get("migration_complexity") in ("high", "critical")
    )

    return {
        "scenario_params": {
            "quantum_capability": quantum_capability,
            "logical_qubits": logical_qubits,
            "error_correction_maturity": error_correction_maturity,
            "data_lifetime_override": data_lifetime_override,
            "migration_budget": migration_budget,
            "migration_speed": migration_speed,
            "key_rotation_freq_days": key_rotation_freq_days,
        },
        "results": {
            "total_assets": len(scenario_assets),
            "average_risk_score": round(avg_risk, 1),
            "critical_risk_assets": critical_count,
            "high_risk_assets": high_count,
            "vulnerable_signatures": vulnerable_sigs,
            "exposed_data_records": exposed_data_records,
            "total_migration_cost": round(total_cost, 2),
            "total_downtime_hours": round(total_downtime, 1),
            "budget_coverage": round(budget_coverage * 100, 1),
            "agility_score": agility["score"],
            "expert_review_needed": expert_review_needed,
            "risk_reduction_potential": round(avg_risk * (1 - budget_coverage * 0.7), 1),
        },
        "disclaimer": "This is an illustrative simulation, not a forecast. Results are scenario-based prioritization aids only.",
    }


def compare_scenarios(scenarios: List[Dict]) -> List[Dict]:
    """
    Build a comparison table from multiple What-If scenario results (§13).
    """
    table = []
    for i, s in enumerate(scenarios):
        r = s.get("results", {})
        p = s.get("scenario_params", {})
        table.append({
            "scenario": f"Scenario {i + 1}",
            "quantum_capability": p.get("quantum_capability", "N/A"),
            "legacy_assets": r.get("total_assets", 0) - r.get("critical_risk_assets", 0) - r.get("high_risk_assets", 0),
            "pqc_assets": r.get("total_assets", 0) - r.get("vulnerable_signatures", 0),
            "critical_risk": r.get("critical_risk_assets", 0),
            "migration_cost": r.get("total_migration_cost", 0),
            "remaining_exposure": r.get("exposed_data_records", 0),
            "agility_score": r.get("agility_score", 0),
        })
    return table
