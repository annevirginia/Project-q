"""
QuantumShield v2 — Synthetic Dataset Generator (§2, §3)

Generates 4 switchable datasets (A–D) with ≥100 records each,
using a fixed reproducible seed. All data is synthetic — NovaBank Demo org.

Dataset Profiles:
  A — Legacy Enterprise (mostly RSA/ECDH/ECDSA, weak certs, high migration complexity)
  B — Mixed Transition (legacy + hybrid, some ML-KEM/ML-DSA, moderate progress)
  C — Post-Quantum Migration Program (mostly PQC, few legacy holdouts, strong inventory)
  D — Stress-Test Environment (many assets, conflicts, missing owners, high cost)
"""

import random
import hashlib
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# ─── Fixed reproducible seed (§18) ─────────────────────────────────────────
GLOBAL_SEED = 42

# ─── NovaBank Demo organization assets (§16) ───────────────────────────────

NOVABANK_CORE_ASSETS = [
    {"name": "NovaBank Public Website", "type": "application", "owner": "Web Platform Team",
     "criticality": "high", "classification": "public", "exposed": True, "exposure_detail": "internet-facing"},
    {"name": "NovaBank Customer API", "type": "api", "owner": "Digital Banking Team",
     "criticality": "mission-critical", "classification": "restricted", "exposed": True, "exposure_detail": "internet-facing"},
    {"name": "Internal Payment Service", "type": "application", "owner": "Payments Team",
     "criticality": "mission-critical", "classification": "highly_restricted", "exposed": False, "exposure_detail": "not-exposed"},
    {"name": "Customer Database", "type": "database", "owner": "Data Engineering Team",
     "criticality": "mission-critical", "classification": "restricted", "exposed": False, "exposure_detail": "not-exposed"},
    {"name": "Backup Archive System", "type": "backup", "owner": "Infrastructure Team",
     "criticality": "high", "classification": "confidential", "exposed": False, "exposure_detail": "not-exposed"},
    {"name": "Certificate Authority (Internal)", "type": "certificate", "owner": "Security Team",
     "criticality": "mission-critical", "classification": "highly_restricted", "exposed": False, "exposure_detail": "vpn-gateway"},
    {"name": "Mobile Banking App", "type": "application", "owner": "Mobile Dev Team",
     "criticality": "high", "classification": "confidential", "exposed": True, "exposure_detail": "internet-facing"},
    {"name": "Third-Party Payment Vendor", "type": "third_party", "owner": "Vendor Management",
     "criticality": "high", "classification": "restricted", "exposed": True, "exposure_detail": "internet-facing"},
    {"name": "Blockchain Transaction Ledger", "type": "ledger", "owner": "FinTech Innovation Team",
     "criticality": "high", "classification": "confidential", "exposed": False, "exposure_detail": "not-exposed"},
    {"name": "Identity Service (IAM)", "type": "application", "owner": "Identity Team",
     "criticality": "mission-critical", "classification": "restricted", "exposed": True, "exposure_detail": "vpn-gateway"},
    {"name": "Data Warehouse", "type": "database", "owner": "Analytics Team",
     "criticality": "medium", "classification": "internal", "exposed": False, "exposure_detail": "not-exposed"},
    {"name": "Long-Term Compliance Archive", "type": "backup", "owner": "Compliance Team",
     "criticality": "high", "classification": "restricted", "exposed": False, "exposure_detail": "not-exposed"},
]

