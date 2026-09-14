FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt pyproject.toml /app/
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -e .

COPY . /app

# Hugging Face Spaces expects port 7860
EXPOSE 7860

CMD ["python", "-m", "uvicorn", "crop_mix.app:app", "--host", "0.0.0.0", "--port", "7860"]
