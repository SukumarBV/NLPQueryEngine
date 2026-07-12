# syntax=docker/dockerfile:1
#
# Single-service production image: builds the React frontend, then serves
# both the static frontend and the FastAPI backend from one Python
# process on one port. This is the image to deploy to Koyeb's free web
# service (which only allows a single service on the free Instance).
#
# Build:  docker build -t nlp-query-engine .
# Run:    docker run -p 8000:8000 -e GEMINI_API_KEY=... nlp-query-engine

# ---------- Stage 1: build the React frontend ----------
FROM node:20-alpine AS frontend-build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY frontend/ .
# Same-origin deployment: leave the API URL relative ("/api/...").
ENV REACT_APP_API_URL=""
RUN npm run build

# ---------- Stage 2: Python backend + static frontend ----------
FROM python:3.11-slim
WORKDIR /app

COPY backend/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
# Make sure no local secrets ever end up in the image even if present
# in the build context.
RUN rm -f .env

COPY --from=frontend-build /app/build ./static

# Koyeb sets $PORT at runtime; default to 8000 for local `docker run`.
ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
