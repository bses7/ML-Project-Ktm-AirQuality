Here is a professional, high-impact `README.md` file for your project. It is structured to be "recruiter-ready," highlighting both the technical complexity and the real-world health impact.

---

# Swaastha-Ktm: Kathmandu Air Guard

**An Automated 24-Hour Early Warning System for Kathmandu's Air Quality.**

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)](https://nextjs.org/)
[![Scikit-Learn](https://img.shields.io/badge/ML-Scikit--Learn-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white)](https://scikit-learn.org/)
[![XGBoost](https://img.shields.io/badge/ML-XGBoost-23374D?style=for-the-badge&logo=xgboost&logoColor=white)](https://xgboost.ai/)

Kathmandu is one of the most polluted cities in South Asia. Most existing systems only show current pollution levels, leaving the public reactive. **Swaastha-Ktm** changes the narrative by predicting "Hazardous" air quality levels 24 hours in advance, giving schools, hospitals, and families a critical head start to prepare.

---

## Key Features

- **24-Hour Forecast:** Predicts if PM2.5 will reach hazardous levels (>150 µg/m³) tomorrow.
- **Closed-Loop Automation:** An hourly background scheduler fetches, cleans, and merges data from OpenAQ and Visual Crossing APIs.
- **Medical-Grade Data Cleaning:** Implements a rolling median filter to remove sensor noise and humidity-induced "fake spikes."
- **Kathmandu Context Features:** Models specific urban drivers like **Brick Kiln Seasonality** and **Office Rush Hours**.
- **Public Health Optimized:** Tuned with a **0.25 probability threshold** to achieve an **85% Hazard Catch Rate (Recall).**

---

## The Machine Learning Brain

The project leverages a 3-year historical dataset (Jan 2022 - Dec 2025). After extensive hyperparameter tuning using **Optuna**, the **Voting Ensemble** emerged as the winning model.

### **Model Performance Leaderboard**

| Model                | Catch Rate (Recall) | Precision | Reliability (F1) |
| :------------------- | :------------------ | :-------- | :--------------- |
| **Voting Ensemble**  | **85%**             | **41%**   | **0.56**         |
| Single XGBoost       | 94%                 | 34%       | 0.50             |
| Single Random Forest | 25%                 | 56%       | 0.34             |

_We chose the Voting Ensemble because it provides the best "Guardian" behavior—sensitive enough to protect people while minimizing false alarms._

---

The modes are available at

```bash
backend/app/ml_models/artifacts
```

## Tech Stack

- **Languages:** Python 3.10+, TypeScript
- **Backend:** FastAPI, Uvicorn, APScheduler
- **Data Engineering:** Pandas, NumPy
- **ML Frameworks:** XGBoost 2.0.2, Scikit-Learn 1.6.1, Optuna
- **Frontend:** Next.js 14, Tailwind CSS, Lucide Icons
- **APIs:** OpenAQ (Sensor 7710), Visual Crossing (Weather Timeline)

---

## Project Structure

```text
Swaastha-Ktm/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/predict.py  # Prediction logic
│   │   ├── ml_models/artifacts/         # Trained .pkl files
│   │   ├── raw_data/                    # Automated local CSV storage
│   │   ├── services/                    # Fetcher, Cleaner, Engineer
│   │   └── main.py                      # FastAPI entry point
│   └── seed_data.py                     # Initial 48h data fetch script
├── frontend/swaasthaktm                 # Next.js Dashboard
├── Notebook # All the Notebooks used for Data Build, EDA and Training
└── aqData/
└── weatherData/
└── docker-compose.yaml
└── ReadMe.md
```

---

## Pipeline Execution & Deployment

The project uses a structured pipeline manager (`main.py`) to handle the lifecycle of the model from raw data to Docker deployment.

### 1. Initial Setup
```bash
# Clone the repository
git clone https://github.com/your-username/Swaastha-Ktm.git
cd Swaastha-Ktm

# Install training dependencies
pip install -r requirements.txt
```

### 2. Run the ML Pipeline
You can run the entire flow (Build → Clean → Preprocess → Train → Evaluate) with a single command:
```bash
python main.py
```

### 3. Granular Pipeline Control
The project supports stage-specific execution for debugging or fine-tuning:

| Command | Action |
| :--- | :--- |
| `python main.py --stage build` | Merges raw CSVs from `aqData` and `weatherData`. |
| `python main.py --stage clean` | Handles outliers and interpolates missing sensor data. |
| `python main.py --stage preprocess` | Generates temporal features and 24h lag variables. |
| `python main.py --stage train` | Trains models using parameters in `params/best_params.json`. |
| `python main.py --stage train --mode tune` | Re-runs **Optuna** optimization to find new best parameters. |
| `python main.py --stage evaluate` | Generates PR curves and CMs in `models/evaluations/`. |

### 4. Zero-Touch Deployment
When you are satisfied with the evaluation metrics, deploy the entire stack (FastAPI + Next.js) using:
```bash
python main.py --stage deploy
```
**This command automatically:**
1. Syncs the latest `.pkl` models to `backend/app/ml_models/artifacts/`.
2. Syncs the `scaler.pkl` and `features.pkl` to ensure feature parity.
3. Triggers `docker-compose up --build -d` to launch the containers.

---

## 📂 Artifact Management
- **Best Parameters:** Stored in `params/best_params.json` for reproducibility.
- **Model Artifacts:** Saved in `models/` (and synced to the app during deploy).
- **Visualizations:** Auto-generated during the `evaluate` stage in `models/evaluations/`.

---

## Installation & Setup

### 1. Backend Setup

```bash
# Navigate to backend
cd backend

# Install dependencies
pip install -r requirements.txt

# Create .env using the sample provided

# Run the Seeding Script (Creates initial history)
python -m app.seed_data

# Start the API
python -m app.main
```

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

---

## The Swaastha-Ktm Dashboard

The UI is designed with a **Medical AQI Gauge** and **Health Prescriptions**, translating complex particulate math into actionable life-saving advice.

- **Green Scale:** Safe - Perfect for the morning commute.
- **Deep Maroon Scale:** Hazardous - Wear N95 masks; keep windows closed.

---

## Future Enhancements

- **Database Integration:** Move from CSV history to **PostgreSQL** for better scalability.
- **Push Alerts:** Automated SMS/Email notifications when a 0.25 hazard probability is triggered.
- **Spatial Expansion:** Adding sensors from Patan, Bhaktapur, and Maharajgunj for valley-wide coverage.

---

## Links

- **Kaggle Training Notebook:** [https://www.kaggle.com/code/bishesh0/kathmandu-air-quality-prediction](https://www.kaggle.com/code/bishesh0/kathmandu-air-quality-prediction)

---

**Author:** Bishesh  
_Protecting Kathmandu, one prediction at a time._
