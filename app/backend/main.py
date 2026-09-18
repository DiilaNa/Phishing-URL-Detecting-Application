from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse
import ipaddress
import re
import time

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


# ============================================================
# Application Configuration
# ============================================================

APP_TITLE = "Phishing URL Shield API"
APP_DESCRIPTION = (
    "Machine Learning REST API for real-time phishing URL detection"
)
APP_VERSION = "1.0.0"


# ============================================================
# ML Artifact Paths
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent.parent
MODEL_DIR = PROJECT_ROOT / "ml-pipeline" / "model"

MODEL_PATH = MODEL_DIR / "phishing_rf_model.pkl"
SCALER_PATH = MODEL_DIR / "scaler.pkl"
FEATURES_PATH = MODEL_DIR / "features_list.pkl"


# ============================================================
# Constants for Feature Extraction
# ============================================================

KNOWN_SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "is.gd",
    "cutt.ly", "ow.ly", "rebrand.ly", "t.ly", "qr.ae"
}

PHISH_KEYWORDS_REGEX = (
    r"(login|verify|update|banking|secure|signin|account|"
    r"wallet|confirm|credential|password|auth|billing)"
)


# ============================================================
# FastAPI Application & CORS Configuration
# ============================================================

app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Global Application State
# ============================================================

model = None
scaler = None
features_list: List[str] = []
history_logs: List[Dict] = []


# ============================================================
# Model Loading
# ============================================================

def load_ml_artifacts() -> None:
    """Load the trained ML model, scaler and feature list."""
    global model, scaler, features_list

    try:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
        if not SCALER_PATH.exists():
            raise FileNotFoundError(f"Scaler file not found: {SCALER_PATH}")
        if not FEATURES_PATH.exists():
            raise FileNotFoundError(f"Features file not found: {FEATURES_PATH}")

        model = joblib.load(MODEL_PATH)
        scaler = joblib.load(SCALER_PATH)
        features_list = joblib.load(FEATURES_PATH)

        if not isinstance(features_list, list):
            raise TypeError("features_list.pkl must contain a list.")

        print("✓ All ML artifacts loaded successfully.")
        print(f"✓ Model: {MODEL_PATH}")
        print(f"✓ Scaler: {SCALER_PATH}")
        print(f"✓ Features: {len(features_list)}")

    except Exception as exc:
        model = None
        scaler = None
        features_list = []
        print(f"✗ Failed to load ML artifacts: {exc}")


load_ml_artifacts()


# ============================================================
# Pydantic Request Models
# ============================================================

class SingleURLRequest(BaseModel):
    url: str = Field(
        ...,
        min_length=1,
        max_length=2048,
        description="URL to analyze",
    )


class BatchURLRequest(BaseModel):
    urls: List[str] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="URLs to analyze",
    )


# ============================================================
# Numerical Feature Extraction for Machine Learning Model
# ============================================================

def extract_features(raw_url: str) -> List[int]:
    """
    Extract the 10 numerical features expected by the Random Forest model:
    1. length_url: Total length of the URL
    2. nb_dots: Number of dots ('.')
    3. nb_hyphens: Number of hyphens ('-')
    4. nb_slash: Number of slashes ('/')
    5. nb_subdomains: Number of subdomains in host
    6. prefix_suffix: Presence of '-' in domain host (0 or 1)
    7. shortening_service: Domain is a known URL shortener (0 or 1)
    8. phish_hints: Phishing keyword presence (0 or 1)
    9. ip: Host is an IP address (0 or 1)
    10. https_token: Protocol is insecure HTTP (0: HTTPS, 1: HTTP)
    """
    url = raw_url.strip()
    if not url:
        raise ValueError("URL cannot be empty.")

    # Normalize protocol for URL parsing if omitted
    if not url.lower().startswith(("http://", "https://")):
        normalized_url = "https://" + url
    else:
        normalized_url = url

    parsed = urlparse(normalized_url)
    hostname = parsed.netloc or parsed.path.split("/")[0]

    if "@" in hostname:
        hostname = hostname.split("@")[-1]

    clean_host = hostname.split(":")[0].lower()

    # 1. Feature: URL Length
    length_url = len(url)

    # 2. Feature: Dot count
    nb_dots = url.count(".")

    # 3. Feature: Hyphen count
    nb_hyphens = url.count("-")

    # 4. Feature: Slash count
    nb_slash = url.count("/")

    # 5. Feature: Subdomains count
    host_parts = [p for p in clean_host.split(".") if p]
    nb_subdomains = max(1, len(host_parts) - 1)

    # 6. Feature: Prefix / Suffix
    prefix_suffix = 1 if "-" in clean_host else 0

    # 7. Feature: Shortening Service
    shortening_service = 1 if (
        clean_host in KNOWN_SHORTENERS
        or any(clean_host.endswith("." + s) for s in KNOWN_SHORTENERS)
    ) else 0

    # 8. Feature: Phishing Keyword Hints (phish_hints feature in dataset)
    phish_hints = 1 if re.search(PHISH_KEYWORDS_REGEX, url.lower()) else 0

    # 9. Feature: IP Address Host
    is_ip = 0
    try:
        ipaddress.ip_address(clean_host)
        is_ip = 1
    except ValueError:
        is_ip = 0

    # 10. Feature: Insecure HTTP Protocol Token
    https_token = 1 if url.lower().startswith("http://") else 0

    return [
        length_url,
        nb_dots,
        nb_hyphens,
        nb_slash,
        nb_subdomains,
        prefix_suffix,
        shortening_service,
        phish_hints,
        is_ip,
        https_token,
    ]


