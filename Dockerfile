FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    redis-tools \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/
COPY scripts/ ./scripts/

# Create directories
RUN mkdir -p logs keys ssl data

# Expose ports
EXPOSE 5000 25 587 465

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run application
CMD ["gunicorn", "-w", "8", "-b", "0.0.0.0:5000", \
     "--timeout", "300", "--worker-class", "sync", \
     "app.main:create_app()"]
