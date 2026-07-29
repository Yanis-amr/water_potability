"""
explain.py
----------
Couche d'explicabilité du projet :
    1. SHAP : calcule la contribution de chaque variable à UNE prédiction.
    2. IA générative (LLM) : transforme la prédiction + les SHAP values en
       un rapport pédagogique en langage naturel.

Le LLM ne remplace JAMAIS le modèle de Machine Learning : il ne fait que
mettre en mots des résultats déjà calculés par le pipeline scikit-learn et
SHAP. Le prompt lui interdit explicitement d'inventer des données
scientifiques et lui impose de rappeler qu'il s'agit d'une aide à la
décision, non d'un diagnostic certifié.
"""

from __future__ import annotations

import logging

import functools

import joblib
import numpy as np
import pandas as pd
import shap
from openai import OpenAI

from src.config import (
    FEATURE_NAMES,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
    SHAP_BACKGROUND_PATH,
)

logger = logging.getLogger(__name__)

_client: OpenAI | None = None


def _get_client() -> OpenAI | None:
    """Instancie le client OpenAI de façon paresseuse (au premier appel qui
    en a réellement besoin), plutôt qu'au chargement du module.

    Important : `import src.explain` est utilisé par `train.py` uniquement
    pour `save_shap_background`, qui n'a aucun rapport avec le LLM. Si le
    client était créé au niveau module, une erreur de configuration ou de
    dépendance côté client OpenAI (ex. incompatibilité de version `httpx`)
    ferait planter l'entraînement du modèle. En le créant seulement ici,
    ces deux responsabilités restent indépendantes.
    """
    global _client
    if _client is None and OPENAI_API_KEY:
        _client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
    return _client


# ---------------------------------------------------------------------------
# SHAP
# ---------------------------------------------------------------------------
class _PipelineProbaPredictor:
    """Wrapper appelable autour de `pipeline.predict_proba`, utilisé comme
    fonction de prédiction pour `shap.KernelExplainer`.

    Contrairement à une fonction imbriquée (closure), une classe définie au
    niveau du module est picklable. Ici, on ne sérialise même pas cet objet :
    il est reconstruit à chaque démarrage de l'API à partir du pipeline déjà
    chargé. Cela évite complètement l'erreur `PicklingError` rencontrée avec
    une closure locale.
    """

    def __init__(self, pipeline):
        self.pipeline = pipeline

    def __call__(self, data: np.ndarray) -> np.ndarray:
        df = pd.DataFrame(data, columns=FEATURE_NAMES)
        return self.pipeline.predict_proba(df)[:, 1]


def save_shap_background(X_background: pd.DataFrame) -> None:
    """Sauvegarde un échantillon de référence ("background") pour SHAP.

    On ne sauvegarde JAMAIS le `KernelExplainer` lui-même : il embarque une
    fonction de prédiction qui n'est picklable que si le pipeline est
    disponible au même moment. On sauvegarde donc uniquement les données
    (un DataFrame, parfaitement picklable), et l'explainer est reconstruit
    à la volée par `load_shap_explainer()`.
    """
    background = shap.sample(X_background, min(100, len(X_background)), random_state=0)
    joblib.dump(background, SHAP_BACKGROUND_PATH)
    logger.info("Background SHAP sauvegardé : %s", SHAP_BACKGROUND_PATH)


@functools.lru_cache(maxsize=1)
def load_shap_explainer():
    """Reconstruit (et met en cache) le `KernelExplainer` au premier appel.

    Combine le pipeline entraîné (chargé via `src.inference.load_pipeline`,
    lui-même mis en cache) et le background sauvegardé par
    `save_shap_background`. Le résultat n'est jamais écrit sur disque.
    """
    from src.inference import load_pipeline  # import local pour éviter un cycle

    pipeline = load_pipeline()
    background = joblib.load(SHAP_BACKGROUND_PATH)
    predict_fn = _PipelineProbaPredictor(pipeline)
    return shap.KernelExplainer(predict_fn, background)


