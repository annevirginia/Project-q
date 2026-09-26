"""
QuantumShield v2 — Quantum Risk Model (§5)

Explainable risk score 0–100 with 7 weighted factors.
Includes §5.1 normalization rubric.
"""

from typing import Dict, Any

# §5 — Weights (sum to 1.00)
RISK_WEIGHTS = {
    "algorithm_risk": 0.25,
    "data_sensitivity": 0.20,
    "data_lifetime": 0.15,
    "asset_criticality": 0.15,
    "internet_exposure": 0.10,
    "migration_complexity": 0.10,
    "inventory_uncertainty": 0.05,
}


def normalize_algorithm_risk(algorithm: str, quantum_status: str) -> float:
    """
    §5.1 normalization: algorithm_risk
    0 = ML-KEM/ML-DSA/SLH-DSA, AES-256
    33 = Hybrid classical+PQC
    66 = RSA/ECC ≥3072-bit, AES-128
    100 = RSA/ECC <2048-bit, SHA-1, DH
    """
    algo_upper = algorithm.upper() if algorithm else ""

    # Quantum-resilient (PQC standards)
    if quantum_status == "quantum-resilient":
        if "+" in algorithm:  # Hybrid
            return 33
        return 0

    # Classically broken
    if quantum_status == "classically-broken":
        return 100

    # Quantum-weakened
    if quantum_status == "quantum-weakened":
        if "AES-128" in algo_upper:
            return 66
        return 40  # SHA-256 etc.

    # Quantum-broken (Shor's)
    if quantum_status == "quantum-broken":
        # Check key size
        if "1024" in algo_upper or "DH-1024" in algo_upper:
            return 100
        if "4096" in algo_upper:
            return 66
        if "3072" in algo_upper:
            return 66
        return 85  # 2048-bit RSA, standard ECC

    return 75  # Unknown


def normalize_data_sensitivity(classification: str) -> float:
    """
    §5.1 normalization: data_sensitivity
    0 = Public, 33 = Internal, 66 = Confidential, 100 = Restricted/Highly Restricted
    """
    mapping = {
        "public": 0,
        "internal": 33,
        "confidential": 66,
        "restricted": 100,
        "highly_restricted": 100,
    }
    return mapping.get(classification, 50)


def normalize_data_lifetime(lifetime_years: int) -> float:
    """
    §5.1 normalization: data_lifetime
    0 = <1 year, 33 = 1-3 years, 66 = 3-10 years, 100 = >10 years/indefinite
    """
    if lifetime_years is None:
        return 100  # unknown = worst case
    if lifetime_years >= 99:  # indefinite
        return 100
    if lifetime_years > 10:
        return 100
    if lifetime_years > 3:
        return 66
    if lifetime_years >= 1:
        return 33
    return 0


def normalize_asset_criticality(criticality: str) -> float:
    """
    §5.1 normalization: asset_criticality
    0 = Low, 33 = Medium, 66 = High, 100 = Mission-critical
    """
    mapping = {
        "low": 0,
        "medium": 33,
        "high": 66,
        "mission-critical": 100,
    }
    return mapping.get(criticality, 50)


def normalize_internet_exposure(exposure_detail: str, internet_exposed: bool) -> float:
    """
    §5.1 normalization: internet_exposure
    0 = Not exposed, 33 = VPN/gateway, 66 = Internet-facing, 100 = Internet + no auth
    """
    if not internet_exposed:
        return 0
    mapping = {
        "not-exposed": 0,
        "vpn-gateway": 33,
        "internet-facing": 66,
        "internet-no-auth": 100,
    }
    return mapping.get(exposure_detail, 66)


def normalize_migration_complexity(migration_status: str, migration_complexity: str) -> float:
    """
    §5.1 normalization: migration_complexity
    0 = Completed, 33 = Low/planned, 66 = High/blocked, 100 = Unsupported/no plan
    """
    if migration_status == "completed":
        return 0
    if migration_status in ("deploying", "testing"):
        return 25
    if migration_status == "planning":
        return 33

    # not-started
    complexity_map = {
        "low": 33,
        "medium": 50,
        "high": 66,
        "critical": 100,
    }
    return complexity_map.get(migration_complexity, 80)


def normalize_inventory_uncertainty(confidence: str, evidence: list = None) -> float:
    """
    §5.1 normalization: inventory_uncertainty
    0 = Full evidence/high confidence, 33 = Partial, 66 = Low, 100 = None/unknown
    """
    has_evidence = evidence and len(evidence) > 0

    if confidence == "high" and has_evidence:
        return 0
    if confidence == "medium" and has_evidence:
        return 33
    if confidence == "low":
        return 66
    if confidence == "unknown" or not has_evidence:
        return 100
    return 50


