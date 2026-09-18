## Machine Learning Model Pipeline

The detection engine uses a supervised ensemble model trained to classify URLs as **Legitimate (`0`)** or **Phishing (`1`)** in real-time. The pipeline extracts lightweight lexical and structural features directly from the URL string—enabling sub-millisecond inference without requiring webpage content downloads or external network calls.

---

### Dataset Overview

- **Source Dataset**: `dataset_phishing.csv`
- **Total Records**: 11,430 URLs
- **Raw Features in Dataset**: 89 (lexical, content, domain, and external page metrics)
- **Class Balance**: 50% Legitimate / 50% Phishing (Perfect balance)
  - **Legitimate (`0`)**: 5,715 samples
  - **Phishing (`1`)**: 5,715 samples
- **Data Quality**: 0 missing values, 0 duplicate records.

---

### Feature Engineering & Selection

Rather than relying on heavy network-dependent features (such as scraping page HTML or querying third-party WHOIS/DNS servers), **10 high-impact lexical and structural URL heuristics** were engineered for fast, reliable, privacy-preserving detection:

| # | Feature Name | Type | Description & Security Rationale | Feature Importance |
| :-: | :--- | :-: | :--- | :-: |
| 1 | `length_url` | Numeric | Character length of the full URL. Phishing links often embed obfuscated paths or redirection tokens. | **36.68%** |
| 2 | `phish_hints` | Binary | Checks for sensitive credential-harvesting keywords (`login`, `verify`, `banking`, `secure`, `wallet`, etc.). | **13.99%** |
| 3 | `nb_slash` | Numeric | Total `/` characters in URL. Deep directory nesting is common in phishing kits. | **11.47%** |
| 4 | `nb_hyphens` | Numeric | Total `-` characters. Hyphens are frequently used in domain names to spoof reputable brands. | **10.01%** |
| 5 | `nb_dots` | Numeric | Total `.` characters. High dot counts signify sub-domain stuffing or deceptive domain structures. | **8.60%** |
| 6 | `ip` | Binary | `1` if raw IPv4 address is used instead of a domain name (e.g., `http://192.168.1.1/login`). | **7.73%** |
| 7 | `shortening_service` | Binary | `1` if known URL shortener domains are used (`bit.ly`, `tinyurl.com`, `t.co`, etc.) to disguise destinations. | **3.19%** |
| 8 | `https_token` | Binary | `1` if the string `https` is deceptively inserted into the hostname or path (e.g., `https-verify.net`). | **3.15%** |
| 9 | `nb_subdomains` | Numeric | Number of subdomains in hostname. Multi-level subdomains are commonly created to mimic legitimate domains. | **3.10%** |
| 10 | `prefix_suffix` | Binary | `1` if hyphen `-` exists in the hostname itself. | **2.09%** |

---

### Preprocessing & Data Split

1. **Stratified Train-Test Split (80/20)**:
   - **Training Set**: 9,144 URLs (4,572 Legitimate, 4,572 Phishing)
   - **Testing Set**: 2,286 URLs (1,143 Legitimate, 1,143 Phishing)
   - Stratification ensures exact class parity across training and evaluation splits.
2. **Feature Standardization**:
   - `StandardScaler` fits on training data only to prevent data leakage.
   - Normalizes varied feature ranges (e.g., URL length vs. binary 0/1 flags) to zero mean and unit variance.

---

### Model Comparison & Benchmarks

Four distinct classification algorithms were trained and evaluated on the identical unseen test set (2,286 samples):

| Model | Accuracy | Precision | Recall | F1-Score | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Logistic Regression** | 76.07% | 81.97% | 66.84% | 0.7364 | Baseline |
| **Decision Tree** | 78.22% | 80.40% | 74.63% | 0.7740 | Tested |
| **Gradient Boosting** | 80.49% | **85.17%** | 73.84% | 0.7910 | Tested |
| **Random Forest Classifier** | **81.10%** | 81.43% | **80.58%** | **0.8100** | **Selected (Best)** |

#### Why Random Forest was Selected:
- **Highest Overall F1-Score (0.8100)**: In cybersecurity applications, achieving a high balance between **Precision** (avoiding false alarms on safe URLs) and **Recall** (catching actual phishing threats) is paramount.
- **Robust against Overfitting**: Combining 100 decorrelated decision trees reduces variance significantly compared to individual tree models.
- **Non-Linear Interactions**: Seamlessly captures non-linear cross-interactions between lexical features (e.g., a URL containing both `login` hints and an IP address).

---

### Final Model Specifications

- **Algorithm**: `RandomForestClassifier` (Scikit-Learn)
- **Number of Estimators (`n_estimators`)**: `100`
- **Criterion**: Gini Impurity
- **Random State**: `42` (ensures reproducible splits and training)

---

### Serialized Model Artifacts

After training, the pipeline exports serialized artifacts to `ml-pipeline/model/` for consumption by the FastAPI backend:

| Artifact | File | Purpose |
| :--- | :--- | :--- |
| **Model** | `phishing_rf_model.pkl` | Trained Random Forest classifier weights and tree ensemble |
| **Scaler** | `scaler.pkl` | Fitted `StandardScaler` instance for consistent feature normalization |
| **Feature Schema** | `features_list.pkl` | Strictly ordered list of the 10 selected feature names |

---

### Inference Workflow

```mermaid
graph LR
    A[Raw URL String] --> B[Feature Extraction 10 Features]
    B --> C[StandardScaler Normalization]
    C --> D[Random Forest Model]
    D --> E[Class Prediction 0 / 1]
    D --> F[Phishing Risk Probability %]


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
