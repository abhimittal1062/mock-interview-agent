FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg build-essential git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# CPU-only torch, no CUDA/NVIDIA downloads
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.12.0

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
