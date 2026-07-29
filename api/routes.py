"""
routes.py
---------
Définition des endpoints REST de l'API.
"""

from __future__ import annotations

import io
import json
import logging

import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from src.config import (
    FEATURE_NAMES,
    LLM_ENABLED,
    METRICS_PATH,
    MODEL_COMPARISON_PATH,
    PIPELINE_PATH,
)
from src.explain import (
    explain_prediction,
    generate_ai_report,
    generate_batch_ai_summary,
    load_shap_explainer,
)
from src.inference import load_pipeline, predict_batch, predict_single
from src.schemas import (
    BatchSummary,
    ExplainedPredictionResponse,
    HealthResponse,
    MetricsResponse,
    ModelInfoResponse,
    WaterSample,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", tags=["Général"])
def read_root() -> dict:
    """Message de bienvenue et liens utiles."""
    return {
        "message": "Water Potability AI API",
        "docs": "/docs",
        "health": "/health",
    }


@router.get("/health", response_model=HealthResponse, tags=["Général"])
def health_check() -> HealthResponse:
    """Vérifie que l'API et le modèle sont opérationnels."""
    model_loaded = PIPELINE_PATH.exists()
    return HealthResponse(
        status="ok" if model_loaded else "degraded",
        model_loaded=model_loaded,
        llm_enabled=LLM_ENABLED,
    )


@router.post("/predict", response_model=ExplainedPredictionResponse, tags=["Prédiction"])
def predict(sample: WaterSample) -> ExplainedPredictionResponse:
    """Prédit la potabilité d'un échantillon d'eau et fournit une explication.

    Retourne la prédiction, la probabilité, les variables SHAP les plus
    influentes, et un rapport généré par IA (si configurée).
    """
    try:
        sample_dict = sample.model_dump()
        label, probability = predict_single(sample_dict)

        explainer = load_shap_explainer()
        sample_df = pd.DataFrame([sample_dict])[FEATURE_NAMES]
        shap_values = explain_prediction(explainer, sample_df)

        ai_report = generate_ai_report(
            features=sample_dict,
            prediction=label,
            probability=probability,
            shap_values=shap_values,
        )

        return ExplainedPredictionResponse(
            prediction=label,
            probability=probability,
            shap_values=shap_values,
            ai_report=ai_report,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        logger.exception("Erreur lors de la prédiction")
        raise HTTPException(status_code=500, detail=f"Erreur interne : {exc}") from exc


@router.post("/batch_predict", tags=["Prédiction"])
async def batch_predict(file: UploadFile = File(...)):
    """Prédit la potabilité pour un fichier CSV de plusieurs échantillons.

    Retourne un CSV enrichi (colonnes `prediction` + `probability`) en
    pièce jointe, ainsi qu'un résumé statistique dans l'en-tête `X-Summary`.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Le fichier doit être un CSV.")

    try:
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content))
        result_df = predict_batch(df)

        n_samples = len(result_df)
        n_potable = int((result_df["prediction"] == "Potable").sum())
        n_non_potable = n_samples - n_potable

        # Variables "problématiques" : celles les plus éloignées de leur médiane
        # côté échantillons non potables (heuristique simple et transparente).
        non_potable = result_df[result_df["prediction"] == "NonPotable"]
        problematic_features: list[str] = []
        if not non_potable.empty:
            deviations = (
                (non_potable[FEATURE_NAMES] - result_df[FEATURE_NAMES].median()).abs().mean()
            )
            problematic_features = deviations.sort_values(ascending=False).head(3).index.tolist()

        ai_summary = generate_batch_ai_summary(
            n_samples, n_potable, n_non_potable, problematic_features
        )

        summary = BatchSummary(
            n_samples=n_samples,
            n_potable=n_potable,
            n_non_potable=n_non_potable,
            most_problematic_features=problematic_features,
            ai_summary=ai_summary,
        )

        stream = io.StringIO()
        result_df.to_csv(stream, index=False)
        stream.seek(0)

        response = StreamingResponse(
            iter([stream.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=predictions_enrichies.csv",
                "X-Summary": json.dumps(summary.model_dump(), ensure_ascii=False),
            },
        )
        return response
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        logger.exception("Erreur lors de la prédiction batch")
        raise HTTPException(status_code=500, detail=f"Erreur interne : {exc}") from exc


@router.get("/model_info", response_model=ModelInfoResponse, tags=["Modèle"])
def model_info() -> ModelInfoResponse:
    """Informations sur le modèle actuellement chargé."""
    if not METRICS_PATH.exists():
        raise HTTPException(status_code=503, detail="Métriques introuvables. Entraînez le modèle.")

    metrics = json.loads(METRICS_PATH.read_text())
    pipeline = load_pipeline()
    model_name = type(pipeline.named_steps["classifier"]).__name__

    return ModelInfoResponse(
        model_name=metrics.get("model_name", model_name),
        features=FEATURE_NAMES,
        trained_at=metrics.get("trained_at"),
    )


@router.get("/metrics", response_model=MetricsResponse, tags=["Modèle"])
def metrics() -> MetricsResponse:
    """Métriques de performance du modèle final + comparaison des modèles."""
    if not METRICS_PATH.exists():
        raise HTTPException(status_code=503, detail="Métriques introuvables. Entraînez le modèle.")

    data = json.loads(METRICS_PATH.read_text())
    comparison = None
    if MODEL_COMPARISON_PATH.exists():
        comparison = json.loads(MODEL_COMPARISON_PATH.read_text())

    return MetricsResponse(
        model_name=data["model_name"],
        accuracy=data["accuracy"],
        kappa=data["kappa"],
        sensitivity=data["sensitivity"],
        specificity=data["specificity"],
        auc=data["auc"],
        comparison=comparison,
    )
