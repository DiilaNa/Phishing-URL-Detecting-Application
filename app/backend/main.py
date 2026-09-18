from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse
import re
import time

import joblib
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

# main.py is located at:
#
# app/backend/main.py
#
# Project root:
#
# Phishing-URL-Detecting-Application/
#
# ML artifacts:
#
# ml-pipeline/model/
#
# Therefore:
# backend -> app -> project root -> ml-pipeline/model

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent.parent
MODEL_DIR = PROJECT_ROOT / "ml-pipeline" / "model"

MODEL_PATH = MODEL_DIR / "phishing_rf_model.pkl"
SCALER_PATH = MODEL_DIR / "scaler.pkl"
FEATURES_PATH = MODEL_DIR / "features_list.pkl"


# ============================================================
# FastAPI Application
# ============================================================

app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
)


# ============================================================
# CORS Configuration
# ============================================================

# Development frontend URLs.
#
# Add your deployed frontend URL here when deploying.

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
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
    """
    Load the trained ML model, scaler and feature list.

    The application will still start if the artifacts cannot
    be loaded. Prediction endpoints will return a controlled
    503 response instead of crashing the application.
    """

    global model
    global scaler
    global features_list

    try:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Model file not found: {MODEL_PATH}"
            )

        if not SCALER_PATH.exists():
            raise FileNotFoundError(
                f"Scaler file not found: {SCALER_PATH}"
            )

        if not FEATURES_PATH.exists():
            raise FileNotFoundError(
                f"Features file not found: {FEATURES_PATH}"
            )

        model = joblib.load(MODEL_PATH)
        scaler = joblib.load(SCALER_PATH)
        features_list = joblib.load(FEATURES_PATH)

        if not isinstance(features_list, list):
            raise TypeError(
                "features_list.pkl must contain a list."
            )

        print("✓ All ML artifacts loaded successfully.")
        print(f"✓ Model: {MODEL_PATH}")
        print(f"✓ Scaler: {SCALER_PATH}")
        print(f"✓ Features: {len(features_list)}")

    except Exception as exc:
        model = None
        scaler = None
        features_list = []

        print("✗ Failed to load ML artifacts.")
        print(f"✗ Error: {exc}")


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
# URL Feature Extraction
# ============================================================

def extract_features(raw_url: str) -> List[int]:
    """
    Convert a raw URL into the 10 numerical features expected
    by the trained Random Forest model.
    """

    url = raw_url.strip()

    if not url:
        raise ValueError("URL cannot be empty.")

    # Add a scheme if the user didn't provide one.
    if not url.lower().startswith(("http://", "https://")):
        url = f"http://{url}"

    parsed = urlparse(url)

    hostname = parsed.netloc

    if not hostname:
        hostname = parsed.path.split("/")[0]

    # Remove possible authentication information.
    if "@" in hostname:
        hostname = hostname.split("@")[-1]

    # Remove port.
    clean_host = hostname.split(":")[0]

    # --------------------------------------------------------
    # Feature 1: URL Length
    # --------------------------------------------------------

    length_url = len(url)

    # --------------------------------------------------------
    # Feature 2: Number of Dots
    # --------------------------------------------------------

    nb_dots = url.count(".")

    # --------------------------------------------------------
    # Feature 3: Number of Hyphens
    # --------------------------------------------------------

    nb_hyphens = url.count("-")

    # --------------------------------------------------------
    # Feature 4: Number of Slashes
    # --------------------------------------------------------

    nb_slash = url.count("/")

    # --------------------------------------------------------
    # Feature 5: Number of Subdomains
    # --------------------------------------------------------

    subdomain_parts = clean_host.split(".")

    nb_subdomains = max(
        0,
        len(subdomain_parts) - 2
    )

    # --------------------------------------------------------
    # Feature 6: Prefix / Suffix
    # --------------------------------------------------------

    prefix_suffix = (
        1
        if "-" in clean_host
        else 0
    )

    # --------------------------------------------------------
    # Feature 7: URL Shortening Service
    # --------------------------------------------------------

    shorteners_regex = (
        r"(bit\.ly|tinyurl\.com|t\.co|goo\.gl|"
        r"is\.gd|cutt\.ly|ow\.ly)"
    )

    shortening_service = (
        1
        if re.search(
            shorteners_regex,
            url.lower()
        )
        else 0
    )

    # --------------------------------------------------------
    # Feature 8: Phishing Keywords
    # --------------------------------------------------------

    phishing_keywords_regex = (
        r"(login|verify|update|banking|secure|"
        r"signin|account|wallet|confirm)"
    )

    phishing_hints = (
        1
        if re.search(
            phishing_keywords_regex,
            url.lower()
        )
        else 0
    )

    # --------------------------------------------------------
    # Feature 9: IP Address
    # --------------------------------------------------------

    ip_pattern = (
        r"^(?:(?:25[0-5]|"
        r"2[0-4][0-9]|"
        r"[01]?[0-9][0-9]?)\.){3}"
        r"(?:25[0-5]|"
        r"2[0-4][0-9]|"
        r"[01]?[0-9][0-9]?)$"
    )

    ip = (
        1
        if re.match(
            ip_pattern,
            clean_host
        )
        else 0
    )

    # --------------------------------------------------------
    # Feature 10: HTTPS Token
    # --------------------------------------------------------

    https_token = (
        1
        if "https" in hostname.lower()
        else 0
    )

    return [
        length_url,
        nb_dots,
        nb_hyphens,
        nb_slash,
        nb_subdomains,
        prefix_suffix,
        shortening_service,
        phishing_hints,
        ip,
        https_token,
    ]


