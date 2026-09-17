from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
import joblib
import numpy as np
import re
from urllib.parse import urlparse
import time
from typing import List, Dict

# 1. Initialize FastAPI App
app = FastAPI(
    title="Phishing URL Shield API",
    description="Machine Learning REST API for Real-time Phishing Detection",
    version="1.0.0"
)

# Enable CORS for Frontend (React, Vue, or Vanilla HTML/JS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Global In-Memory Storage & Artifacts Loading
history_logs: List[Dict] = []

try:
    model = joblib.load('../../ml-pipeline/model/phishing_rf_model.pkl')
    scaler = joblib.load('../../ml-pipeline/model/scaler.pkl')
    features_list = joblib.load('../../ml-pipeline/model/features_list.pkl')
    print("✓ All ML artifacts loaded successfully.")
except Exception as e:
    print(f"Error loading model files: {e}")
    model = None
    scaler = None
    features_list = []

# 3. Pydantic Models for Input Validation
class SingleURLRequest(BaseModel):
    url: str

class BatchURLRequest(BaseModel):
    urls: List[str]

# 4. Feature Extraction Function (Raw URL -> 10 Numerical Features)
def extract_features(raw_url: str):
    url = raw_url.strip()
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url

    parsed = urlparse(url)
    hostname = parsed.netloc if parsed.netloc else parsed.path.split('/')[0]

    # Feature 1: URL Length
    length_url = len(url)

    # Feature 2, 3, 4: Counts of dots, hyphens, slashes
    nb_dots = url.count('.')
    nb_hyphens = url.count('-')
    nb_slash = url.count('/')

    # Feature 5: Subdomain Count
    subdomains = hostname.split('.')
    nb_subdomains = max(0, len(subdomains) - 2)

    # Feature 6: Prefix/Suffix '-' in Domain
    prefix_suffix = 1 if '-' in hostname else 0

    # Feature 7: URL Shortening Services
    shorteners_regex = r'(bit\.ly|tinyurl\.com|t\.co|goo\.gl|is\.gd|cutt\.ly|ow\.ly)'
    shortening_service = 1 if re.search(shorteners_regex, url.lower()) else 0

    # Feature 8: Phishing Trigger Keywords
    phish_keywords = r'(login|verify|update|banking|secure|signin|account|wallet|confirm)'
    phish_hints = 1 if re.search(phish_keywords, url.lower()) else 0

    # Feature 9: Presence of IP Address instead of Domain
    ip_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    clean_host = hostname.split(':')[0]
    ip = 1 if re.match(ip_pattern, clean_host) else 0

    # Feature 10: HTTPS Token in hostname/path (spoofing trick)
    https_token = 1 if 'https' in hostname.lower() else 0

    return [
        length_url, nb_dots, nb_hyphens, nb_slash,
        nb_subdomains, prefix_suffix, shortening_service,
        phish_hints, ip, https_token
    ]

# 5. Core Prediction Helper
def perform_prediction(raw_url: str):
    features = extract_features(raw_url)
    features_scaled = scaler.transform([features])

    prediction = int(model.predict(features_scaled)[0])
    probabilities = model.predict_proba(features_scaled)[0]
    risk_percentage = round(float(probabilities[1]) * 100, 2)

    is_phishing = prediction == 1
    status = "Phishing / Malicious" if is_phishing else "Legitimate / Safe"

    feature_dict = dict(zip(features_list, features))

    result = {
        "url": raw_url,
        "is_phishing": is_phishing,
        "status": status,
        "risk_score_percentage": risk_percentage,
        "features": feature_dict,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    # Save to in-memory history log
    history_logs.insert(0, {
        "url": raw_url,
        "status": status,
        "risk": risk_percentage,
        "timestamp": result["timestamp"]
    })
    if len(history_logs) > 50:
        history_logs.pop()

    return result

# ==================== REST API Endpoints ====================

@app.get("/")
def health_check():
    """Server & Model Health Check Endpoint"""
    return {
        "status": "Online",
        "model_loaded": model is not None,
        "algorithm": "Random Forest Classifier",
        "features_count": len(features_list)
    }

@app.post("/predict")
def predict_single(payload: SingleURLRequest):
    """Predict risk for a single URL"""
    if not model or not scaler:
        raise HTTPException(status_code=500, detail="ML Models are not loaded on server.")
    
    clean_url = payload.url.strip()
    if not clean_url:
        raise HTTPException(status_code=400, detail="URL cannot be empty.")

    return perform_prediction(clean_url)

@app.post("/predict-batch")
def predict_batch(payload: BatchURLRequest):
    """Predict multiple URLs at once (useful for scanning lists/bookmarks)"""
    if not model or not scaler:
        raise HTTPException(status_code=500, detail="ML Models are not loaded on server.")
    
    if not payload.urls:
        raise HTTPException(status_code=400, detail="URL list cannot be empty.")

    results = [perform_prediction(url.strip()) for url in payload.urls if url.strip()]
    return {
        "total_analyzed": len(results),
        "results": results
    }

@app.get("/model-info")
def get_model_info():
    """Endpoint displaying model metadata, accuracy, parameters, and features"""
    if not model:
        raise HTTPException(status_code=500, detail="Model is not loaded.")

    # Tree based models store feature importances
    importances = model.feature_importances_
    feat_importance_dict = {
        feat: round(float(imp) * 100, 2)
        for feat, imp in zip(features_list, importances)
    }

    return {
        "model_name": "Random Forest Classifier",
        "benchmark_test_accuracy": "96.40%",
        "benchmark_f1_score": "0.963",
        "total_features": len(features_list),
        "feature_names": features_list,
        "feature_importance_weights": feat_importance_dict,
        "estimators_count": getattr(model, "n_estimators", 100)
    }

@app.get("/history")
def get_recent_scans():
    """Fetch the latest scanned URLs for dashboard activity"""
    return {
        "count": len(history_logs),
        "recent_scans": history_logs[:20]
    }