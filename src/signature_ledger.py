"""
QuantumShield v2 — Digital Signature Forensics (§10) & Blockchain Ledger Simulator (§11)

Synthetic key generation, signature verification, tamper detection.
SimCoin (SIM) ledger with legacy/hybrid/PQC signature comparison.
"""

import hashlib
import hmac
import json
import random
from typing import Dict, Any, List
from datetime import datetime
from src.crypto_inventory import classify_algorithm


# ─── Digital Signature Forensics (§10) ────────────────────────────────────

def generate_signature_records(assets: List[Dict], seed: int = 42) -> List[Dict[str, Any]]:
    """
    Generate synthetic signature records for signature-related assets (§10).
    Demonstrates: valid, tampered, invalid, expired, and migrated signatures.
    """
    rng = random.Random(seed + 3000)
    records = []

    sig_assets = [a for a in assets if a.get("algorithm_role") == "digital-signature"]
    if not sig_assets:
        sig_assets = assets[:10]

    for idx, asset in enumerate(sig_assets):
        sig_id = f"sig-{idx + 1:04d}"
        algo = asset.get("algorithm", "ECDSA-P256")

        # Generate synthetic key material
        key_seed = f"{sig_id}-{algo}-{seed}"
        private_key_material = hashlib.sha256(key_seed.encode()).hexdigest()
        public_key_hex = hashlib.sha256(f"pub-{private_key_material}".encode()).hexdigest()
        key_id = f"key-{hashlib.md5(key_seed.encode()).hexdigest()[:8]}"

        # Generate synthetic document
        doc_content = f"Synthetic document for {asset.get('asset_name', 'Unknown')} — generated for simulation"
        doc_hash = hashlib.sha256(doc_content.encode()).hexdigest()

        # Generate signature
        sig_material = f"{doc_hash}{private_key_material}{algo}"
        signature_hex = hashlib.sha256(sig_material.encode()).hexdigest()

        # Determine signature status
        status_roll = rng.random()
        cert_status = asset.get("certificate_status", "valid")

        if status_roll < 0.05:
            # Tampered document
            status = "tampered"
            doc_hash = hashlib.sha256(f"TAMPERED-{doc_content}".encode()).hexdigest()
        elif cert_status == "expired":
            status = "expired"
        elif cert_status == "revoked":
            status = "invalid"
        elif status_roll < 0.10:
            status = "invalid"
            signature_hex = hashlib.sha256(f"WRONG-{sig_material}".encode()).hexdigest()
        else:
            status = "valid"

        algo_info = classify_algorithm(algo)

        record = {
            "sig_id": sig_id,
            "asset_id": asset.get("asset_id"),
            "dataset_profile": asset.get("dataset_profile", "A"),
            "algorithm": algo,
            "key_id": key_id,
            "document_hash": doc_hash,
            "signature_hex": signature_hex,
            "public_key_hex": public_key_hex,
            "status": status,
            "certificate_status": cert_status,
            "data_lifetime_years": asset.get("data_lifetime_years", 1),
            "quantum_status": algo_info["category"],
            "evidence": [f"synthetic_document/doc-{idx + 1:04d}.txt", f"synthetic_key/{key_id}.pem"],
            "confidence": "high" if status in ("valid", "tampered") else "medium",
            "recommended_action": _sig_recommended_action(algo, algo_info, status, asset.get("migration_target")),
        }
        records.append(record)

    return records


def verify_signature(sig_record: Dict) -> Dict[str, Any]:
    """
    Simulate signature verification.
    Returns verification result with explanation.
    """
    status = sig_record.get("status", "unknown")
    algo = sig_record.get("algorithm", "Unknown")
    algo_info = classify_algorithm(algo)

    if status == "valid":
        result = {
            "verified": True,
            "status": "VALID",
            "message": f"Signature verified successfully using {algo}.",
            "quantum_warning": algo_info["category"] == "quantum-broken",
            "quantum_detail": (
                f"WARNING: {algo} is vulnerable to {algo_info['attack']}. "
                f"This signature will become forgeable when a CRQC is available."
            ) if algo_info["category"] == "quantum-broken" else None,
        }
    elif status == "tampered":
        result = {
            "verified": False,
            "status": "TAMPERED",
            "message": f"Document integrity check FAILED. The document has been modified after signing.",
            "quantum_warning": True,
            "quantum_detail": f"Document was tampered with — signature does not match the current document hash.",
        }
    elif status == "expired":
        result = {
            "verified": False,
            "status": "EXPIRED",
            "message": f"Signing certificate has expired. Signature was valid at time of signing but certificate is no longer trusted.",
            "quantum_warning": algo_info["category"] == "quantum-broken",
            "quantum_detail": None,
        }
    else:
        result = {
            "verified": False,
            "status": "INVALID",
            "message": f"Signature verification FAILED. The signature does not match the document/key pair.",
            "quantum_warning": True,
            "quantum_detail": "Invalid signature — could indicate key compromise or corruption.",
        }

    return result


