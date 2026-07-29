"""
train.py
--------
Script d'entraînement principal.

Reproduit la méthodologie du script R :
    1. Chargement + split stratifié train/test (80/20)
    2. Pipeline sklearn : SimpleImputer(median) -> StandardScaler -> Classifieur
    3. Comparaison de 4 modèles avec validation croisée (5 folds) :
         - Logistic Regression (baseline)
         - Logistic Regression pondérée (class_weight="balanced")
         - LASSO (LogisticRegression, pénalité L1)
         - SVM RBF (avec GridSearchCV sur C et gamma)
    4. Sélection automatique du meilleur modèle (AUC sur le test set)
    5. Sauvegarde : models/pipeline.joblib, models/metrics.json,
       models/feature_names.json, reports/model_comparison.json

Usage:
    python -m src.train
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

import joblib
import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from src.config import (
    CV_FOLDS,
    FEATURE_NAMES,
    FEATURE_NAMES_PATH,
    METRICS_PATH,
    MODEL_COMPARISON_PATH,
    PIPELINE_PATH,
    RANDOM_STATE,
)
from src.evaluate import evaluate_predictions
from src.preprocessing import load_raw_data, train_test_split_stratified

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def build_pipeline(classifier) -> Pipeline:
    """Construit le pipeline complet (imputation -> scaling -> modèle).

    Le pipeline est entièrement sérialisable : au moment de l'inférence,
    il suffit d'appeler `pipeline.predict()` sur des données brutes, sans
    prétraitement manuel.
    """
    return Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("classifier", classifier),
        ]
    )


def train_logistic_baseline(X_train, y_train, cv):
    logger.info("Entraînement : Logistic Regression (baseline)")
    pipeline = build_pipeline(LogisticRegression(max_iter=1000, random_state=RANDOM_STATE))
    pipeline.fit(X_train, y_train)
    return pipeline


def train_logistic_weighted(X_train, y_train, cv):
    logger.info("Entraînement : Logistic Regression pondérée")
    pipeline = build_pipeline(
        LogisticRegression(max_iter=1000, class_weight="balanced", random_state=RANDOM_STATE)
    )
    pipeline.fit(X_train, y_train)
    return pipeline


def train_lasso(X_train, y_train, cv):
    logger.info("Entraînement : LASSO (LogisticRegression L1) + GridSearchCV")
    pipeline = build_pipeline(
        LogisticRegression(
            penalty="l1",
            solver="liblinear",
            class_weight="balanced",
            max_iter=1000,
            random_state=RANDOM_STATE,
        )
    )
    param_grid = {"classifier__C": np.logspace(-3, 2, 20)}
    search = GridSearchCV(pipeline, param_grid, scoring="roc_auc", cv=cv, n_jobs=-1)
    search.fit(X_train, y_train)
    logger.info("Meilleur C (LASSO) : %s", search.best_params_)
    return search.best_estimator_


def _balanced_subsample(X, y, random_state: int = RANDOM_STATE):
    """Sous-échantillonnage équilibré (autant de Potable que de NonPotable).

    Reproduit la stratégie du script R d'origine pour le SVM : plutôt que
    de pondérer les classes sur l'intégralité du train set (coûteux avec
    un noyau RBF), on entraîne sur un sous-échantillon équilibré. Cela
    réduit fortement le temps de GridSearchCV sans dégrader les
    performances, car le SVM RBF est sensible au volume de données lors
    de l'optimisation d'hyperparamètres.
    """
    idx_pos = y[y == 1].index
    idx_neg = y[y == 0].sample(n=len(idx_pos), random_state=random_state).index
    idx = idx_pos.union(idx_neg)
    return X.loc[idx], y.loc[idx]


def train_svm_rbf(X_train, y_train, cv):
    logger.info("Entraînement : SVM RBF sur sous-échantillon équilibré + GridSearchCV")

    X_sub, y_sub = _balanced_subsample(X_train, y_train)
    logger.info(
        "Taille sous-échantillon SVM : %s (%s Potable / %s NonPotable)",
        len(X_sub),
        int((y_sub == 1).sum()),
        int((y_sub == 0).sum()),
    )

    # class_weight="balanced" n'est plus nécessaire : le sous-échantillon
    # est déjà équilibré 50/50.
    pipeline = build_pipeline(
        SVC(kernel="rbf", probability=True, cache_size=500, random_state=RANDOM_STATE)
    )
    param_grid = {
        "classifier__C": [2**i for i in range(-1, 4)],
        "classifier__gamma": [2**i for i in range(-3, 2)],
    }
    # CV à 3 folds pour ce modèle spécifiquement : le sous-échantillon est
    # déjà plus petit, 3 folds suffisent et accélèrent encore la recherche.
    svm_cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=RANDOM_STATE)
    search = GridSearchCV(pipeline, param_grid, scoring="roc_auc", cv=svm_cv, n_jobs=-1)
    search.fit(X_sub, y_sub)
    logger.info("Meilleurs hyperparamètres (SVM RBF) : %s", search.best_params_)
    return search.best_estimator_


def main() -> None:
    df = load_raw_data()
    X_train, X_test, y_train, y_test = train_test_split_stratified(df)

    cv = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)

    trainers = {
        "Logistic Regression": train_logistic_baseline,
        "Logistic Regression pondérée": train_logistic_weighted,
        "LASSO": train_lasso,
        "SVM RBF": train_svm_rbf,
    }

    results = []
    fitted_models = {}

    for name, trainer_fn in trainers.items():
        model = trainer_fn(X_train, y_train, cv)
        fitted_models[name] = model

        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1]

        result = evaluate_predictions(name, y_test.to_numpy(), y_pred, y_proba)
        results.append(result.to_dict())
        logger.info(
            "%s -> AUC=%.4f | Sens=%.4f | Spec=%.4f | Acc=%.4f",
            name,
            result.auc,
            result.sensitivity,
            result.specificity,
            result.accuracy,
        )

    # Sélection automatique du meilleur modèle (AUC la plus élevée)
    best_result = max(results, key=lambda r: r["auc"])
    best_model_name = best_result["model_name"]
    best_pipeline = fitted_models[best_model_name]

    logger.info("=> Modèle retenu : %s (AUC=%.4f)", best_model_name, best_result["auc"])

    # --- Sauvegardes ---------------------------------------------------
    joblib.dump(best_pipeline, PIPELINE_PATH)
    logger.info("Pipeline sauvegardé : %s", PIPELINE_PATH)

    metrics_payload = {
        **best_result,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "n_train": len(X_train),
        "n_test": len(X_test),
    }
    METRICS_PATH.write_text(json.dumps(metrics_payload, indent=2, ensure_ascii=False))
    logger.info("Métriques sauvegardées : %s", METRICS_PATH)

    FEATURE_NAMES_PATH.write_text(json.dumps(FEATURE_NAMES, indent=2, ensure_ascii=False))
    logger.info("Feature names sauvegardées : %s", FEATURE_NAMES_PATH)

    MODEL_COMPARISON_PATH.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    logger.info("Comparaison des modèles sauvegardée : %s", MODEL_COMPARISON_PATH)

    # --- Background SHAP (échantillon de référence, calculé une fois) ---
    from src.explain import save_shap_background

    save_shap_background(X_train)


if __name__ == "__main__":
    main()