# ── Stage: Production image ──────────────────────────────────────────
FROM python:3.11-slim

# System packages required by OpenCV and image processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY app.py config.py database.py defect_detector.py gunicorn.conf.py ./

# Copy YOLO model weights
COPY yolov8n.pt ./
# Uncomment below if you also want the medium model (larger, more accurate)
# COPY yolov8m.pt ./

# Copy trained model weights
COPY models/ ./models/

# Create data directories (will use /data volume on HF Spaces)
RUN mkdir -p /data/uploads /data/inspection_results /data/logs

# Hugging Face Spaces expects port 7860
EXPOSE 7860

# Run with Gunicorn production server
CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]
