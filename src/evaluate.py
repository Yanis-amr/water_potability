"""
evaluate.py
-----------
Fonctions d'évaluation des modèles : accuracy, kappa, sensibilité,
spécificité, AUC. Reproduit les métriques calculées par `caret::confusionMatrix`
et `pROC::roc` dans le script R d'origine.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    cohen_kappa_score,
    confusion_matrix,
    roc_auc_score,
)


@dataclass
class EvaluationResult:
    model_name: str
    accuracy: float
    kappa: float
    sensitivity: float  # rappel de la classe positive (Potable)
    specificity: float  # rappel de la classe négative (NonPotable)
    auc: float

    def to_dict(self) -> dict:
        return asdict(self)


def evaluate_predictions(
    model_name: str,
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_proba: np.ndarray,
) -> EvaluationResult:
    """Calcule l'ensemble des métriques pour un jeu de prédictions.

    Args:
        model_name: nom du modèle évalué (pour reporting).
        y_true: labels réels (0/1), 1 = Potable.
        y_pred: labels prédits (0/1).
        y_proba: probabilité prédite de la classe positive (Potable).
    """
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()

    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0

    return EvaluationResult(
        model_name=model_name,
        accuracy=float(accuracy_score(y_true, y_pred)),
        kappa=float(cohen_kappa_score(y_true, y_pred)),
        sensitivity=float(sensitivity),
        specificity=float(specificity),
        auc=float(roc_auc_score(y_true, y_proba)),
    )


def balanced_accuracy(sensitivity: float, specificity: float) -> float:
    return (sensitivity + specificity) / 2