# Additional asset templates for expansion
EXTRA_ASSET_TEMPLATES = [
    {"name": "Email Gateway", "type": "application", "owner": "IT Operations"},
    {"name": "HR Portal", "type": "application", "owner": "HR Technology Team"},
    {"name": "Trading Platform API", "type": "api", "owner": "Capital Markets Team"},
    {"name": "Fraud Detection Engine", "type": "application", "owner": "Risk Analytics Team"},
    {"name": "Customer Notification Service", "type": "api", "owner": "Communications Team"},
    {"name": "Loan Processing System", "type": "application", "owner": "Lending Team"},
    {"name": "ATM Network Controller", "type": "application", "owner": "ATM Operations"},
    {"name": "Cloud Key Management Service", "type": "key_store", "owner": "Cloud Security Team"},
    {"name": "API Gateway", "type": "application", "owner": "Platform Engineering"},
    {"name": "Document Signing Service", "type": "application", "owner": "Legal Tech Team"},
    {"name": "Audit Log Aggregator", "type": "database", "owner": "Security Operations"},
    {"name": "Inter-Bank Transfer Service", "type": "api", "owner": "SWIFT Integration Team"},
    {"name": "Customer Data Lake", "type": "database", "owner": "Big Data Team"},
    {"name": "Disaster Recovery Backup", "type": "backup", "owner": "Business Continuity"},
    {"name": "Regulatory Reporting System", "type": "application", "owner": "Compliance Team"},
    {"name": "Partner Integration Gateway", "type": "third_party", "owner": "Partnerships Team"},
    {"name": "Mobile Push Notification Service", "type": "api", "owner": "Mobile Dev Team"},
    {"name": "Internal Chat Service", "type": "application", "owner": "IT Operations"},
    {"name": "Code Signing Certificate Store", "type": "certificate", "owner": "DevOps Team"},
    {"name": "SWIFT Message Queue", "type": "application", "owner": "SWIFT Integration Team"},
    {"name": "Customer KYC Database", "type": "database", "owner": "Compliance Team"},
    {"name": "Merchant Payment Gateway", "type": "api", "owner": "Merchant Services Team"},
    {"name": "Insurance Claims Processor", "type": "application", "owner": "Insurance Division"},
    {"name": "Wealth Management Portal", "type": "application", "owner": "Wealth Team"},
    {"name": "Crypto Wallet Service", "type": "application", "owner": "Digital Assets Team"},
    {"name": "Network TLS Terminator", "type": "application", "owner": "Network Security Team"},
    {"name": "DNS Infrastructure", "type": "application", "owner": "Infrastructure Team"},
    {"name": "VPN Gateway", "type": "application", "owner": "Network Security Team"},
    {"name": "Secrets Vault", "type": "key_store", "owner": "Security Team"},
    {"name": "CI/CD Pipeline", "type": "application", "owner": "DevOps Team"},
    {"name": "Container Registry", "type": "application", "owner": "DevOps Team"},
    {"name": "Log Management SIEM", "type": "application", "owner": "Security Operations"},
    {"name": "Endpoint Protection Manager", "type": "application", "owner": "IT Security"},
    {"name": "Customer SSO Service", "type": "application", "owner": "Identity Team"},
    {"name": "Third-Party Credit Bureau API", "type": "third_party", "owner": "Credit Risk Team"},
    {"name": "Pension Fund Database", "type": "database", "owner": "Retirement Services"},
    {"name": "Real-Time Fraud Scoring API", "type": "api", "owner": "Fraud Prevention Team"},
    {"name": "Core Banking Mainframe Bridge", "type": "application", "owner": "Core Systems Team"},
    {"name": "Customer Statement Archive", "type": "backup", "owner": "Document Management"},
    {"name": "Tax Reporting Service", "type": "api", "owner": "Tax Division"},
]

# ─── Algorithm pools per category ──────────────────────────────────────────

