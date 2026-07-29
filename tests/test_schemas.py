"""
Tests unitaires légers sur les schémas Pydantic et l'évaluation des modèles.

Ces tests ne nécessitent pas de modèle entraîné : ils valident la logique
pure (validation, calcul de métriques) et servent de filet de sécurité
minimal pour la CI.
"""

import numpy as np

from src.evaluate import evaluate_predictions
from src.schemas import WaterSample


def test_water_sample_valid():
    sample = WaterSample(
        ph=7.2,
        hardness=180,
        tds=250,
        chlorine=8,
        sulfate=340,
        conductivity=450,
        organic_carbon=12,
        trihalomethanes=65,
        turbidity=4,
    )
    assert sample.ph == 7.2


def test_evaluate_predictions_perfect_classifier():
    y_true = np.array([0, 0, 1, 1])
    y_pred = np.array([0, 0, 1, 1])
    y_proba = np.array([0.1, 0.2, 0.9, 0.95])

    result = evaluate_predictions("test-model", y_true, y_pred, y_proba)

    assert result.accuracy == 1.0
    assert result.sensitivity == 1.0
    assert result.specificity == 1.0
    assert result.auc == 1.0
