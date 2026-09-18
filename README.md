## Backend API (FastAPI)

The backend service is a lightweight, high-performance REST API built with **FastAPI** that performs real-time URL feature extraction and serves inference predictions using serialized machine learning artifacts.

---

### Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **ASGI Server**: [Uvicorn](https://www.uvicorn.org/)
- **Data Validation**: [Pydantic v2](https://docs.pydantic.dev/)
- **Feature Engineering & ML Inference**: `scikit-learn`, `joblib`, `pandas`, `numpy`

---

### Directory Structure

```text
Phishing-URL-Detecting-Application/
├── app/
│   └── backend/
│       └── main.py          # FastAPI application & endpoint definitions
├── ml-pipeline/
│   └── model/               # Serialized model & scaler artifacts (.pkl)
├── requirements.txt
└── README.md