ALGORITHMS = {
    "quantum_broken": [
        {"name": "RSA-1024", "role": "digital-signature", "key_length": 1024, "quantum_status": "quantum-broken"},
        {"name": "RSA-2048", "role": "digital-signature", "key_length": 2048, "quantum_status": "quantum-broken"},
        {"name": "RSA-2048", "role": "key-establishment", "key_length": 2048, "quantum_status": "quantum-broken"},
        {"name": "RSA-4096", "role": "digital-signature", "key_length": 4096, "quantum_status": "quantum-broken"},
        {"name": "ECDSA-P256", "role": "digital-signature", "key_length": 256, "quantum_status": "quantum-broken"},
        {"name": "ECDSA-P384", "role": "digital-signature", "key_length": 384, "quantum_status": "quantum-broken"},
        {"name": "Ed25519", "role": "digital-signature", "key_length": 256, "quantum_status": "quantum-broken"},
        {"name": "ECDH-P256", "role": "key-establishment", "key_length": 256, "quantum_status": "quantum-broken"},
        {"name": "ECDH-P384", "role": "key-establishment", "key_length": 384, "quantum_status": "quantum-broken"},
        {"name": "DH-2048", "role": "key-establishment", "key_length": 2048, "quantum_status": "quantum-broken"},
        {"name": "DH-1024", "role": "key-establishment", "key_length": 1024, "quantum_status": "quantum-broken"},
    ],
    "quantum_weakened": [
        {"name": "AES-128", "role": "encryption", "key_length": 128, "quantum_status": "quantum-weakened"},
        {"name": "SHA-256", "role": "hashing", "key_length": 256, "quantum_status": "quantum-weakened"},
    ],
    "classically_broken": [
        {"name": "SHA-1", "role": "hashing", "key_length": 160, "quantum_status": "classically-broken"},
        {"name": "MD5", "role": "hashing", "key_length": 128, "quantum_status": "classically-broken"},
        {"name": "DES", "role": "encryption", "key_length": 56, "quantum_status": "classically-broken"},
        {"name": "3DES", "role": "encryption", "key_length": 168, "quantum_status": "classically-broken"},
    ],
    "quantum_resilient": [
        {"name": "ML-KEM-768", "role": "key-establishment", "key_length": 768, "quantum_status": "quantum-resilient"},
        {"name": "ML-KEM-1024", "role": "key-establishment", "key_length": 1024, "quantum_status": "quantum-resilient"},
        {"name": "ML-DSA-65", "role": "digital-signature", "key_length": 0, "quantum_status": "quantum-resilient"},
        {"name": "ML-DSA-87", "role": "digital-signature", "key_length": 0, "quantum_status": "quantum-resilient"},
        {"name": "SLH-DSA-128s", "role": "digital-signature", "key_length": 128, "quantum_status": "quantum-resilient"},
        {"name": "SLH-DSA-256f", "role": "digital-signature", "key_length": 256, "quantum_status": "quantum-resilient"},
        {"name": "AES-256", "role": "encryption", "key_length": 256, "quantum_status": "quantum-resilient"},
        {"name": "SHA-384", "role": "hashing", "key_length": 384, "quantum_status": "quantum-resilient"},
    ],
    "hybrid": [
        {"name": "RSA-2048+ML-KEM-768", "role": "key-establishment", "key_length": 0, "quantum_status": "quantum-resilient"},
        {"name": "ECDSA+ML-DSA-65", "role": "digital-signature", "key_length": 0, "quantum_status": "quantum-resilient"},
        {"name": "ECDH+ML-KEM-768", "role": "key-establishment", "key_length": 0, "quantum_status": "quantum-resilient"},
    ],
}

# ─── Dataset profile configurations (§3) ──────────────────────────────────

DATASET_PROFILES = {
    "A": {
        "name": "Legacy Enterprise",
        "description": "Mostly RSA/ECDH/ECDSA/Ed25519/SHA-1; long-lived sensitive data; weak/outdated certs; no formal inventory; high migration complexity",
        "algo_weights": {"quantum_broken": 0.55, "classically_broken": 0.15, "quantum_weakened": 0.15, "quantum_resilient": 0.05, "hybrid": 0.10},
        "cert_expired_chance": 0.30,
        "missing_owner_chance": 0.20,
        "migration_started_chance": 0.05,
        "high_complexity_chance": 0.70,
        "long_lifetime_chance": 0.60,
        "low_confidence_chance": 0.35,
        "target_count": 120,
    },
    "B": {
        "name": "Mixed Transition",
        "description": "Legacy + hybrid crypto; some ML-KEM/ML-DSA deployments; incomplete key rotation; moderate migration progress; interoperability issues",
        "algo_weights": {"quantum_broken": 0.30, "classically_broken": 0.05, "quantum_weakened": 0.10, "quantum_resilient": 0.25, "hybrid": 0.30},
        "cert_expired_chance": 0.15,
        "missing_owner_chance": 0.10,
        "migration_started_chance": 0.40,
        "high_complexity_chance": 0.40,
        "long_lifetime_chance": 0.40,
        "low_confidence_chance": 0.15,
        "target_count": 110,
    },
    "C": {
        "name": "Post-Quantum Migration Program",
        "description": "Most key exchange = ML-KEM/hybrid; most signatures = ML-DSA/SLH-DSA; few legacy holdouts; strong inventory/ownership; tracked migration tasks",
        "algo_weights": {"quantum_broken": 0.10, "classically_broken": 0.02, "quantum_weakened": 0.08, "quantum_resilient": 0.55, "hybrid": 0.25},
        "cert_expired_chance": 0.05,
        "missing_owner_chance": 0.03,
        "migration_started_chance": 0.80,
        "high_complexity_chance": 0.15,
        "long_lifetime_chance": 0.30,
        "low_confidence_chance": 0.05,
        "target_count": 105,
    },
    "D": {
        "name": "Stress-Test Environment",
        "description": "Many assets; conflicting policies; expired certs; missing owners; unknown algorithms; long-lived backups; third-party dependencies; high cost; partial evidence",
        "algo_weights": {"quantum_broken": 0.35, "classically_broken": 0.10, "quantum_weakened": 0.15, "quantum_resilient": 0.15, "hybrid": 0.10},
        "cert_expired_chance": 0.40,
        "missing_owner_chance": 0.35,
        "migration_started_chance": 0.15,
        "high_complexity_chance": 0.60,
        "long_lifetime_chance": 0.55,
        "low_confidence_chance": 0.40,
        "target_count": 150,
        "extra_unknown_algos": True,
    },
}

