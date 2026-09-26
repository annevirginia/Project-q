"""
QuantumShield v2 — Cryptographic Inventory Engine (§4)

Scans synthetic assets, classifies algorithms, and produces findings.
Distinguishes algorithm roles and applies §4.1 corrected risk classification.
"""

from typing import List, Dict, Any
from src.risk_model import compute_risk_score, get_risk_band


# §4.1 — Corrected algorithm-risk classification
ALGORITHM_CLASSIFICATION = {
    # Quantum-broken (Shor's algorithm — exponential speedup)
    "RSA-1024": {"category": "quantum-broken", "attack": "Shor (factoring)", "severity": 100},
    "RSA-2048": {"category": "quantum-broken", "attack": "Shor (factoring)", "severity": 85},
    "RSA-4096": {"category": "quantum-broken", "attack": "Shor (factoring)", "severity": 70},
    "ECDSA-P256": {"category": "quantum-broken", "attack": "Shor (discrete log)", "severity": 90},
    "ECDSA-P384": {"category": "quantum-broken", "attack": "Shor (discrete log)", "severity": 85},
    "Ed25519": {"category": "quantum-broken", "attack": "Shor (discrete log)", "severity": 90},
    "ECDH-P256": {"category": "quantum-broken", "attack": "Shor (discrete log)", "severity": 90},
    "ECDH-P384": {"category": "quantum-broken", "attack": "Shor (discrete log)", "severity": 85},
    "DH-2048": {"category": "quantum-broken", "attack": "Shor (discrete log)", "severity": 85},
    "DH-1024": {"category": "quantum-broken", "attack": "Shor (discrete log)", "severity": 100},

    # Quantum-weakened (Grover's algorithm — quadratic speedup)
    "AES-128": {"category": "quantum-weakened", "attack": "Grover (brute-force)", "severity": 40},
    "SHA-256": {"category": "quantum-weakened", "attack": "Grover (search)", "severity": 25},

    # Already classically broken
    "SHA-1": {"category": "classically-broken", "attack": "Collision attacks", "severity": 95},
    "MD5": {"category": "classically-broken", "attack": "Collision attacks", "severity": 100},
    "DES": {"category": "classically-broken", "attack": "Brute-force", "severity": 100},
    "3DES": {"category": "classically-broken", "attack": "Meet-in-the-middle", "severity": 80},

    # Quantum-resilient
    "ML-KEM-768": {"category": "quantum-resilient", "attack": "None known", "severity": 0},
    "ML-KEM-1024": {"category": "quantum-resilient", "attack": "None known", "severity": 0},
    "ML-DSA-65": {"category": "quantum-resilient", "attack": "None known", "severity": 0},
    "ML-DSA-87": {"category": "quantum-resilient", "attack": "None known", "severity": 0},
    "SLH-DSA-128s": {"category": "quantum-resilient", "attack": "None known", "severity": 0},
    "SLH-DSA-256f": {"category": "quantum-resilient", "attack": "None known", "severity": 0},
    "AES-256": {"category": "quantum-resilient", "attack": "None known (Grover halves to 128-bit — still secure)", "severity": 5},
    "SHA-384": {"category": "quantum-resilient", "attack": "None known (Grover halves to 192-bit — still secure)", "severity": 5},

    # Hybrid
    "RSA-2048+ML-KEM-768": {"category": "quantum-resilient", "attack": "Protected if either algorithm holds", "severity": 10},
    "ECDSA+ML-DSA-65": {"category": "quantum-resilient", "attack": "Protected if either algorithm holds", "severity": 10},
    "ECDH+ML-KEM-768": {"category": "quantum-resilient", "attack": "Protected if either algorithm holds", "severity": 10},

    # Unknown
    "Unknown-Custom": {"category": "unknown", "attack": "Cannot assess — unknown algorithm", "severity": 75},
}


def classify_algorithm(algorithm_name: str) -> Dict[str, Any]:
    """Return the classification info for a given algorithm."""
    if algorithm_name in ALGORITHM_CLASSIFICATION:
        return ALGORITHM_CLASSIFICATION[algorithm_name]
    return {"category": "unknown", "attack": "Cannot assess — unknown algorithm", "severity": 75}


def determine_hndl_status(asset: Dict) -> str:
    """
    Determine HNDL status for an asset (§7).
    """
    algo_info = classify_algorithm(asset.get("algorithm", ""))
    classification = asset.get("data_classification", "internal")
    lifetime = asset.get("data_lifetime_years", 1)
    mig_status = asset.get("migration_status", "not-started")

    if algo_info["category"] == "quantum-resilient" and mig_status == "completed":
        return "Protected for current scenario"
    elif algo_info["category"] in ("quantum-broken",) and classification in ("restricted", "highly_restricted"):
        if lifetime > 10 or lifetime == 99:
            return "Requires immediate migration"
        elif lifetime > 5:
            return "Requires hybrid migration"
        else:
            return "Requires monitoring"
    elif algo_info["category"] == "classically-broken":
        return "Requires immediate migration"
    elif algo_info["category"] == "quantum-weakened":
        if lifetime > 10:
            return "Requires monitoring"
        return "Protected for current scenario"
    elif mig_status in ("planning", "testing"):
        return "Requires hybrid migration"
    elif mig_status == "deploying":
        return "Requires monitoring"
    else:
        if algo_info["category"] == "quantum-broken":
            return "Requires hybrid migration"
        return "Protected for current scenario"


