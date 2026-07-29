"""
preprocessing.py
-----------------
Chargement et préparation des données.

Ce module reproduit fidèlement les choix méthodologiques du script R
d'origine :
    - renommage des colonnes vers des noms explicites (snake_case)
    - imputation par la médiane des variables `ph`, `tds`, `sulfate`,
      `conductivity`
    - split stratifié train / test (80/20)

L'imputation et la standardisation "finales" utilisées par le modèle
sont en réalité encapsulées dans le `sklearn.Pipeline` (voir train.py) afin
qu'aucune fuite d'information (data leakage) ne soit possible entre train
et test, et pour que le pipeline sérialisé soit autonome.
"""

from __future__ import annotations

import logging

import pandas as pd
from sklearn.model_selection import train_test_split

from src.config import (
    FEATURE_NAMES,
    RANDOM_STATE,
    RAW_COLUMN_MAPPING,
    RAW_DATA_PATH,
    TARGET_NAME,
    TEST_SIZE,
)

logger = logging.getLogger(__name__)


def load_raw_data(path=RAW_DATA_PATH) -> pd.DataFrame:
    """Charge le CSV brut et renomme les colonnes vers des noms explicites.

    Args:
        path: chemin vers le fichier CSV brut.

    Returns:
        DataFrame avec les colonnes renommées (voir `RAW_COLUMN_MAPPING`).

    Raises:
        FileNotFoundError: si le fichier n'existe pas.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"Fichier de données introuvable : {path}. "
            "Placez le dataset 'water_potability.csv' dans data/raw/."
        )

    df = pd.read_csv(path)

    # Renomme uniquement les colonnes connues, ignore les autres
    rename_map = {k: v for k, v in RAW_COLUMN_MAPPING.items() if k in df.columns}
    df = df.rename(columns=rename_map)

    missing_cols = set(FEATURE_NAMES + [TARGET_NAME]) - set(df.columns)
    if missing_cols:
        raise ValueError(
            f"Colonnes manquantes dans le dataset après renommage : {missing_cols}"
        )

    logger.info("Données chargées : %s lignes, %s colonnes", *df.shape)
    return df[FEATURE_NAMES + [TARGET_NAME]]


def get_missing_values_report(df: pd.DataFrame) -> pd.Series:
    """Retourne le nombre de valeurs manquantes par colonne."""
    return df.isna().sum()


def train_test_split_stratified(
    df: pd.DataFrame,
    test_size: float = TEST_SIZE,
    random_state: int = RANDOM_STATE,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Split stratifié train/test sur la variable cible `potability`.

    L'imputation et la standardisation ne sont volontairement PAS
    effectuées ici : elles sont intégrées au `Pipeline` scikit-learn afin
    d'être apprises uniquement sur le train et appliquées identiquement
    au moment de l'inférence.
    """
    X = df[FEATURE_NAMES]
    y = df[TARGET_NAME].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        stratify=y,
        random_state=random_state,
    )

    logger.info(
        "Split train/test : %s / %s échantillons (stratifié sur potability)",
        len(X_train),
        len(X_test),
    )
    return X_train, X_test, y_train, y_test


def class_balance(y: pd.Series) -> pd.Series:
    """Proportions des classes (utile pour vérifier le déséquilibre 92/8)."""
    return y.value_counts(normalize=True)
