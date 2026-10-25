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
MODEL_DIR = BASE_DIR / "model"

MODEL_PATH = MODEL_DIR / "phishing_rf_model.pkl"
SCALER_PATH = MODEL_DIR / "scaler.pkl"
FEATURES_PATH = MODEL_DIR / "features_list.pkl"


# ============================================================
# Constants for Feature Extraction
# ============================================================

KNOWN_SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "is.gd",
    "cutt.ly", "ow.ly", "rebrand.ly", "t.ly", "qr.ae",
}

KNOWN_BRANDS = {
    "facebook", "google", "paypal", "amazon", "microsoft", "apple", "instagram",
    "netflix", "whatsapp", "telegram", "linkedin", "github", "dropbox", "adobe", "outlook",
}

SUSPICIOUS_TLDS = {"xyz", "top", "gq", "tk", "ml", "cf", "ga", "work", "click", "country"}

HOMOGLYPH_TRANSLATION = str.maketrans({
    "0": "o", "1": "l", "3": "e", "4": "a", "5": "s", "7": "t", "8": "b", "9": "g"
})

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

def extract_features(raw_url: str) -> List[float]:
    """Extract feature vector in the same order as the trained model."""
    feature_dict = extract_feature_dict(raw_url)
    return [float(feature_dict[name]) for name in features_list]


def normalize_url(raw_url: str) -> str:
    url = raw_url.strip()
    if not url:
        raise ValueError("URL cannot be empty.")
    if not url.lower().startswith(("http://", "https://")):
        return "https://" + url
    return url


def _brand_typo_flag(clean_host: str) -> int:
    tokens = [t for t in re.split(r"[^a-z0-9]", clean_host.lower()) if t]
    for token in tokens:
        if not any(ch.isdigit() for ch in token):
            continue
        normalized = token.translate(HOMOGLYPH_TRANSLATION)
        if normalized in KNOWN_BRANDS and token != normalized:
            return 1
    return 0


def _exact_brand_domain(clean_host: str) -> int:
    parts = [p for p in clean_host.split(".") if p]
    base = parts[-2] if len(parts) >= 2 else (parts[0] if parts else "")
    return 1 if base in KNOWN_BRANDS else 0


def extract_feature_dict(raw_url: str) -> Dict[str, float]:
    normalized_url = normalize_url(raw_url)
    parsed = urlparse(normalized_url)

    hostname = parsed.netloc or parsed.path.split("/")[0]
    if "@" in hostname:
        hostname = hostname.split("@")[-1]
    clean_host = hostname.split(":")[0].lower()

    normalized_lower = normalized_url.lower()
    path_lower = parsed.path.lower() if parsed.path else ""

    host_parts = [p for p in clean_host.split(".") if p]
    nb_subdomains = max(1, len(host_parts) - 1)

    try:
        ipaddress.ip_address(clean_host)
        is_ip = 1
    except ValueError:
        is_ip = 0

    try:
        parsed_port = parsed.port
    except ValueError:
        parsed_port = None

    url_len = max(1, len(normalized_url))
    host_len = max(1, len(clean_host))
    tld = host_parts[-1] if host_parts else ""

    return {
        "length_url": float(len(normalized_url)),
        "length_hostname": float(len(clean_host)),
        "ip": float(is_ip),
        "nb_dots": float(normalized_url.count(".")),
        "nb_hyphens": float(normalized_url.count("-")),
        "nb_at": float(normalized_url.count("@")),
        "nb_qm": float(normalized_url.count("?")),
        "nb_and": float(normalized_url.count("&")),
        "nb_eq": float(normalized_url.count("=")),
        "nb_underscore": float(normalized_url.count("_")),
        "nb_percent": float(normalized_url.count("%")),
        "nb_slash": float(normalized_url.count("/")),
        "nb_dslash": float(normalized_url.count("//")),
        "https_token": float(1 if normalized_lower.startswith("http://") else 0),
        "ratio_digits_url": float(sum(ch.isdigit() for ch in normalized_url) / url_len),
        "ratio_digits_host": float(sum(ch.isdigit() for ch in clean_host) / host_len),
        "nb_subdomains": float(nb_subdomains),
        "prefix_suffix": float(1 if "-" in clean_host else 0),
        "shortening_service": float(
            1 if (clean_host in KNOWN_SHORTENERS or any(clean_host.endswith("." + s) for s in KNOWN_SHORTENERS)) else 0
        ),
        "phish_hints": float(1 if re.search(PHISH_KEYWORDS_REGEX, normalized_lower) else 0),
        "punycode": float(1 if "xn--" in clean_host else 0),
        "port": float(1 if parsed_port else 0),
        "path_extension": float(1 if re.search(r"\.[a-z0-9]{1,5}$", path_lower) else 0),
        "brand_typo_flag": float(_brand_typo_flag(clean_host)),
        "exact_brand_domain": float(_exact_brand_domain(clean_host)),
        "suspecious_tld": float(1 if tld in SUSPICIOUS_TLDS else 0),
    }


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
        feature_dict = extract_feature_dict(clean_url)

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

        filtered_feature_dict = {
            name: float(feature_dict[name])
            for name in features_list
            if name in feature_dict
        }
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        result = {
            "url": raw_url,
            "is_phishing": is_phishing,
            "status": status,
            "risk_score_percentage": risk_percentage,
            "features": filtered_feature_dict,
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