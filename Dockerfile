FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY botpass ./botpass

EXPOSE 8080
# ponytail: retry indefinitely; Botasaurus has no configurable bootstrap timeout.
CMD ["sh", "-c", "until python -m botpass.bootstrap; do sleep 2; done; exec uvicorn botpass.app:app --host 0.0.0.0 --port 8080"]