def compute_risk_score(asset: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute the full risk score for an asset per §5.
    Returns score, band, all factors, and weights for explainability.
    """
    factors = {
        "algorithm_risk": normalize_algorithm_risk(
            asset.get("algorithm", ""), asset.get("quantum_status", "")
        ),
        "data_sensitivity": normalize_data_sensitivity(
            asset.get("data_classification", "internal")
        ),
        "data_lifetime": normalize_data_lifetime(
            asset.get("data_lifetime_years")
        ),
        "asset_criticality": normalize_asset_criticality(
            asset.get("business_criticality", "medium")
        ),
        "internet_exposure": normalize_internet_exposure(
            asset.get("exposure_detail", "not-exposed"),
            asset.get("internet_exposed", False)
        ),
        "migration_complexity": normalize_migration_complexity(
            asset.get("migration_status", "not-started"),
            asset.get("migration_complexity", "medium")
        ),
        "inventory_uncertainty": normalize_inventory_uncertainty(
            asset.get("confidence", "medium"),
            asset.get("evidence", [])
        ),
    }

    # Weighted sum
    score = sum(factors[k] * RISK_WEIGHTS[k] for k in RISK_WEIGHTS)
    score = min(100, max(0, round(score, 1)))

    return {
        "score": score,
        "band": get_risk_band(score),
        "factors": factors,
        "weights": dict(RISK_WEIGHTS),
    }


def get_risk_band(score: float) -> str:
    """Map score to risk band (§5)."""
    if score < 25:
        return "Low"
    elif score < 50:
        return "Moderate"
    elif score < 75:
        return "High"
    return "Critical"


def compute_agility_score(assets: list) -> Dict[str, Any]:
    """
    Crypto Agility Score (§9): 0–100.
    Higher = more agile / better prepared.
    """
    if not assets:
        return {"score": 0, "factors": {}, "improvements": []}

    total = len(assets)

    # Factor scores (each 0-100, higher is better)
    completed_migrations = sum(1 for a in assets if a.get("migration_status") == "completed")
    pqc_ready = sum(1 for a in assets if a.get("quantum_status") == "quantum-resilient")
    has_rotation = sum(1 for a in assets if a.get("key_rotation_days") and a["key_rotation_days"] <= 365)
    has_evidence = sum(1 for a in assets if a.get("evidence") and len(a["evidence"]) > 0)
    has_owner = sum(1 for a in assets if a.get("owner") and "Unknown" not in a.get("owner", ""))
    hybrid_capable = sum(1 for a in assets if "+" in a.get("algorithm", ""))
    valid_certs = sum(1 for a in assets if a.get("certificate_status") == "valid")
    cert_assets = sum(1 for a in assets if a.get("certificate_status") not in (None, "not-applicable"))

    factors = {
        "migration_completion": round((completed_migrations / total) * 100, 1),
        "pqc_readiness": round((pqc_ready / total) * 100, 1),
        "key_rotation_coverage": round((has_rotation / total) * 100, 1),
        "inventory_completeness": round((has_evidence / total) * 100, 1),
        "ownership_coverage": round((has_owner / total) * 100, 1),
        "hybrid_support": round((hybrid_capable / total) * 100, 1),
        "certificate_health": round((valid_certs / max(cert_assets, 1)) * 100, 1),
    }

    # Weighted agility score
    weights = {
        "migration_completion": 0.20,
        "pqc_readiness": 0.20,
        "key_rotation_coverage": 0.15,
        "inventory_completeness": 0.15,
        "ownership_coverage": 0.10,
        "hybrid_support": 0.10,
        "certificate_health": 0.10,
    }

    score = sum(factors[k] * weights[k] for k in weights)
    score = min(100, max(0, round(score, 1)))

    # Identify weakest factors and recommend improvements
    sorted_factors = sorted(factors.items(), key=lambda x: x[1])
    improvements = []
    for name, value in sorted_factors[:3]:
        label = name.replace("_", " ").title()
        projected_gain = (100 - value) * weights[name]
        improvements.append({
            "factor": label,
            "current": value,
            "improvement": f"Improving {label} to 100% would add {projected_gain:.1f} points",
            "projected_score": round(score + projected_gain, 1),
        })

    return {
        "score": score,
        "factors": factors,
        "weights": weights,
        "weakest_factors": [s[0] for s in sorted_factors[:3]],
        "improvements": improvements,
    }
