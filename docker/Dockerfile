############################
# 1️⃣ FRONTEND BUILD STAGE
############################
FROM node:20-slim AS frontend

WORKDIR /app

COPY smart_hotel_system/package.json smart_hotel_system/package-lock.json ./
RUN npm ci

COPY smart_hotel_system/static ./static
COPY smart_hotel_system/tailwind.config.js smart_hotel_system/postcss.config.js ./

RUN npm run tailwind:build


############################
# 2️⃣ BACKEND STAGE
############################
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:$PYTHONPATH

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    postgresql-client \
    libpq-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY smart_hotel_system/requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy app
COPY smart_hotel_system/ .

# Copy built CSS
COPY --from=frontend /app/static/dist ./static/dist

# Collect static files
RUN python manage.py collectstatic --noinput

# Create non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup appuser && \
    chown -R appuser:appgroup /app

USER appuser

############################
# ENTRYPOINT (MIGRATIONS)
############################
COPY smart_hotel_system/entrypoint.sh /entrypoint.sh
USER root
RUN chmod +x /entrypoint.sh
USER appuser

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]

CMD ["gunicorn","smart_hotel_system.wsgi:application","--bind", "0.0.0.0:8000","--workers", "3","--timeout", "120","--access-logfile", "-","--error-logfile", "-"
]