def explain_prediction(explainer, sample: pd.DataFrame, top_n: int = 5) -> list[dict]:
    """Retourne les `top_n` variables les plus influentes pour une prédiction.

    Args:
        explainer: `shap.Explainer` chargé.
        sample: DataFrame à une ligne (les features brutes de l'échantillon).
        top_n: nombre de variables à retourner, triées par |impact| décroissant.

    Returns:
        Liste de dicts `{"feature": ..., "impact": ...}`.
    """
    shap_values = explainer.shap_values(sample, nsamples=100, silent=True)
    values = np.array(shap_values).flatten()

    contributions = sorted(
        (
            {"feature": feature, "impact": float(value)}
            for feature, value in zip(FEATURE_NAMES, values)
        ),
        key=lambda item: abs(item["impact"]),
        reverse=True,
    )
    return contributions[:top_n]


# ---------------------------------------------------------------------------
# IA générative
# ---------------------------------------------------------------------------
_SYSTEM_PROMPT = """Tu es un assistant scientifique spécialisé dans l'explication \
de modèles de Machine Learning appliqués à la qualité de l'eau.

Règles strictes :
- Tu ne fais QUE commenter les résultats numériques fournis (prédiction, \
probabilité, valeurs SHAP). Tu n'inventes jamais de nouvelles données, \
seuils réglementaires ou faits scientifiques non fournis.
- Tu rappelles systématiquement que ce rapport est une aide à la décision \
et ne remplace pas une analyse en laboratoire certifiée.
- Ton style est pédagogique, clair, concis, destiné à un public non expert.
"""

_USER_PROMPT_TEMPLATE = """Voici les données d'un échantillon d'eau et le résultat \
du modèle de classification :

Variables mesurées :
{features}

Résultat du modèle :
- Prédiction : {prediction}
- Probabilité d'être potable : {probability:.1%}

Variables les plus influentes (valeurs SHAP, positif = pousse vers "Potable", \
négatif = pousse vers "NonPotable") :
{shap_values}

Rédige un rapport structuré avec les sections suivantes :
1. Résumé
2. Interprétation
3. Facteurs ayant influencé la décision
4. Niveau de confiance
5. Recommandations
6. Limites du modèle
"""


def generate_ai_report(
    features: dict,
    prediction: str,
    probability: float,
    shap_values: list[dict],
) -> str:
    """Génère un rapport en langage naturel expliquant une prédiction.

    Retourne un message explicite si aucune clé API n'est configurée, afin
    que l'application reste fonctionnelle sans dépendance obligatoire à un
    fournisseur de LLM.
    """
    client = _get_client()
    if client is None:
        return (
            "Rapport IA indisponible : aucune clé OPENAI_API_KEY n'est configurée. "
            "Consultez le README pour activer cette fonctionnalité."
        )

    features_str = "\n".join(f"- {k} : {v}" for k, v in features.items())
    shap_str = "\n".join(
        f"- {item['feature']} : {item['impact']:+.3f}" for item in shap_values
    )

    user_prompt = _USER_PROMPT_TEMPLATE.format(
        features=features_str,
        prediction=prediction,
        probability=probability,
        shap_values=shap_str,
    )

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content or ""
    except Exception as exc:  # pragma: no cover - dépend d'un service externe
        logger.exception("Erreur lors de l'appel au LLM")
        return f"Le rapport IA n'a pas pu être généré (erreur : {exc})."


def generate_batch_ai_summary(
    n_samples: int,
    n_potable: int,
    n_non_potable: int,
    problematic_features: list[str],
) -> str:
    """Génère un résumé IA pour un lot de prédictions (mode batch)."""
    client = _get_client()
    if client is None:
        return (
            "Résumé IA indisponible : aucune clé OPENAI_API_KEY n'est configurée."
        )

    user_prompt = f"""Voici les résultats d'une analyse par lot de {n_samples} \
échantillons d'eau :
- Eaux potables : {n_potable}
- Eaux non potables : {n_non_potable}
- Variables les plus souvent problématiques : {", ".join(problematic_features)}

Rédige un court résumé (5-8 phrases) à destination d'un responsable qualité \
de l'eau : tendance générale, variables à surveiller en priorité, et \
recommandation d'actions. Rappelle qu'il s'agit d'une aide à la décision."""

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content or ""
    except Exception as exc:  # pragma: no cover
        logger.exception("Erreur lors de l'appel au LLM (batch)")
        return f"Le résumé IA n'a pas pu être généré (erreur : {exc})."