# ─── Migration targets per algorithm ──────────────────────────────────────

MIGRATION_TARGETS = {
    "RSA-1024": "ML-DSA-65",
    "RSA-2048": "ML-DSA-65",
    "RSA-4096": "ML-DSA-87",
    "ECDSA-P256": "ML-DSA-65",
    "ECDSA-P384": "ML-DSA-87",
    "Ed25519": "ML-DSA-65",
    "ECDH-P256": "ML-KEM-768",
    "ECDH-P384": "ML-KEM-1024",
    "DH-2048": "ML-KEM-768",
    "DH-1024": "ML-KEM-768",
    "AES-128": "AES-256",
    "SHA-1": "SHA-384",
    "MD5": "SHA-384",
    "DES": "AES-256",
    "3DES": "AES-256",
    "SHA-256": "SHA-384",  # optional upgrade
    "ML-KEM-768": None,
    "ML-KEM-1024": None,
    "ML-DSA-65": None,
    "ML-DSA-87": None,
    "SLH-DSA-128s": None,
    "SLH-DSA-256f": None,
    "AES-256": None,
    "SHA-384": None,
    "RSA-2048+ML-KEM-768": "ML-KEM-768",
    "ECDSA+ML-DSA-65": "ML-DSA-65",
    "ECDH+ML-KEM-768": "ML-KEM-768",
}

# ─── Sender/Receiver names for ledger ─────────────────────────────────────

LEDGER_PARTICIPANTS = [
    "NovaBank Treasury", "NovaBank Payments", "Customer Alice",
    "Customer Bob", "Merchant Charlie", "Vendor Delta",
    "NovaBank Lending", "NovaBank Insurance", "Escrow Service",
    "NovaBank Wealth Mgmt", "Customer Eve", "Partner FinCo",
]


def _pick_weighted(rng: random.Random, pool_weights: Dict[str, float]) -> Dict[str, Any]:
    """Pick a random algorithm from weighted category pools."""
    categories = list(pool_weights.keys())
    weights = [pool_weights[c] for c in categories]
    category = rng.choices(categories, weights=weights, k=1)[0]

    # Handle unknown algorithms for stress-test
    if category not in ALGORITHMS:
        return {"name": "Unknown-Custom", "role": "unknown", "key_length": 0, "quantum_status": "quantum-broken"}

    return rng.choice(ALGORITHMS[category])


def _generate_date(rng: random.Random, start_year: int = 2020, end_year: int = 2026) -> str:
    """Generate a random date string."""
    year = rng.randint(start_year, end_year)
    month = rng.randint(1, 12)
    day = rng.randint(1, 28)
    return f"{year}-{month:02d}-{day:02d}"


