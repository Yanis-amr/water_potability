"""
main.py
-------
Point d'entrée de l'API FastAPI.

Lancement :
    uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from src.config import CORS_ORIGINS, LOG_LEVEL

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="Water Potability AI API",
    description=(
        "API de prédiction de la potabilité de l'eau à partir de "
        "caractéristiques physico-chimiques, avec explicabilité SHAP "
        "et rapports générés par IA."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "X-Summary"],
    expose_headers=["X-Summary"],
)

app.include_router(router)
