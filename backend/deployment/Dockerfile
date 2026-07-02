# Ignite backend — FastAPI stub.
# Build context = backend/.
# Build: docker build -t ignite-backend:dev backend -f backend/deployment/Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./

ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["python", "main.py"]
