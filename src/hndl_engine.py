"""
QuantumShield v2 — Data Lifecycle & Exposure Module (§6)
and Harvest-Now-Decrypt-Later (HNDL) Simulator (§7)

Models the full lifecycle of each asset's data and computes
exposure windows under quantum scenarios.
"""

from typing import Dict, Any, List
from datetime import datetime
from src.crypto_inventory import classify_algorithm


# ─── Data Lifecycle Module (§6) ────────────────────────────────────────────

LIFECYCLE_STAGES = [
    "creation", "transmission", "storage", "backup",
    "sharing", "archival", "deletion", "key-rotation",
    "re-encryption", "pqc-migration"
]


def compute_data_lifecycle(asset: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulate the data lifecycle for an asset (§6).
    Returns timeline events, exposure analysis, and recommendations.
    """
    algo = asset.get("algorithm", "Unknown")
    algo_info = classify_algorithm(algo)
    lifetime = asset.get("data_lifetime_years", 1)
    if lifetime == 99:
        lifetime = 30  # treat indefinite as 30 years for timeline
    classification = asset.get("data_classification", "internal")
    mig_status = asset.get("migration_status", "not-started")
    mig_target = asset.get("migration_target")
    role = asset.get("algorithm_role", "unknown")

    # Build timeline
    base_year = 2024
    timeline = []

    # Stage 1: Creation
    timeline.append({
        "year": base_year,
        "stage": "creation",
        "description": f"Data created and protected with {algo} ({role})",
        "risk_level": "low" if algo_info["category"] == "quantum-resilient" else "moderate",
    })

    # Stage 2: Transmission
    if role in ("key-establishment", "encryption"):
        timeline.append({
            "year": base_year,
            "stage": "transmission",
            "description": f"Data transmitted using {algo} for {role}",
            "risk_level": "high" if algo_info["category"] == "quantum-broken" else "low",
        })

    # Stage 3: Storage
    storage_end = base_year + min(lifetime, 15)
    timeline.append({
        "year": base_year,
        "stage": "storage",
        "description": f"Data stored for {lifetime} years, encrypted with {algo}",
        "risk_level": "critical" if (algo_info["category"] == "quantum-broken" and lifetime > 5) else "moderate",
        "end_year": storage_end,
    })

    # Stage 4: Backup
    backup_years = min(lifetime * 2, 30)
    timeline.append({
        "year": base_year + 1,
        "stage": "backup",
        "description": f"Backed up for {backup_years} years",
        "risk_level": "high" if (algo_info["category"] == "quantum-broken" and backup_years > 10) else "moderate",
        "end_year": base_year + 1 + backup_years,
    })

    # Stage 5: Signing (if applicable)
    if role == "digital-signature":
        timeline.append({
            "year": base_year,
            "stage": "signing",
            "description": f"Data signed using {algo}",
            "risk_level": "critical" if algo_info["category"] == "quantum-broken" else "low",
        })

    # Stage 6: Quantum exposure window
    exposure_start = base_year
    # Estimated CRQC window (illustrative, NOT a prediction)
    crqc_window = 2035
    if algo_info["category"] == "quantum-broken":
        timeline.append({
            "year": crqc_window,
            "stage": "quantum-exposure",
            "description": f"Illustrative CRQC scenario: {algo} becomes vulnerable to {algo_info['attack']}",
            "risk_level": "critical",
        })

    # Stage 7: Migration recommendation
    if mig_status != "completed" and mig_target:
        rec_year = base_year + 2 if algo_info["category"] == "quantum-broken" else base_year + 5
        timeline.append({
            "year": rec_year,
            "stage": "pqc-migration",
            "description": f"Recommended: migrate to {mig_target}",
            "risk_level": "low",
        })

    # Stage 8: Re-encryption if needed
    if algo_info["category"] in ("quantum-broken", "classically-broken") and lifetime > 5:
        timeline.append({
            "year": base_year + 3,
            "stage": "re-encryption",
            "description": f"Re-encrypt stored data with quantum-resilient algorithm",
            "risk_level": "moderate",
        })

    # Sort by year
    timeline.sort(key=lambda t: t["year"])

    # Compute exposure analysis
    current_encryption_covers = (
        algo_info["category"] == "quantum-resilient" or
        (algo_info["category"] == "quantum-weakened" and lifetime <= 5)
    )

    return {
        "asset_id": asset.get("asset_id"),
        "asset_name": asset.get("asset_name"),
        "algorithm": algo,
        "algorithm_category": algo_info["category"],
        "data_lifetime_years": asset.get("data_lifetime_years", 1),
        "data_classification": classification,
        "timeline": timeline,
        "analysis": {
            "required_confidentiality_years": lifetime,
            "current_encryption_sufficient": current_encryption_covers,
            "harvestable_now": algo_info["category"] == "quantum-broken" and asset.get("internet_exposed", False),
            "future_decryption_risk": algo_info["category"] in ("quantum-broken", "classically-broken"),
            "re_encryption_needed": algo_info["category"] in ("quantum-broken", "classically-broken") and lifetime > 3,
            "signature_longevity_risk": role == "digital-signature" and algo_info["category"] == "quantum-broken",
            "historical_migration_needed": lifetime > 10 and algo_info["category"] == "quantum-broken",
        },
        "recommended_action": _lifecycle_recommendation(asset, algo_info, lifetime),
        "quantum_exposure_classification": _classify_exposure(algo_info, lifetime, classification),
    }


def _classify_exposure(algo_info: Dict, lifetime: int, classification: str) -> str:
    """Classify the overall quantum exposure level."""
    if algo_info["category"] == "quantum-resilient":
        return "low"
    if algo_info["category"] == "classically-broken":
        return "critical"
    if algo_info["category"] == "quantum-broken":
        if lifetime > 10 and classification in ("restricted", "highly_restricted"):
            return "critical"
        if lifetime > 5:
            return "high"
        return "moderate"
    if algo_info["category"] == "quantum-weakened":
        return "low" if lifetime <= 5 else "moderate"
    return "moderate"


def _lifecycle_recommendation(asset: Dict, algo_info: Dict, lifetime: int) -> str:
    """Generate lifecycle-specific recommendation."""
    algo = asset.get("algorithm", "Unknown")
    target = asset.get("migration_target")
    role = asset.get("algorithm_role", "unknown")

    if algo_info["category"] == "quantum-resilient":
        return f"Data is protected by {algo}. Continue monitoring for algorithm updates."

    parts = []
    if algo_info["category"] in ("quantum-broken", "classically-broken"):
        parts.append(f"Migrate {role} from {algo} to {target or 'PQC equivalent'}")
    if lifetime > 5 and algo_info["category"] == "quantum-broken":
        parts.append("implement hybrid encryption during transition")
    if lifetime > 10:
        parts.append("plan long-term re-encryption and re-signing of archived data")
    if role == "digital-signature" and algo_info["category"] == "quantum-broken":
        parts.append("implement signature re-signing workflow")

    return "; ".join(parts) + "." if parts else "Review and classify algorithm."


# ─── HNDL Simulator (§7) ──────────────────────────────────────────────────

def simulate_hndl(
    assets: List[Dict],
    quantum_capability: float = 0.0,
    migration_completion_pct: float = 0.0,
) -> Dict[str, Any]:
    """
    Simulate Harvest-Now-Decrypt-Later exposure across assets (§7).

    Args:
        assets: List of asset dicts
        quantum_capability: 0.0–1.0 representing quantum threat level
        migration_completion_pct: 0–100, % of assets migrated

    Returns:
        HNDL analysis with per-asset and aggregate results.
    """
    results = []
    total_records = 0
    exposed_records = 0
    protected_records = 0
    needs_reencryption = 0
    needs_key_rotation = 0
    needs_sig_renewal = 0

    for asset in assets:
        algo = asset.get("algorithm", "Unknown")
        algo_info = classify_algorithm(algo)
        lifetime = asset.get("data_lifetime_years", 1)
        classification = asset.get("data_classification", "internal")
        mig_status = asset.get("migration_status", "not-started")
        role = asset.get("algorithm_role", "unknown")

        # Simulated record count per asset
        record_count = _estimate_record_count(asset)
        total_records += record_count

        # Determine HNDL status
        status = _compute_hndl_record_status(algo_info, lifetime, classification, mig_status, quantum_capability)

        exposed_count = 0
        protected_count = 0
        reencrypt_count = 0

        if status in ("Requires immediate migration", "Requires re-encryption"):
            exposed_count = record_count
            reencrypt_count = record_count
        elif status == "Requires hybrid migration":
            exposed_count = int(record_count * 0.6)
            protected_count = record_count - exposed_count
        elif status == "Requires monitoring":
            exposed_count = int(record_count * 0.2)
            protected_count = record_count - exposed_count
        else:
            protected_count = record_count

        exposed_records += exposed_count
        protected_records += protected_count
        needs_reencryption += reencrypt_count

        if role == "digital-signature" and algo_info["category"] == "quantum-broken":
            needs_sig_renewal += record_count

        if asset.get("key_rotation_days") and asset["key_rotation_days"] > 365 and algo_info["category"] == "quantum-broken":
            needs_key_rotation += record_count

        results.append({
            "asset_id": asset.get("asset_id"),
            "asset_name": asset.get("asset_name"),
            "algorithm": algo,
            "records": record_count,
            "exposed_records": exposed_count,
            "protected_records": protected_count,
            "hndl_status": status,
            "quantum_risk_category": algo_info["category"],
        })

    return {
        "summary": {
            "total_records": total_records,
            "currently_exposed": exposed_records,
            "protected_after_migration": protected_records,
            "needs_re_encryption": needs_reencryption,
            "needs_key_rotation": needs_key_rotation,
            "needs_signature_renewal": needs_sig_renewal,
            "risk_before_migration": round((exposed_records / max(total_records, 1)) * 100, 1),
            "risk_after_migration": round(max(0, (exposed_records - needs_reencryption) / max(total_records, 1)) * 100, 1),
        },
        "per_asset": results,
        "scenario": {
            "quantum_capability": quantum_capability,
            "migration_completion_pct": migration_completion_pct,
            "disclaimer": "This is an illustrative simulation, not a forecast of CRQC availability.",
        },
    }


def _estimate_record_count(asset: Dict) -> int:
    """Estimate synthetic record count based on asset type."""
    type_records = {
        "database": 50000,
        "api": 10000,
        "backup": 100000,
        "application": 5000,
        "certificate": 100,
        "key_store": 500,
        "ledger": 25000,
        "third_party": 8000,
    }
    return type_records.get(asset.get("asset_type", "application"), 5000)


def _compute_hndl_record_status(
    algo_info: Dict, lifetime: int, classification: str,
    mig_status: str, quantum_capability: float
) -> str:
    """Compute HNDL status per §7 status model."""
    if mig_status == "completed" and algo_info["category"] == "quantum-resilient":
        return "Protected for current scenario"

    if algo_info["category"] == "classically-broken":
        return "Requires immediate migration"

    if algo_info["category"] == "quantum-broken":
        is_sensitive = classification in ("restricted", "highly_restricted", "confidential")
        is_long_lived = lifetime > 5 or lifetime == 99

        if quantum_capability > 0.7:
            return "Requires immediate migration"
        if is_sensitive and is_long_lived:
            return "Requires re-encryption"
        if is_sensitive or is_long_lived:
            return "Requires hybrid migration"
        return "Requires monitoring"

    if algo_info["category"] == "quantum-weakened":
        if lifetime > 10:
            return "Requires monitoring"
        return "Protected for current scenario"

    return "Protected for current scenario"
