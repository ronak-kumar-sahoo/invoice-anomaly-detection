from sqlalchemy import create_engine, Column, String, Float, Boolean, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./invoice_anomaly.db")

# Fix for PostgreSQL URL format from Render
# Render gives "postgres://" but SQLAlchemy needs "postgresql://"
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SQLite needs extra argument, PostgreSQL does not
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(DATABASE_URL)

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

class PaymentRecord(Base):
    __tablename__ = "payment_records"

    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(String, index=True)
    vendor_id = Column(String)
    invoice_amount = Column(Float)
    paid_amount = Column(Float)
    payment_method = Column(String)
    previous_method = Column(String)
    transaction_hour = Column(Integer)
    payment_frequency = Column(Integer)
    is_partial_payment = Column(Boolean)
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