"""
inference.py
------------
Chargement du pipeline sérialisé et prédiction.

Le pipeline sauvegardé par `train.py` contient déjà l'imputation et la
standardisation : il ne faut donc JAMAIS re-prétraiter les données ici.
On se contente d'appeler `pipeline.predict` / `pipeline.predict_proba`
sur les données brutes.
"""

from __future__ import annotations

import functools
import logging

import joblib
import pandas as pd

from src.config import CLASS_LABELS, FEATURE_NAMES, PIPELINE_PATH

logger = logging.getLogger(__name__)


@functools.lru_cache(maxsize=1)
def load_pipeline():
    """Charge le pipeline entraîné (mis en cache en mémoire)."""
    if not PIPELINE_PATH.exists():
        raise FileNotFoundError(
            f"Pipeline introuvable : {PIPELINE_PATH}. "
            "Lancez d'abord l'entraînement avec `python -m src.train`."
        )
    logger.info("Chargement du pipeline : %s", PIPELINE_PATH)
    return joblib.load(PIPELINE_PATH)


def _to_dataframe(sample: dict) -> pd.DataFrame:
    """Convertit un dict de features en DataFrame ordonné selon FEATURE_NAMES."""
    return pd.DataFrame([{name: sample[name] for name in FEATURE_NAMES}])


def predict_single(sample: dict) -> tuple[str, float]:
    """Prédit la potabilité d'un unique échantillon.

    Args:
        sample: dict contenant les 9 variables physico-chimiques.

    Returns:
        Tuple (label prédit, probabilité d'être potable).
    """
    pipeline = load_pipeline()
    df = _to_dataframe(sample)

    proba_potable = float(pipeline.predict_proba(df)[0, 1])
    label = CLASS_LABELS[int(proba_potable >= 0.5)]
    return label, proba_potable


def predict_batch(df: pd.DataFrame) -> pd.DataFrame:
    """Prédit la potabilité pour un DataFrame de plusieurs échantillons.

    Ajoute deux colonnes au DataFrame d'entrée : `prediction` et `probability`.
    """
    pipeline = load_pipeline()
    missing = set(FEATURE_NAMES) - set(df.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes dans le CSV : {missing}")

    X = df[FEATURE_NAMES]
    probabilities = pipeline.predict_proba(X)[:, 1]
    labels = [CLASS_LABELS[int(p >= 0.5)] for p in probabilities]

    result = df.copy()
    result["prediction"] = labels
    result["probability"] = probabilities
    return result
