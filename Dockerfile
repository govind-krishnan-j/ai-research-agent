FROM node:22-bookworm-slim AS frontend
WORKDIR /build
COPY web/package*.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY agent.py api.py report.py tools.py ./
COPY --from=frontend /build/dist ./web/dist
ENV REQUIRE_INVITE=1
CMD ["sh", "-c", "exec python -m uvicorn api:app --host 0.0.0.0 --port \"${PORT:-8000}\" --workers 1"]
