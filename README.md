# Water Potability AI

Application complète de prédiction de la potabilité de l'eau à partir de 9
caractéristiques physico-chimiques, avec pipeline Machine Learning
(scikit-learn), API REST (FastAPI), interface web (React), explicabilité
(SHAP) et une couche d'IA générative qui traduit les résultats du modèle en
rapport pédagogique.

Ce projet est une reconstruction professionnelle d'une analyse initialement
réalisée en R (comparaison de modèles : régression logistique, régression
logistique pondérée, GLMNET LASSO, SVM RBF). La méthodologie statistique est
conservée ; l'implémentation est entièrement réécrite en Python selon les
standards d'un projet MLOps industrialisable.

---

## Sommaire

- [Architecture](#architecture)
- [Stack technique](#stack-technique)
- [Installation](#installation)
- [Entraînement du modèle](#entraînement-du-modèle)
- [Lancement de l'API](#lancement-de-lapi)
- [Lancement du frontend](#lancement-du-frontend)
- [Docker](#docker)
- [Endpoints de l'API](#endpoints-de-lapi)
- [Explicabilité (SHAP)](#explicabilité-shap)
- [Couche IA générative](#couche-ia-générative)
- [Méthodologie Machine Learning](#méthodologie-machine-learning)
- [Qualité de code](#qualité-de-code)
- [Captures attendues](#captures-attendues)

---

## Architecture

```
water-potability-ai/
│
├── data/
│   ├── raw/                 # water_potability.csv (non versionné)
│   └── processed/
│
├── notebooks/
│   └── exploration.ipynb    # EDA minimale (le reste est dans le pipeline)
│
├── src/
│   ├── config.py             # chemins, constantes, variables d'env
│   ├── preprocessing.py      # chargement des données, split stratifié
│   ├── train.py               # entraînement, comparaison, sélection du modèle
│   ├── evaluate.py            # métriques (accuracy, kappa, sensibilité...)
│   ├── inference.py           # chargement du pipeline + prédiction
│   ├── explain.py             # SHAP + génération de rapports IA
│   └── schemas.py             # modèles Pydantic partagés
│
├── models/
│   ├── pipeline.joblib         # pipeline scikit-learn complet (généré)
│   ├── shap_explainer.joblib   # explainer SHAP (généré)
│   ├── metrics.json            # métriques du modèle final (généré)
│   └── feature_names.json      # ordre des variables (généré)
│
├── api/
│   ├── main.py                # point d'entrée FastAPI
│   └── routes.py              # endpoints REST
│
├── frontend/                  # application React (Vite + Tailwind)
│   └── src/
│       ├── components/        # PredictForm, ResultPanel, ShapChart, ...
│       └── lib/                # client API (axios), métadonnées features
│
├── reports/
│   └── model_comparison.json  # comparaison des 4 modèles (généré)
│
├── tests/                     # tests unitaires (pytest)
├── requirements.txt
├── pyproject.toml             # config black / ruff / pytest
├── Dockerfile                 # image API
├── docker-compose.yml         # orchestration API + frontend
└── .env.example
```

### Principe clé : un pipeline auto-suffisant

Le pipeline scikit-learn sauvegardé (`models/pipeline.joblib`) embarque
**l'imputation, la standardisation et le modèle**. À l'inférence, on ne
prétraite jamais manuellement les données : on appelle directement
`pipeline.predict_proba(donnees_brutes)`. Cela élimine tout risque de
divergence entre le prétraitement d'entraînement et celui de production.

---

## Stack technique

| Domaine            | Technologies |
|---------------------|--------------|
| Machine Learning    | scikit-learn, pandas, numpy, joblib |
| Explicabilité       | SHAP |
| API                 | FastAPI, Pydantic, Uvicorn |
| IA générative       | OpenAI SDK (compatible tout endpoint OpenAI-like) |
| Frontend            | React (Vite), TailwindCSS, Axios |
| Qualité             | Black, Ruff, Pytest |
| Industrialisation   | Docker, docker-compose |

---

## Installation

### Prérequis

- Python 3.12+
- Node.js 20+
- Le dataset `water_potability.csv` (dataset Kaggle "Water Potability" ou
  équivalent) placé dans `data/raw/water_potability.csv`

### Backend

```bash
python -m venv .venv
source .venv/bin/activate  # Windows : .venv\Scripts\activate

pip install -r requirements.txt
copy .env.example .env        # renseigner OPENAI_API_KEY si souhaité
```

### Frontend

```bash
cd frontend
npm install
copy .env.example .env
```

---

## Entraînement du modèle

```bash
python -m src.train
```

Ce script :

1. Charge `data/raw/water_potability.csv` et effectue un split stratifié
   80/20.
2. Entraîne 4 modèles dans un `Pipeline` scikit-learn
   (`SimpleImputer(median)` → `StandardScaler` → classifieur) :
   - Logistic Regression (baseline)
   - Logistic Regression pondérée (`class_weight="balanced"`)
   - LASSO (`LogisticRegression` pénalité L1, `GridSearchCV`)
   - SVM RBF (`GridSearchCV` sur `C` et `gamma`)
3. Évalue chaque modèle sur le test set (accuracy, kappa, sensibilité,
   spécificité, AUC).
4. Sélectionne automatiquement le meilleur modèle (AUC la plus élevée —
   le SVM RBF, conformément à l'analyse R d'origine).
5. Sauvegarde `models/pipeline.joblib`, `models/metrics.json`,
   `models/feature_names.json`, `reports/model_comparison.json`, ainsi que
   l'explainer SHAP (`models/shap_explainer.joblib`).

---

## Lancement de l'API

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

La documentation interactive Swagger est disponible sur
`http://localhost:8000/docs`.

---

## Lancement du frontend

```bash
cd frontend
npm run dev
```

L'application est disponible sur `http://localhost:5173`. Le serveur de
développement Vite proxy automatiquement les appels `/api/*` vers
`http://localhost:8000`.

---

## Docker

Pour lancer l'ensemble de la stack (API + frontend) :

```bash
docker compose up --build
```

- API : `http://localhost:8000`
- Frontend : `http://localhost:5173`

> Le modèle doit être entraîné (`python -m src.train`) avant de construire
> l'image API, afin que `models/pipeline.joblib` existe.

---

## Endpoints de l'API

| Méthode | Route             | Description |
|---------|--------------------|--------------|
| GET     | `/`                | Message de bienvenue |
| GET     | `/health`          | État de l'API et du modèle |
| POST    | `/predict`         | Prédiction + SHAP + rapport IA pour un échantillon |
| POST    | `/batch_predict`   | Prédiction pour un fichier CSV (retourne un CSV enrichi) |
| GET     | `/model_info`      | Métadonnées du modèle chargé |
| GET     | `/metrics`         | Métriques de performance + comparaison des modèles |

### Exemple `POST /predict`

Requête :

```json
{
  "ph": 7.2,
  "hardness": 180,
  "tds": 250,
  "chloramines": 8,
  "sulfate": 340,
  "conductivity": 450,
  "organic_carbon": 12,
  "trihalomethanes": 65,
  "turbidity": 4
}
```

Réponse :

```json
{
  "prediction": "Potable",
  "probability": 0.94,
  "shap_values": [
    {"feature": "conductivity", "impact": 0.42},
    {"feature": "ph", "impact": -0.18}
  ],
  "ai_report": "1. Résumé\n..."
}
```

---

## Explicabilité (SHAP)

`src/explain.py` construit un `shap.KernelExplainer` autour du pipeline
complet (donc y compris l'imputation et le scaling), à partir d'un
échantillon de 100 observations du train set comme "background". Pour
chaque prédiction, les 5 variables ayant la plus forte contribution
(positive ou négative) sont retournées et affichées côté frontend sous
forme de barres de signal.

---

## Couche IA générative

Le LLM (configurable via `OPENAI_API_KEY`, `OPENAI_BASE_URL`,
`OPENAI_MODEL` dans `.env`) **ne remplace jamais le modèle de ML**.

Par défaut, le projet pointe vers l'**endpoint Gemini compatible OpenAI**
(gratuit, avec quotas par minute/jour) plutôt que l'API OpenAI payante :
récupérer une clé gratuite sur https://aistudio.google.com/apikey, la
renseigner dans `OPENAI_API_KEY`, et laisser `OPENAI_BASE_URL` /
`OPENAI_MODEL` tels quels dans `.env.example`. Aucune modification de code
n'est nécessaire — le client `openai` du SDK accepte n'importe quel
endpoint compatible. Pour repasser sur l'API OpenAI officielle, il suffit
de changer ces deux variables (voir les valeurs commentées dans
`.env.example`).

Le LLM reçoit en entrée :

- les 9 variables de l'échantillon,
- la prédiction et la probabilité du pipeline scikit-learn,
- les valeurs SHAP calculées,

et génère un rapport structuré (résumé, interprétation, facteurs
d'influence, niveau de confiance, recommandations, limites du modèle). Le
prompt système interdit explicitement d'inventer des données scientifiques
et impose de rappeler qu'il s'agit d'une aide à la décision.

Si `OPENAI_API_KEY` n'est pas renseignée, l'application reste pleinement
fonctionnelle : un message explicite remplace le rapport IA, sans bloquer
la prédiction ni l'explicabilité SHAP.

---

## Méthodologie Machine Learning

Reprise fidèle des choix méthodologiques du script R d'origine :

- **Imputation** : médiane pour `ph`, `tds`, `sulfate`, `conductivity`
  (seules variables comportant des valeurs manquantes).
- **Standardisation** : `StandardScaler` sur l'ensemble des variables.
- **Split** : stratifié 80/20 sur la variable cible.
- **Validation croisée** : 5 folds stratifiés.
- **Déséquilibre des classes** : géré via `class_weight="balanced"`
  (plutôt que le sous-échantillonnage manuel utilisé côté SVM dans le
  script R), afin de conserver l'intégralité des données d'entraînement
  tout en corrigeant le biais de classe majoritaire.
- **Recherche d'hyperparamètres** : `GridSearchCV` pour LASSO (`C`) et
  SVM RBF (`C`, `gamma`), optimisés sur l'AUC.
- **Sélection finale** : le modèle avec l'AUC la plus élevée sur le test
  set est retenu — le SVM RBF, conformément à la conclusion du benchmark R.

Les modèles Random Forest et k-NN, présents en annexe dans le script R
d'origine, ne sont pas repris dans l'application finale (conformément au
cahier des charges) ; le notebook `exploration.ipynb` se concentre sur
l'EDA strictement nécessaire à la compréhension du problème.

---

## Qualité de code

```bash
black src api tests
ruff check src api tests
pytest
```

La configuration Black/Ruff/Pytest est centralisée dans `pyproject.toml`.

---

## Déploiement gratuit (Render)

Voir le guide détaillé fourni séparément pour la marche à suivre complète.
Résumé :

1. Les artefacts du modèle entraîné (`models/*.joblib`, `models/*.json`)
   sont commités dans le repo Git — l'hébergement gratuit ne ré-entraîne
   pas le modèle dans le cloud.
2. **Backend** : Render > New > Web Service > Docker, branché sur ce repo.
   Variables d'environnement à renseigner : `OPENAI_API_KEY`,
   `OPENAI_BASE_URL`, `OPENAI_MODEL`, `CORS_ORIGINS`.
3. **Frontend** : Render > New > Static Site, build command
   `cd frontend && npm install && npm run build`, publish directory
   `frontend/dist`, variable d'environnement `VITE_API_URL` pointée vers
   l'URL du backend.
4. Un fichier `render.yaml` (Blueprint) est fourni à la racine pour
   automatiser cette création si souhaité.

**Limites du gratuit à connaître** : le service backend s'endort après 15
minutes d'inactivité (premier appel après le réveil : 30-60 secondes de
latence), et dispose de 512 Mo de RAM seulement — d'où l'usage de
`requirements-prod.txt` (dépendances allégées) plutôt que
`requirements.txt` complet pour l'image Docker.

---

## Captures attendues

Une fois l'application lancée (`npm run dev` + `uvicorn`), vous devriez
obtenir :

1. **Écran "Échantillon"** : formulaire des 9 variables à gauche, jauge de
   probabilité animée + facteurs SHAP + rapport IA à droite.
2. **Écran "Lot (CSV)"** : zone de dépôt de fichier, synthèse statistique
   (nombre d'échantillons potables/non potables, variables les plus
   problématiques), résumé IA, et bouton de téléchargement du CSV enrichi.
3. **Swagger** (`/docs`) : documentation interactive de tous les endpoints.

---

## Auteur

Projet réalisé à partir d'une analyse originale en R (classification de la
potabilité de l'eau), reconstruit intégralement en Python dans une optique
d'industrialisation et de portfolio ingénieur IA.

Yanis AMRANE
