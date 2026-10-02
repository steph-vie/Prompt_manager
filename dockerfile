FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Considéré "unhealthy" après 3 échecs consécutifs (les échecs pendant
# start-period ne comptent pas : la maintenance tourne avant le serveur)
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health', timeout=3)" || exit 1

ENV PYTHONUNBUFFERED=1
CMD ["sh", "-c", "flask maintenance && flask run --host=0.0.0.0"]