# ============================================================
# Model Availability
# ============================================================

def ensure_model_loaded() -> None:
    """
    Make sure the ML model and scaler are available.

    Raises:
        HTTPException: If the model is unavailable.
    """

    if model is None or scaler is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "The machine learning model is currently "
                "unavailable. Please try again later."
            ),
        )


# ============================================================
# Prediction
# ============================================================

def perform_prediction(raw_url: str) -> Dict:
    """
    Extract URL features and perform ML prediction.
    """

    ensure_model_loaded()

    try:
        features = extract_features(raw_url)

        # Make sure the feature count matches the trained model.
        if features_list and len(features) != len(features_list):
            raise RuntimeError(
                "Feature count mismatch between the API "
                "and trained model."
            )

        features_scaled = scaler.transform([features])

        prediction = int(
            model.predict(features_scaled)[0]
        )

        probabilities = model.predict_proba(
            features_scaled
        )[0]

        # Random Forest class probabilities normally follow
        # the order in model.classes_.
        phishing_probability = 0.0

        if hasattr(model, "classes_"):
            classes = list(model.classes_)

            if 1 in classes:
                phishing_index = classes.index(1)
                phishing_probability = float(
                    probabilities[phishing_index]
                )
        else:
            # Fallback for the expected binary classification
            # setup.
            phishing_probability = float(
                probabilities[1]
            )

        risk_percentage = round(
            phishing_probability * 100,
            2
        )

        is_phishing = prediction == 1

        status = (
            "Phishing / Malicious"
            if is_phishing
            else "Legitimate / Safe"
        )

        feature_dict = dict(
            zip(
                features_list,
                features
            )
        )

        timestamp = time.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        result = {
            "url": raw_url,
            "is_phishing": is_phishing,
            "status": status,
            "risk_score_percentage": risk_percentage,
            "features": feature_dict,
            "timestamp": timestamp,
        }

        # ----------------------------------------------------
        # Save History
        # ----------------------------------------------------

        history_logs.insert(
            0,
            {
                "url": raw_url,
                "status": status,
                "risk": risk_percentage,
                "timestamp": timestamp,
            },
        )

        # Keep only the latest 50 scans.
        if len(history_logs) > 50:
            history_logs.pop()

        return result

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        print(
            f"Prediction error for URL "
            f"'{raw_url}': {exc}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "An error occurred while analyzing "
                "the URL."
            ),
        ) from exc


# ============================================================
# Health Check
# ============================================================

@app.get("/")
def health_check() -> Dict:
    """
    Server and ML model health check.
    """

    return {
        "status": "Online",
        "model_loaded": (
            model is not None
            and scaler is not None
        ),
        "algorithm": "Random Forest Classifier",
        "features_count": len(features_list),
    }


# ============================================================
# Single URL Prediction
# ============================================================

@app.post("/predict")
def predict_single(
    payload: SingleURLRequest,
) -> Dict:
    """
    Analyze a single URL.
    """

    clean_url = payload.url.strip()

    if not clean_url:
        raise HTTPException(
            status_code=400,
            detail="URL cannot be empty.",
        )

    return perform_prediction(clean_url)


# ============================================================
# Batch URL Prediction
# ============================================================

@app.post("/predict-batch")
def predict_batch(
    payload: BatchURLRequest,
) -> Dict:
    """
    Analyze multiple URLs at once.
    """

    ensure_model_loaded()

    cleaned_urls = [
        url.strip()
        for url in payload.urls
        if url and url.strip()
    ]

    if not cleaned_urls:
        raise HTTPException(
            status_code=400,
            detail="URL list cannot be empty.",
        )

    results = []

    for url in cleaned_urls:
        try:
            result = perform_prediction(url)
            results.append(result)

        except HTTPException as exc:
            # Return a controlled result for an individual
            # failed URL instead of failing the entire batch.
            results.append(
                {
                    "url": url,
                    "is_phishing": False,
                    "status": "Analysis Failed",
                    "risk_score_percentage": 0,
                    "features": {},
                    "timestamp": time.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    "error": exc.detail,
                }
            )

    return {
        "total_analyzed": len(results),
        "results": results,
    }


# ============================================================
# Model Information
# ============================================================

@app.get("/model-info")
def get_model_info() -> Dict:
    """
    Return information about the trained ML model.
    """

    ensure_model_loaded()

    try:
        importances = model.feature_importances_

        feature_importance = {
            feature: round(
                float(importance) * 100,
                2,
            )
            for feature, importance in zip(
                features_list,
                importances,
            )
        }

        return {
            "model_name": (
                "Random Forest Classifier"
            ),
            "benchmark_test_accuracy": "96.40%",
            "benchmark_f1_score": "0.963",
            "total_features": len(
                features_list
            ),
            "feature_names": features_list,
            "feature_importance_weights": (
                feature_importance
            ),
            "estimators_count": getattr(
                model,
                "n_estimators",
                100,
            ),
        }

    except Exception as exc:
        print(
            f"Model information error: {exc}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to retrieve model information."
            ),
        ) from exc


# ============================================================
# Scan History
# ============================================================

@app.get("/history")
def get_recent_scans() -> Dict:
    """
    Return the latest URL scan history.
    """

    return {
        "count": len(history_logs),
        "recent_scans": history_logs[:20],
    }