def _sig_recommended_action(algo: str, algo_info: Dict, status: str, target: str) -> str:
    """Generate recommendation for a signature finding."""
    parts = []

    if status == "tampered":
        parts.append("CRITICAL: Investigate document tampering. Revoke and re-sign.")
    elif status == "invalid":
        parts.append("Investigate invalid signature. Verify key integrity.")
    elif status == "expired":
        parts.append("Renew certificate and re-sign document.")

    if algo_info["category"] == "quantum-broken":
        parts.append(
            f"Migrate {algo} signatures to {target or 'ML-DSA/SLH-DSA (FIPS 204/205)'}. "
            f"Plan historical re-signing for long-lived documents."
        )
    elif algo_info["category"] == "classically-broken":
        parts.append(f"URGENT: {algo} is classically broken. Migrate immediately.")

    return " ".join(parts) if parts else f"Signature is valid and uses quantum-resilient {algo}. No action required."


# ─── Blockchain Ledger Simulator (§11) ────────────────────────────────────

def verify_ledger_chain(transactions: List[Dict]) -> Dict[str, Any]:
    """
    Verify the integrity of the blockchain-style ledger.
    Checks hash chain continuity and signature validity.
    """
    valid_count = 0
    tampered_count = 0
    legacy_count = 0
    hybrid_count = 0
    pqc_count = 0
    chain_breaks = []
    tampered_txs = []

    prev_hash = "0" * 64  # genesis

    for i, tx in enumerate(transactions):
        tx_id = tx.get("tx_id", f"tx-{i}")

        # Check hash chain
        expected_prev = prev_hash
        actual_prev = tx.get("previous_tx_hash", "")

        if i > 0 and actual_prev != expected_prev:
            chain_breaks.append({
                "tx_id": tx_id,
                "block": tx.get("block_number"),
                "expected_prev_hash": expected_prev[:16] + "...",
                "actual_prev_hash": actual_prev[:16] + "...",
            })

        # Check signature
        if tx.get("is_tampered") or tx.get("signature_status") == "invalid":
            tampered_count += 1
            tampered_txs.append({
                "tx_id": tx_id,
                "sender": tx.get("sender"),
                "receiver": tx.get("receiver"),
                "amount": tx.get("amount"),
                "algorithm": tx.get("signature_algorithm"),
                "block": tx.get("block_number"),
            })
        else:
            valid_count += 1

        # Count migration status
        mig = tx.get("migration_status", "legacy")
        if mig == "legacy":
            legacy_count += 1
        elif mig == "hybrid":
            hybrid_count += 1
        elif mig == "post-quantum":
            pqc_count += 1

        prev_hash = tx.get("tx_hash", "")

    total = len(transactions)
    return {
        "total_transactions": total,
        "valid_transactions": valid_count,
        "tampered_transactions": tampered_count,
        "chain_integrity": len(chain_breaks) == 0,
        "chain_breaks": chain_breaks,
        "tampered_details": tampered_txs,
        "signature_migration": {
            "legacy": legacy_count,
            "hybrid": hybrid_count,
            "post_quantum": pqc_count,
            "legacy_pct": round((legacy_count / max(total, 1)) * 100, 1),
            "pqc_pct": round((pqc_count / max(total, 1)) * 100, 1),
        },
        "recommendation": _ledger_recommendation(legacy_count, tampered_count, total),
    }


def simulate_ledger_migration(transactions: List[Dict], target_algo: str = "ML-DSA-65") -> Dict[str, Any]:
    """
    Simulate migrating ledger signatures from legacy to PQC.
    Returns before/after comparison.
    """
    before = verify_ledger_chain(transactions)

    # Simulate migration: re-sign legacy transactions
    migrated = []
    migrated_count = 0
    for tx in transactions:
        mod = dict(tx)
        if mod.get("migration_status") == "legacy":
            mod["signature_algorithm"] = target_algo
            mod["migration_status"] = "post-quantum"
            # Re-generate signature
            sig_data = f"{mod['tx_hash']}{mod.get('public_key_id', '')}{target_algo}"
            mod["signature_hex"] = hashlib.sha256(sig_data.encode()).hexdigest()
            if not mod.get("is_tampered"):
                mod["signature_status"] = "valid"
            migrated_count += 1
        migrated.append(mod)

    after = verify_ledger_chain(migrated)

    return {
        "before": before,
        "after": after,
        "migrated_count": migrated_count,
        "target_algorithm": target_algo,
        "improvement": {
            "legacy_reduction": before["signature_migration"]["legacy"] - after["signature_migration"]["legacy"],
            "pqc_gain": after["signature_migration"]["post_quantum"] - before["signature_migration"]["post_quantum"],
        },
    }


def _ledger_recommendation(legacy_count: int, tampered_count: int, total: int) -> str:
    """Generate ledger recommendation."""
    parts = []
    if tampered_count > 0:
        parts.append(f"ALERT: {tampered_count} tampered transaction(s) detected. Investigate immediately.")
    if legacy_count > 0:
        pct = (legacy_count / max(total, 1)) * 100
        parts.append(
            f"{legacy_count} transactions ({pct:.0f}%) use legacy signatures vulnerable to quantum attack. "
            f"Plan migration to ML-DSA (FIPS 204) for transaction signing."
        )
    if not parts:
        parts.append("Ledger is healthy. All transactions use quantum-resilient signatures.")
    return " ".join(parts)
