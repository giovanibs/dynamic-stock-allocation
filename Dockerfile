# syntax=docker/dockerfile:1

FROM python:3.13-slim AS base

WORKDIR /app

# Install `make` as `python:3.13-slim` doesn't include it
RUN apt-get update && apt-get install -y make && apt-get clean

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

COPY . .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -e ./src

EXPOSE 8000

CMD make django-up