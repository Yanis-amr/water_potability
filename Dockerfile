# --- Water Potability AI — API backend ---
FROM python:3.12-slim

WORKDIR /app

# Dépendances système minimales (compilation de certains paquets scientifiques)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-prod.txt .
RUN pip install --no-cache-dir -r requirements-prod.txt

COPY src/ ./src/
COPY api/ ./api/
COPY models/ ./models/

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

EXPOSE 8000

# Render (et la plupart des PaaS) injectent une variable d'environnement
# PORT et attendent que l'app écoute dessus. En local / docker-compose,
# PORT n'est pas définie donc on retombe sur 8000.
CMD uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}