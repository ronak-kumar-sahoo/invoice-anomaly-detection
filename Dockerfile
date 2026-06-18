FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y tesseract-ocr poppler-utils && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Generate datasets and train models
RUN python ml/invoice_generator.py && \
    python ml/invoice_train.py && \
    python ml/payment_generator.py && \
    python ml/payment_train.py

# Expose port
EXPOSE 10000

# Start FastAPI
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","10000"]