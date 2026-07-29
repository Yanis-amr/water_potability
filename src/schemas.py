"""
schemas.py
----------
Modèles Pydantic utilisés pour valider les entrées/sorties de l'API.

Centraliser les schémas ici permet de les réutiliser à la fois dans
`api/routes.py` et dans les scripts internes (inference, tests) sans
dupliquer la logique de validation.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, ConfigDict


class WaterSample(BaseModel):
    """Caractéristiques physico-chimiques d'un échantillon d'eau."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ph": 7.2,
                "hardness": 180,
                "tds": 250,
                "chlorine": 8,
                "sulfate": 340,
                "conductivity": 450,
                "organic_carbon": 12,
                "trihalomethanes": 65,
                "turbidity": 4,
            }
        }
    )

    ph: float = Field(..., ge=0, le=14, description="pH de l'eau (0-14)")
    hardness: float = Field(..., ge=0, description="Dureté de l'eau (mg/L)")
    tds: float = Field(..., ge=0, description="Solides dissous totaux (ppm)")
    chlorine: float = Field(..., ge=0, description="chlorine (ppm)")
    sulfate: float = Field(..., ge=0, description="Sulfates (mg/L)")
    conductivity: float = Field(..., ge=0, description="Conductivité (µS/cm)")
    organic_carbon: float = Field(..., ge=0, description="Carbone organique (ppm)")
    trihalomethanes: float = Field(..., ge=0, description="Trihalométhanes (µg/L)")
    turbidity: float = Field(..., ge=0, description="Turbidité (NTU)")


class ShapContribution(BaseModel):
    feature: str
    impact: float


class PredictionResponse(BaseModel):
    prediction: Literal["Potable", "NonPotable"]
    probability: float = Field(..., description="Probabilité d'être potable (0-1)")


class ExplainedPredictionResponse(PredictionResponse):
    shap_values: list[ShapContribution]
    ai_report: str | None = None


class BatchSummary(BaseModel):
    n_samples: int
    n_potable: int
    n_non_potable: int
    most_problematic_features: list[str]
    ai_summary: str | None = None


class ModelInfoResponse(BaseModel):
    model_name: str
    features: list[str]
    trained_at: str | None = None
    version: str = "1.0.0"


class MetricsResponse(BaseModel):
    model_name: str
    accuracy: float
    kappa: float
    sensitivity: float
    specificity: float
    auc: float
    comparison: list[dict] | None = None


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    model_loaded: bool
    llm_enabled: bool
