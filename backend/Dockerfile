FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV MODEL_N_JOBS=1

EXPOSE 8000

CMD ["uvicorn", "ml_api_stroke:app", "--host", "0.0.0.0", "--port", "8000"]