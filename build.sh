#!/bin/bash
apt-get update && apt-get install -y tesseract-ocr poppler-utils
pip install -r requirements.txt
python ml/invoice_generator.py
python ml/invoice_train.py
python ml/payment_generator.py
python ml/payment_train.py