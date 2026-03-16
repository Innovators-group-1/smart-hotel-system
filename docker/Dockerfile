############################
#  FRONTEND BUILD STAGE
############################
FROM node:20-slim AS frontend

WORKDIR /app

# Copy package files
COPY smart_hotel_system/package.json smart_hotel_system/package-lock.json ./
RUN npm ci

# Copy static files and config
COPY smart_hotel_system/static ./static
COPY smart_hotel_system/tailwind.config.js smart_hotel_system/postcss.config.js ./

# Copy templates and apps for potential use in frontend build (e.g., for Tailwind scanning)
COPY smart_hotel_system/templates ./templates
COPY smart_hotel_system/apps ./apps

# Build Tailwind CSS
RUN npm run tailwind:build && ls -la static/dist/


############################
#  BACKEND STAGE
############################
FROM python:3.11-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    postgresql-client \
    libpq-dev \
    build-essential \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY smart_hotel_system/requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY smart_hotel_system/ .

# Copy built CSS from frontend stage
COPY --from=frontend /app/static/dist ./static/dist

# Copy and setup entrypoint script (do this as root)
COPY smart_hotel_system/smart_hotel_system/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Create directories for static and media files
RUN mkdir -p /app/staticfiles /app/media

# Create non-root user and set permissions
RUN groupadd -r appgroup && \
    useradd -r -g appgroup appuser && \
    chown -R appuser:appgroup /app /entrypoint.sh

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000


# Use entrypoint for migrations
ENTRYPOINT ["/entrypoint.sh"]

# Start Gunicorn
CMD ["gunicorn", \
     "smart_hotel_system.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info"]