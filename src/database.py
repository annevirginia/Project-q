"""
QuantumShield v2 — SQLite Database Setup
Uses SQLAlchemy ORM for all simulation data.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "quantumshield.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


def get_db():
    """Yield a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables."""
    from src.models import (
        Asset, Finding, MigrationTask, SignatureRecord,
        LedgerTransaction, AttackEvent, AuditLog, DatasetMeta
    )
    Base.metadata.create_all(bind=engine)


def reset_db():
    """Drop and recreate all tables."""
    from src.models import (
        Asset, Finding, MigrationTask, SignatureRecord,
        LedgerTransaction, AttackEvent, AuditLog, DatasetMeta
    )
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
