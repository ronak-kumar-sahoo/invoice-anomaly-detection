from sqlalchemy import create_engine, Column, String, Float, Boolean, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = "sqlite:///./invoice_anomaly.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class InvoiceRecord(Base):
    __tablename__ = "invoice_records"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(String, index=True)
    vendor_id = Column(String)
    category = Column(String)
    amount = Column(Float)
    quantity = Column(Integer)
    unit_price = Column(Float)
    payment_delay = Column(Integer)
    is_anomaly = Column(Boolean)
    ml_risk_score = Column(Float)
    rule_risk_score = Column(Float)
    final_risk_score = Column(Float)
    risk_level = Column(String)
    flags = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

def create_tables():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()