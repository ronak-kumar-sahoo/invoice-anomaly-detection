from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import predict, upload, history
from app.database.db import create_tables

app = FastAPI(
    title="Invoice & Payment Anomaly Detection API",
    description="An end-to-end API for detecting anomalies in invoices and payment transactions using ML and rule-based logic.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    create_tables()
    print("Database tables created.")

@app.get("/")
def root():
    return {
        "message": "Invoice Anomaly Detection API is running.",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

app.include_router(predict.router, tags=["Prediction"])
app.include_router(upload.router, tags=["Upload"])
app.include_router(history.router, tags=["History"])