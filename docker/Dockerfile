# Build the CSS tailwind using node
FROM node:20-slim AS frontend
# set the working dir
WORKDIR /app
# copy dependencies to allow caching
COPY smart_hotel_system/package.json smart_hotel_system/package-lock.json ./
# install dependencies
RUN npm ci
# copy the tailwind source files
COPY smart_hotel_system/static ./static
COPY smart_hotel_system/tailwind.config.js smart_hotel_system/postcss.config.js ./
# build the css using tailwind script
RUN npm run tailwind:build



# Build the Django app that serves the frontend
FROM python:3.11-slim AS backend
# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:$PYTHONPATH
# setting up the working directory
WORKDIR /app
# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*
# Copy dependencies to allow caching
COPY smart_hotel_system/requirements.txt ./requirements.txt
# install dependencies
ENV PIP_DEFAULT_TIMEOUT=100
RUN pip install -r requirements.txt
# Copy the Django application files
COPY smart_hotel_system/ ./
# copy the built css from the frontend stage
COPY --from=frontend /app/static/dist ./static/dist
# collect static files
RUN python manage.py collectstatic --noinput
# expose the port
EXPOSE 8000
# Security: run as non-root
RUN groupadd -r appgroup && useradd -r -g appgroup appuser && \
    chown -R appuser:appgroup /app
USER appuser
# run the server
CMD ["gunicorn", "--chdir", "/app", "smart_hotel_system.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]