"""
QuantumShield v2 — SQLAlchemy ORM Models
All entities for the post-quantum cryptographic simulation.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text, DateTime, JSON, ForeignKey
)
from sqlalchemy.orm import relationship
from src.database import Base


class DatasetMeta(Base):
    """Tracks which synthetic dataset profile is currently loaded."""
    __tablename__ = "dataset_meta"

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile = Column(String(1), nullable=False)  # A, B, C, D
    name = Column(String(100), nullable=False)
    description = Column(Text)
    loaded_at = Column(DateTime, default=datetime.utcnow)
    record_count = Column(Integer, default=0)
    seed_value = Column(Integer, default=42)


class Asset(Base):
    """
    A synthetic cryptographic asset (§2).
    Covers: applications, APIs, databases, backup systems, certificates,
    keys, signatures, blockchain transactions, users, cloud storage,
    third-party integrations, network connections, data assets.
    """
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    asset_id = Column(String(20), unique=True, nullable=False, index=True)  # e.g. asset-001
    dataset_profile = Column(String(1), nullable=False)  # A, B, C, D
    asset_name = Column(String(200), nullable=False)
    asset_type = Column(String(50), nullable=False)  # api, database, certificate, etc.
    owner = Column(String(200))
    environment = Column(String(50), default="production-simulation")
    data_classification = Column(String(30))  # public, internal, confidential, restricted, highly_restricted
    data_lifetime_years = Column(Integer)
    business_criticality = Column(String(30))  # low, medium, high, mission-critical
    internet_exposed = Column(Boolean, default=False)
    exposure_detail = Column(String(50))  # not-exposed, vpn-gateway, internet-facing, internet-no-auth

    # Cryptographic properties
    algorithm = Column(String(50))  # RSA-2048, ECDSA, ML-DSA, etc.
    algorithm_role = Column(String(50))  # key-establishment, encryption, digital-signature, hashing, etc.
    key_length = Column(Integer)
    key_location = Column(String(100))  # synthetic-hsm, software, cloud-kms
    key_rotation_days = Column(Integer)
    last_rotation_date = Column(String(20))
    certificate_status = Column(String(20))  # valid, expired, revoked, unknown

    # Quantum classification
    quantum_status = Column(String(30))  # quantum-broken, quantum-weakened, classically-broken, quantum-resilient
    harvest_now_decrypt_later = Column(Boolean, default=False)

    # Migration
    migration_target = Column(String(50))  # ML-KEM, ML-DSA, SLH-DSA, Hybrid, AES-256
    migration_status = Column(String(30))  # not-started, planning, testing, deploying, completed
    migration_complexity = Column(String(20))  # low, medium, high, critical
    estimated_migration_cost = Column(Float, default=0)
    estimated_downtime_hours = Column(Float, default=0)
    owner_approval_required = Column(Boolean, default=True)

    # Evidence
    evidence = Column(JSON)  # list of synthetic evidence file paths
    confidence = Column(String(20), default="high")  # high, medium, low, unknown

    # Relationships
    findings = relationship("Finding", back_populates="asset", cascade="all, delete-orphan")
    migration_tasks = relationship("MigrationTask", back_populates="asset", cascade="all, delete-orphan")
    signatures = relationship("SignatureRecord", back_populates="asset", cascade="all, delete-orphan")

    created_at = Column(DateTime, default=datetime.utcnow)


class Finding(Base):
    """
    A cryptographic finding produced by the Inventory Engine (§4).
    """
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    finding_id = Column(String(20), unique=True, nullable=False, index=True)  # e.g. find-0001
    asset_id = Column(String(20), ForeignKey("assets.asset_id"), nullable=False)
    dataset_profile = Column(String(1), nullable=False)

    algorithm = Column(String(50))
    algorithm_role = Column(String(50))

    # Risk breakdown (§5 — 7 factors)
    algorithm_risk = Column(Float, default=0)
    data_sensitivity = Column(Float, default=0)
    data_lifetime = Column(Float, default=0)
    asset_criticality = Column(Float, default=0)
    internet_exposure = Column(Float, default=0)
    migration_complexity_score = Column(Float, default=0)
    inventory_uncertainty = Column(Float, default=0)

    # Computed
    risk_score = Column(Float, default=0)  # 0–100
    risk_band = Column(String(20))  # Low, Moderate, High, Critical
    priority = Column(Integer, default=0)  # 1 = highest

    # HNDL
    hndl_status = Column(String(50))

    # Evidence & explanation
    evidence = Column(JSON)
    confidence = Column(String(20))
    recommended_action = Column(Text)
    explanation = Column(Text)  # Human-readable breakdown

    # Relationship
    asset = relationship("Asset", back_populates="findings")

    created_at = Column(DateTime, default=datetime.utcnow)


class MigrationTask(Base):
    """
    Per-asset migration record (§8.3).
    """
    __tablename__ = "migration_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(20), unique=True, nullable=False, index=True)  # e.g. mig-0001
    asset_id = Column(String(20), ForeignKey("assets.asset_id"), nullable=False)
    dataset_profile = Column(String(1), nullable=False)

    current_algorithm = Column(String(50))
    recommended_target = Column(String(50))
    migration_phase = Column(Integer, default=1)  # 1–11
    phase_name = Column(String(50))
    migration_owner = Column(String(200))
    dependencies = Column(JSON)  # list of dependent asset_ids
    compatibility_risk = Column(String(20))
    estimated_cost = Column(Float, default=0)
    estimated_downtime_hours = Column(Float, default=0)
    testing_requirements = Column(Text)
    rollback_plan = Column(Text)
    approval_required = Column(Boolean, default=True)
    approval_status = Column(String(20), default="pending")  # pending, approved, rejected
    progress_percent = Column(Float, default=0)
    validation_status = Column(String(20), default="not-started")  # not-started, in-progress, passed, failed

    asset = relationship("Asset", back_populates="migration_tasks")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SignatureRecord(Base):
    """
    Digital signature forensics record (§10).
    """
    __tablename__ = "signatures"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sig_id = Column(String(20), unique=True, nullable=False, index=True)  # e.g. sig-0001
    asset_id = Column(String(20), ForeignKey("assets.asset_id"), nullable=False)
    dataset_profile = Column(String(1), nullable=False)

    algorithm = Column(String(50))  # RSA-PSS, ECDSA, Ed25519, ML-DSA, SLH-DSA
    key_id = Column(String(50))
    document_hash = Column(String(128))
    signature_hex = Column(Text)
    public_key_hex = Column(Text)

    status = Column(String(20))  # valid, invalid, tampered, expired
    certificate_status = Column(String(20))
    data_lifetime_years = Column(Integer)
    quantum_status = Column(String(30))
    evidence = Column(JSON)
    confidence = Column(String(20))
    recommended_action = Column(Text)

    asset = relationship("Asset", back_populates="signatures")

    created_at = Column(DateTime, default=datetime.utcnow)


class LedgerTransaction(Base):
    """
    Blockchain-style ledger transaction (§11).
    Currency: SimCoin (SIM).
    """
    __tablename__ = "ledger_transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tx_id = Column(String(20), unique=True, nullable=False, index=True)  # e.g. tx-000001
    dataset_profile = Column(String(1), nullable=False)

    sender = Column(String(100), nullable=False)
    receiver = Column(String(100), nullable=False)
    amount = Column(Float, nullable=False)  # in SIM
    timestamp = Column(DateTime, default=datetime.utcnow)
    previous_tx_hash = Column(String(128))
    tx_hash = Column(String(128))

    signature_algorithm = Column(String(50))
    public_key_id = Column(String(50))
    signature_hex = Column(Text)
    signature_status = Column(String(20))  # valid, invalid, tampered
    migration_status = Column(String(30))  # legacy, hybrid, post-quantum
    block_number = Column(Integer, default=0)

    is_tampered = Column(Boolean, default=False)  # For demo: flag synthetic tampering

    created_at = Column(DateTime, default=datetime.utcnow)


class AttackEvent(Base):
    """
    Simulated attack event for the HNDL and attack-surface modules.
    """
    __tablename__ = "attack_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(20), unique=True, nullable=False, index=True)  # e.g. evt-0001
    asset_id = Column(String(20), nullable=False)
    dataset_profile = Column(String(1), nullable=False)

    event_type = Column(String(50))  # harvest, decrypt-attempt, key-compromise, signature-forge
    description = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    quantum_capability_required = Column(Integer)  # logical qubits
    success = Column(Boolean, default=False)
    impact = Column(String(20))  # low, medium, high, critical
    evidence = Column(JSON)

    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    """
    Audit log for all simulation actions (§19).
    """
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_role = Column(String(20), default="analyst")  # viewer, analyst, admin
    action = Column(String(100), nullable=False)
    target = Column(String(200))
    details = Column(Text)
    ip_address = Column(String(50))
