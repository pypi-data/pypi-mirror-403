from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON, event
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from datetime import datetime
from typing import Dict, Any
import json
import hashlib

DATABASE_URL = "sqlite:///./lnt_sovereign.db"

# Hardened SQLite Engine with WAL mode for high-concurrency
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection: Any, connection_record: Any) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class DecisionAudit(Base): # type: ignore
    """
    Hardened audit table for AIDA-compliant decision tracking.
    Includes 'Sovereign Proof' signature chaining.
    """
    __tablename__ = "decision_audits"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    domain = Column(String(50))
    user_input = Column(Text)
    neural_proposal = Column(JSON)
    symbolic_status = Column(String(20))
    explanation = Column(Text)
    sovereign_proof = Column(String(64))  # SHA-256 Hash
    previous_hash = Column(String(64))    # Signature Chain
    bias_score = Column(JSON)
    metadata_json = Column(JSON)

Base.metadata.create_all(bind=engine)

def get_last_hash(db: Session) -> str:
    """Retrieves the hash of the most recent audit entry to maintain the chain."""
    last_entry = db.query(DecisionAudit).order_by(DecisionAudit.id.desc()).first()
    if last_entry and hasattr(last_entry, 'sovereign_proof'):
        res: str = str(last_entry.sovereign_proof)
        return res
    return "GENESIS_BLOCK"

def log_decision(
    domain: str, 
    user_input: str, 
    proposal: Dict[str, Any], 
    result: Dict[str, Any], 
    bias_score: float = 1.0
) -> None:
    """
    Persists a neuro-symbolic decision to the secure audit ledger with signature chaining.
    """
    db: Session = SessionLocal()
    try:
        prev_hash = get_last_hash(db)
        
        # Build the proof hash (chaining logic)
        proof_payload = {
            "prev_hash": prev_hash,
            "domain": domain,
            "input": user_input,
            "status": result.get("status"),
            "timestamp": datetime.utcnow().isoformat()
        }
        proof_hash = hashlib.sha256(json.dumps(proof_payload, sort_keys=True).encode()).hexdigest()

        audit_entry = DecisionAudit(
            domain=domain,
            user_input=user_input,
            neural_proposal=proposal,
            symbolic_status=result.get("status", "UNKNOWN"),
            explanation=result.get("explanation", "N/A"),
            sovereign_proof=proof_hash,
            previous_hash=prev_hash,
            bias_score=bias_score,
            metadata_json=result.get("proof", {}) if isinstance(result.get("proof"), dict) else {}
        )
        db.add(audit_entry)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