# ============================================================
# Pure Machine Learning Prediction
# ============================================================

def ensure_model_loaded() -> None:
    if model is None or scaler is None:
        raise HTTPException(
            status_code=503,
            detail="The machine learning model is currently unavailable.",
        )


def perform_prediction(raw_url: str) -> Dict:
    """
    Perform 100% Machine Learning inference:
    1. Extract numerical feature vector [f1, f2, ..., f10]
    2. Normalize feature vector using StandardScaler
    3. Run Random Forest Classifier to compute prediction and class probability
    """
    ensure_model_loaded()

    try:
        clean_url = raw_url.strip()
        features = extract_features(clean_url)

        # Scale features
        features_df = pd.DataFrame([features], columns=features_list)
        features_scaled = scaler.transform(features_df)

        # Machine Learning Inference (Random Forest)
        prediction = int(model.predict(features_scaled)[0])
        probabilities = model.predict_proba(features_scaled)[0]

        if hasattr(model, "classes_"):
            classes = list(model.classes_)
            phishing_index = classes.index(1) if 1 in classes else 1
            phishing_probability = float(probabilities[phishing_index])
        else:
            phishing_probability = float(probabilities[1])

        risk_percentage = round(phishing_probability * 100, 2)
        is_phishing = (prediction == 1)

        status = (
            "Phishing / Malicious"
            if is_phishing
            else "Legitimate / Safe"
        )

        feature_dict = dict(zip(features_list, features))
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        result = {
            "url": raw_url,
            "is_phishing": is_phishing,
            "status": status,
            "risk_score_percentage": risk_percentage,
            "features": feature_dict,
            "timestamp": timestamp,
        }

        # Save History
        history_logs.insert(
            0,
            {
                "url": raw_url,
                "status": status,
                "risk": risk_percentage,
                "timestamp": timestamp,
            },
        )
        if len(history_logs) > 50:
            history_logs.pop()

        return result

    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        print(f"Prediction error for URL '{raw_url}': {exc}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while analyzing the URL.",
        ) from exc


# ============================================================
# API Endpoints
# ============================================================

@app.get("/")
def health_check() -> Dict:
    """Server and ML model health check."""
    return {
        "status": "Online",
        "model_loaded": (model is not None and scaler is not None),
        "algorithm": "Random Forest Classifier",
        "features_count": len(features_list),
    }


@app.post("/predict")
def predict_single(payload: SingleURLRequest) -> Dict:
    """Analyze a single URL using the ML model."""
    clean_url = payload.url.strip()
    if not clean_url:
        raise HTTPException(status_code=400, detail="URL cannot be empty.")
    return perform_prediction(clean_url)


@app.post("/predict-batch")
def predict_batch(payload: BatchURLRequest) -> Dict:
    """Analyze multiple URLs at once using the ML model."""
    ensure_model_loaded()
    cleaned_urls = [u.strip() for u in payload.urls if u and u.strip()]

    if not cleaned_urls:
        raise HTTPException(status_code=400, detail="URL list cannot be empty.")

    results = []
    for url in cleaned_urls:
        try:
            results.append(perform_prediction(url))
        except HTTPException as exc:
            results.append({
                "url": url,
                "is_phishing": False,
                "status": "Analysis Failed",
                "risk_score_percentage": 0,
                "features": {},
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "error": exc.detail,
            })

    return {
        "total_analyzed": len(results),
        "results": results,
    }


@app.get("/model-info")
def get_model_info() -> Dict:
    """Return information about the trained ML model."""
    ensure_model_loaded()
    try:
        importances = model.feature_importances_
        feature_importance = {
            feature: round(float(importance) * 100, 2)
            for feature, importance in zip(features_list, importances)
        }

        return {
            "model_name": "Random Forest Classifier",
            "benchmark_test_accuracy": "82.31%",
            "benchmark_f1_score": "0.802",
            "total_features": len(features_list),
            "feature_names": features_list,
            "feature_importance_weights": feature_importance,
            "estimators_count": getattr(model, "n_estimators", 150),
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve model information.",
        ) from exc


@app.get("/history")
def get_recent_scans() -> Dict:
    """Return the latest URL scan history."""
    return {
        "count": len(history_logs),
        "recent_scans": history_logs[:20],
    }