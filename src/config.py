"""
config.py
---------
Configuration centralisée du projet : chemins, constantes, paramètres
d'entraînement et variables d'environnement.

Toutes les autres briques du projet (préprocessing, entraînement, API,
explicabilité) importent leurs constantes depuis ce module afin d'éviter
toute valeur codée en dur dispersée dans le code.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Chargement des variables d'environnement (.env à la racine du projet)
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

# ---------------------------------------------------------------------------
# Arborescence du projet
# ---------------------------------------------------------------------------
DATA_DIR = ROOT_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
MODELS_DIR = ROOT_DIR / "models"
REPORTS_DIR = ROOT_DIR / "reports"

RAW_DATA_PATH = RAW_DATA_DIR / "water_potability.csv"

PIPELINE_PATH = MODELS_DIR / "pipeline.joblib"
# On ne sauvegarde jamais le shap.KernelExplainer lui-même (il embarque une
# fonction de prédiction non picklable). On sauvegarde uniquement
# l'échantillon de référence ("background") et on reconstruit l'explainer
# à la volée à partir du pipeline chargé (voir src/explain.py).
SHAP_BACKGROUND_PATH = MODELS_DIR / "shap_background.joblib"
METRICS_PATH = MODELS_DIR / "metrics.json"
FEATURE_NAMES_PATH = MODELS_DIR / "feature_names.json"
MODEL_COMPARISON_PATH = REPORTS_DIR / "model_comparison.json"

for directory in (RAW_DATA_DIR, PROCESSED_DATA_DIR, MODELS_DIR, REPORTS_DIR):
    directory.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Colonnes du dataset
# ---------------------------------------------------------------------------
# Noms "métier" utilisés côté API / frontend (snake_case, explicites)
FEATURE_NAMES: list[str] = [
    "ph",
    "hardness",
    "tds",
    "chlorine",
    "sulfate",
    "conductivity",
    "organic_carbon",
    "trihalomethanes",
    "turbidity",
]

TARGET_NAME = "potability"

# Colonnes du CSV brut (dataset Kaggle "Water Potability") -> renommées vers
# FEATURE_NAMES lors du chargement. Adapter ce mapping si votre CSV utilise
# déjà les noms ci-dessus.
RAW_COLUMN_MAPPING: dict[str, str] = {
    "ph": "ph",
    "Hardness": "hardness",
    "Solids": "tds",
    "chlorine": "chlorine",
    "Sulfate": "sulfate",
    "Conductivity": "conductivity",
    "Organic_carbon": "organic_carbon",
    "Trihalomethanes": "trihalomethanes",
    "Turbidity": "turbidity",
    "Potability": "potability",
}

# Variables contenant des valeurs manquantes dans le dataset d'origine
FEATURES_WITH_MISSING_VALUES: list[str] = ["ph", "tds", "sulfate", "conductivity"]

CLASS_LABELS = {0: "NonPotable", 1: "Potable"}

# ---------------------------------------------------------------------------
# Paramètres d'entraînement
# ---------------------------------------------------------------------------
RANDOM_STATE = 123
TEST_SIZE = 0.2
CV_FOLDS = 5

# ---------------------------------------------------------------------------
# Variables d'environnement
# ---------------------------------------------------------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
# Par défaut : endpoint Gemini compatible OpenAI (offre gratuite avec quotas).
# Clé gratuite : https://aistudio.google.com/apikey
OPENAI_BASE_URL = os.getenv(
    "OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/"
)
# Alias auto-mis à jour par Google vers la dernière version Flash stable
# (évite les 404 liés à la dépréciation d'un nom de modèle précis).
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gemini-flash-latest")
LLM_ENABLED = bool(OPENAI_API_KEY)

API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")