def generate_assets(profile_key: str, seed: int = GLOBAL_SEED) -> List[Dict[str, Any]]:
    """
    Generate synthetic assets for a given dataset profile.
    Returns a list of asset dicts ready for ORM insertion.
    """
    profile = DATASET_PROFILES[profile_key]
    rng = random.Random(seed + ord(profile_key))
    assets = []

    # Start with the 12 core NovaBank assets
    base_assets = list(NOVABANK_CORE_ASSETS)

    # Fill remaining from extra templates
    target_count = profile["target_count"]
    extra_needed = target_count - len(base_assets)
    extra_pool = list(EXTRA_ASSET_TEMPLATES)
    rng.shuffle(extra_pool)

    for i, template in enumerate(extra_pool[:extra_needed]):
        criticality = rng.choice(["low", "medium", "high", "mission-critical"])
        classification = rng.choice(["public", "internal", "confidential", "restricted", "highly_restricted"])
        exposed = rng.random() < 0.35
        exposure_options = ["internet-facing", "internet-no-auth", "vpn-gateway"] if exposed else ["not-exposed"]
        base_assets.append({
            "name": template["name"],
            "type": template["type"],
            "owner": template["owner"],
            "criticality": criticality,
            "classification": classification,
            "exposed": exposed,
            "exposure_detail": rng.choice(exposure_options),
        })

    # If we still need more, duplicate with suffixes
    while len(base_assets) < target_count:
        template = rng.choice(EXTRA_ASSET_TEMPLATES)
        suffix = rng.randint(100, 999)
        base_assets.append({
            "name": f"{template['name']} (Instance {suffix})",
            "type": template["type"],
            "owner": template.get("owner", "Unknown"),
            "criticality": rng.choice(["low", "medium", "high"]),
            "classification": rng.choice(["internal", "confidential", "restricted"]),
            "exposed": rng.random() < 0.25,
            "exposure_detail": rng.choice(["not-exposed", "vpn-gateway", "internet-facing"]),
        })

    for idx, base in enumerate(base_assets[:target_count]):
        asset_num = idx + 1
        asset_id = f"asset-{asset_num:03d}"

        # Pick algorithm based on profile weights
        algo_weights = dict(profile["algo_weights"])

        # Stress-test: add unknown algorithms
        if profile.get("extra_unknown_algos") and rng.random() < 0.15:
            algo_weights["unknown"] = 0.15

        algo = _pick_weighted(rng, algo_weights)

        # Determine data lifetime
        if rng.random() < profile["long_lifetime_chance"]:
            lifetime = rng.choice([10, 15, 20, 25, 30, -1])  # -1 = indefinite
        else:
            lifetime = rng.choice([1, 2, 3, 5, 7])

        # Certificate status
        if algo["role"] in ("digital-signature", "certificate-issuance"):
            if rng.random() < profile["cert_expired_chance"]:
                cert_status = rng.choice(["expired", "revoked"])
            else:
                cert_status = "valid"
        else:
            cert_status = rng.choice(["valid", "not-applicable"])

        # Owner override for missing owners
        owner = base.get("owner", "Unknown")
        if rng.random() < profile["missing_owner_chance"]:
            owner = "Unknown / Unassigned"

        # Migration status
        if algo["quantum_status"] == "quantum-resilient":
            mig_status = "completed"
            mig_target = None
            mig_complexity = "low"
        elif rng.random() < profile["migration_started_chance"]:
            mig_status = rng.choice(["planning", "testing", "deploying"])
            mig_target = MIGRATION_TARGETS.get(algo["name"])
            mig_complexity = rng.choice(["low", "medium", "high"])
        else:
            mig_status = "not-started"
            mig_target = MIGRATION_TARGETS.get(algo["name"])
            if rng.random() < profile["high_complexity_chance"]:
                mig_complexity = rng.choice(["high", "critical"])
            else:
                mig_complexity = rng.choice(["low", "medium"])

        # Confidence
        if rng.random() < profile["low_confidence_chance"]:
            confidence = rng.choice(["low", "unknown"])
        else:
            confidence = rng.choice(["high", "medium"])

        # HNDL
        hndl = (
            algo["quantum_status"] in ("quantum-broken",) and
            base.get("classification", "internal") in ("confidential", "restricted", "highly_restricted") and
            (lifetime > 5 or lifetime == -1)
        )

        # Key rotation
        rotation_days = rng.choice([30, 90, 180, 365, 730, None])
        last_rotation = _generate_date(rng) if rotation_days else None

        # Cost
        base_cost = {"low": 5000, "medium": 25000, "high": 65000, "critical": 120000}
        cost = base_cost.get(mig_complexity, 25000) * (1 + rng.random() * 0.5)
        downtime = rng.choice([0, 1, 2, 4, 8, 12, 24]) if mig_status != "completed" else 0

        # Evidence
        evidence_files = []
        if confidence in ("high", "medium"):
            evidence_files.append(f"synthetic_config/{base['type']}-{asset_num:03d}.yaml")
            if cert_status in ("valid", "expired", "revoked"):
                evidence_files.append(f"synthetic_certificate/{base['type']}-cert-{asset_num:03d}.pem")

        asset = {
            "asset_id": asset_id,
            "dataset_profile": profile_key,
            "asset_name": base["name"],
            "asset_type": base["type"],
            "owner": owner,
            "environment": "production-simulation",
            "data_classification": base.get("classification", "internal"),
            "data_lifetime_years": lifetime if lifetime != -1 else 99,
            "business_criticality": base.get("criticality", "medium"),
            "internet_exposed": base.get("exposed", False),
            "exposure_detail": base.get("exposure_detail", "not-exposed"),
            "algorithm": algo["name"],
            "algorithm_role": algo["role"],
            "key_length": algo["key_length"],
            "key_location": rng.choice(["synthetic-hsm", "software-keystore", "cloud-kms", "embedded"]),
            "key_rotation_days": rotation_days,
            "last_rotation_date": last_rotation,
            "certificate_status": cert_status,
            "quantum_status": algo["quantum_status"],
            "harvest_now_decrypt_later": hndl,
            "migration_target": mig_target,
            "migration_status": mig_status,
            "migration_complexity": mig_complexity,
            "estimated_migration_cost": round(cost, 2),
            "estimated_downtime_hours": downtime,
            "owner_approval_required": mig_complexity in ("high", "critical"),
            "evidence": evidence_files,
            "confidence": confidence,
        }
        assets.append(asset)

    return assets


