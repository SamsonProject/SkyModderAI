# SkyModderAI / ModCheck — Docker image
# Build: docker build -t modcheck .
# Run:   docker run -p 5000:5000 modcheck

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p data

# Pre-download LOOT masterlist (avoids cold start on first request)
RUN python loot_parser.py skyrimse || true

EXPOSE 10000
ENV FLASK_ENV=production
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-5000} --timeout 120 --workers 2 --threads 4 app:app"]