def generate_recommended_action(asset: Dict, algo_info: Dict) -> str:
    """Generate a human-readable recommended action."""
    algo = asset.get("algorithm", "Unknown")
    target = asset.get("migration_target")
    role = asset.get("algorithm_role", "unknown")
    mig_status = asset.get("migration_status", "not-started")

    if algo_info["category"] == "quantum-resilient" and mig_status == "completed":
        return f"No action required. {algo} is quantum-resilient for {role}. Continue monitoring for new developments."

    if algo_info["category"] == "classically-broken":
        return (
            f"URGENT: {algo} is already classically broken ({algo_info['attack']}). "
            f"Migrate immediately to {target or 'a modern algorithm'} regardless of quantum timeline."
        )

    if algo_info["category"] == "quantum-broken":
        urgency = "HIGH" if asset.get("data_classification") in ("restricted", "highly_restricted") else "MODERATE"
        return (
            f"{urgency} PRIORITY: {algo} ({role}) is vulnerable to {algo_info['attack']} by a CRQC. "
            f"Recommended migration target: {target or 'ML-KEM/ML-DSA (FIPS 203/204)'}. "
            f"Current migration status: {mig_status}. "
            f"Consider hybrid deployment during transition."
        )

    if algo_info["category"] == "quantum-weakened":
        return (
            f"LOW PRIORITY: {algo} effective security is halved by Grover's algorithm "
            f"(e.g., AES-128 → ~64-bit equivalent). Consider upgrading to {target or 'AES-256/SHA-384'} "
            f"for long-lived data."
        )

    return f"Review required: Unable to fully assess {algo}. Ensure algorithm is documented and classified."


def scan_assets(assets: List[Dict]) -> List[Dict[str, Any]]:
    """
    Scan a list of assets and produce findings.
    Each finding includes the full risk breakdown per §4/§5.
    """
    findings = []

    for idx, asset in enumerate(assets):
        finding_id = f"find-{idx + 1:04d}"
        algo = asset.get("algorithm", "Unknown")
        algo_info = classify_algorithm(algo)

        # Compute full risk score
        risk_result = compute_risk_score(asset)
        hndl_status = determine_hndl_status(asset)
        recommended_action = generate_recommended_action(asset, algo_info)

        # Build explanation (§14 — Explainable AI)
        explanation = build_finding_explanation(asset, algo_info, risk_result, hndl_status)

        finding = {
            "finding_id": finding_id,
            "asset_id": asset["asset_id"],
            "dataset_profile": asset.get("dataset_profile", "A"),
            "algorithm": algo,
            "algorithm_role": asset.get("algorithm_role", "unknown"),
            "algorithm_risk": risk_result["factors"]["algorithm_risk"],
            "data_sensitivity": risk_result["factors"]["data_sensitivity"],
            "data_lifetime": risk_result["factors"]["data_lifetime"],
            "asset_criticality": risk_result["factors"]["asset_criticality"],
            "internet_exposure": risk_result["factors"]["internet_exposure"],
            "migration_complexity_score": risk_result["factors"]["migration_complexity"],
            "inventory_uncertainty": risk_result["factors"]["inventory_uncertainty"],
            "risk_score": risk_result["score"],
            "risk_band": risk_result["band"],
            "priority": idx + 1,
            "hndl_status": hndl_status,
            "evidence": asset.get("evidence", []),
            "confidence": asset.get("confidence", "medium"),
            "recommended_action": recommended_action,
            "explanation": explanation,
        }
        findings.append(finding)

    # Sort by risk score descending for priority
    findings.sort(key=lambda f: f["risk_score"], reverse=True)
    for i, f in enumerate(findings):
        f["priority"] = i + 1

    return findings


def build_finding_explanation(asset: Dict, algo_info: Dict, risk_result: Dict, hndl_status: str) -> str:
    """Build a human-readable explanation of the finding (§14)."""
    factors = risk_result["factors"]
    weights = risk_result["weights"]

    lines = [
        f"Finding: {asset.get('algorithm', 'Unknown')} used for {asset.get('algorithm_role', 'unknown')} in {asset.get('asset_name', 'Unknown Asset')}",
        "",
        f"Why it matters: {algo_info.get('attack', 'Unknown attack vector')}. "
        f"Category: {algo_info.get('category', 'unknown')}.",
        "",
        "Risk factors (weighted contribution to score):",
    ]

    factor_labels = {
        "algorithm_risk": "Algorithm Risk",
        "data_sensitivity": "Data Sensitivity",
        "data_lifetime": "Data Lifetime",
        "asset_criticality": "Asset Criticality",
        "internet_exposure": "Internet Exposure",
        "migration_complexity": "Migration Complexity",
        "inventory_uncertainty": "Inventory Uncertainty",
    }

    for key, label in factor_labels.items():
        raw = factors[key]
        w = weights[key]
        contrib = raw * w
        lines.append(f"  • {label}: {raw:.0f}/100 × {w:.2f} = {contrib:.1f}")

    lines.extend([
        "",
        f"Total risk score: {risk_result['score']:.1f}/100 ({risk_result['band']})",
        f"HNDL status: {hndl_status}",
        f"Confidence: {asset.get('confidence', 'medium')}",
        "",
        "What this system cannot determine:",
        "  • Exact date of CRQC availability",
        "  • Whether specific implementations have side-channel vulnerabilities",
        "  • Organizational readiness factors beyond this simulation's scope",
        "  • Compliance with specific regulatory frameworks",
    ])

    return "\n".join(lines)