def generate_ledger_transactions(profile_key: str, count: int = 50, seed: int = GLOBAL_SEED) -> List[Dict[str, Any]]:
    """
    Generate synthetic blockchain ledger transactions (§11).
    SimCoin (SIM) currency.
    """
    rng = random.Random(seed + ord(profile_key) + 1000)
    profile = DATASET_PROFILES[profile_key]
    transactions = []
    prev_hash = "0" * 64  # genesis

    sig_algo_pool = []
    if profile["algo_weights"].get("quantum_broken", 0) > 0.2:
        sig_algo_pool.extend(["ECDSA-P256", "Ed25519", "RSA-2048"])
    if profile["algo_weights"].get("hybrid", 0) > 0.1:
        sig_algo_pool.extend(["ECDSA+ML-DSA-65"])
    if profile["algo_weights"].get("quantum_resilient", 0) > 0.2:
        sig_algo_pool.extend(["ML-DSA-65", "SLH-DSA-128s"])
    if not sig_algo_pool:
        sig_algo_pool = ["ECDSA-P256", "Ed25519"]

    base_time = datetime(2025, 1, 1, 10, 0, 0)

    for i in range(count):
        tx_num = i + 1
        tx_id = f"tx-{tx_num:06d}"
        sender = rng.choice(LEDGER_PARTICIPANTS)
        receiver = rng.choice([p for p in LEDGER_PARTICIPANTS if p != sender])
        amount = round(rng.uniform(0.5, 50000), 2)
        timestamp = base_time + timedelta(hours=rng.randint(1, 8760))

        sig_algo = rng.choice(sig_algo_pool)
        key_id = f"key-{rng.randint(1000, 9999)}"

        # Create transaction hash
        tx_data = f"{tx_id}{sender}{receiver}{amount}{timestamp}{prev_hash}"
        tx_hash = hashlib.sha256(tx_data.encode()).hexdigest()

        # Signature (synthetic)
        sig_data = f"{tx_hash}{key_id}{sig_algo}"
        sig_hex = hashlib.sha256(sig_data.encode()).hexdigest()

        # Determine migration status of this transaction's signature
        if sig_algo in ("ML-DSA-65", "SLH-DSA-128s"):
            mig_status = "post-quantum"
        elif "+" in sig_algo:
            mig_status = "hybrid"
        else:
            mig_status = "legacy"

        # Tamper some transactions for demo (§11)
        is_tampered = rng.random() < 0.08  # ~8% tampered
        if is_tampered:
            sig_status = "invalid"
            sig_hex = hashlib.sha256(f"TAMPERED-{sig_hex}".encode()).hexdigest()
        else:
            sig_status = "valid"

        tx = {
            "tx_id": tx_id,
            "dataset_profile": profile_key,
            "sender": sender,
            "receiver": receiver,
            "amount": amount,
            "timestamp": timestamp.isoformat(),
            "previous_tx_hash": prev_hash,
            "tx_hash": tx_hash,
            "signature_algorithm": sig_algo,
            "public_key_id": key_id,
            "signature_hex": sig_hex,
            "signature_status": sig_status,
            "migration_status": mig_status,
            "block_number": (i // 5) + 1,
            "is_tampered": is_tampered,
        }
        transactions.append(tx)
        prev_hash = tx_hash

    return transactions


def generate_attack_events(profile_key: str, assets: List[Dict], count: int = 20, seed: int = GLOBAL_SEED) -> List[Dict[str, Any]]:
    """Generate synthetic attack events for HNDL and attack-surface simulation."""
    rng = random.Random(seed + ord(profile_key) + 2000)
    events = []
    vulnerable_assets = [a for a in assets if a["quantum_status"] in ("quantum-broken", "classically-broken")]

    if not vulnerable_assets:
        vulnerable_assets = assets[:5]

    event_types = [
        ("harvest", "Encrypted data captured for future quantum decryption", False),
        ("decrypt-attempt", "Simulated quantum decryption attempt on harvested data", False),
        ("key-compromise", "Simulated private key extraction via quantum factoring", True),
        ("signature-forge", "Simulated digital signature forgery using quantum capabilities", True),
    ]

    base_time = datetime(2025, 6, 1, 0, 0, 0)

    for i in range(min(count, len(vulnerable_assets) * 2)):
        evt_num = i + 1
        asset = rng.choice(vulnerable_assets)
        evt_type, description, needs_high_qubits = rng.choice(event_types)

        qubits_needed = rng.randint(2000, 4000) if needs_high_qubits else rng.randint(100, 1000)
        success = rng.random() < 0.3 if needs_high_qubits else rng.random() < 0.6

        events.append({
            "event_id": f"evt-{evt_num:04d}",
            "asset_id": asset["asset_id"],
            "dataset_profile": profile_key,
            "event_type": evt_type,
            "description": f"{description} — target: {asset['asset_name']} ({asset['algorithm']})",
            "timestamp": (base_time + timedelta(hours=rng.randint(0, 4380))).isoformat(),
            "quantum_capability_required": qubits_needed,
            "success": success,
            "impact": rng.choice(["low", "medium", "high", "critical"]),
            "evidence": [f"synthetic_log/event-{evt_num:04d}.json"],
        })

    return events


def generate_full_dataset(profile_key: str, seed: int = GLOBAL_SEED) -> Dict[str, Any]:
    """
    Generate a complete synthetic dataset for a given profile.
    Returns dict with assets, transactions, attack_events, and metadata.
    """
    if profile_key not in DATASET_PROFILES:
        raise ValueError(f"Unknown profile: {profile_key}. Must be A, B, C, or D.")

    profile = DATASET_PROFILES[profile_key]
    assets = generate_assets(profile_key, seed)
    transactions = generate_ledger_transactions(
        profile_key,
        count=50 if profile_key != "D" else 80,
        seed=seed
    )
    attack_events = generate_attack_events(
        profile_key, assets,
        count=20 if profile_key != "D" else 35,
        seed=seed
    )

    return {
        "profile": profile_key,
        "name": profile["name"],
        "description": profile["description"],
        "seed": seed,
        "asset_count": len(assets),
        "transaction_count": len(transactions),
        "event_count": len(attack_events),
        "assets": assets,
        "transactions": transactions,
        "attack_events": attack_events,
    }
