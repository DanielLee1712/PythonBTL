FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 1. Ép cài bản Torch CPU-only trước cho nhẹ (Rất quan trọng!)
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu --no-cache-dir

# Install python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app/

# Expose port
EXPOSE 8002

# Run command
CMD ["gunicorn", "--bind", "0.0.0.0:8002", "core.wsgi:application"]
