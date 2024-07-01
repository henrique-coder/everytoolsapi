# First stage: build stage
FROM python:3.12.4-alpine3.20 as build

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install build dependencies and ffmpeg
RUN apk update \
    && apk add --no-cache \
        build-base \
        gcc \
        libffi-dev \
        musl-dev \
        openssl-dev

# Copy all files from the current directory to the container /app directory and install Python packages from requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Second stage: runtime stage
FROM python:3.12.4-alpine3.20

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Copy FFmpeg, Python packages and the application code from the build stage
COPY --from=build /app /app
COPY --from=build /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=build /usr/local/bin/gunicorn /usr/local/bin/gunicorn

# Copy the application code from the current directory to the container /app directory
COPY static/ static/
COPY templates/ templates/
COPY requirements.txt requirements.txt
COPY everytoolsapi.py everytoolsapi.py
COPY config.yaml config.yaml
COPY favicon.ico favicon.ico
COPY .env .env
# COPY .env.dev .env.dev  # This is for development only

RUN apk add --no-cache ffmpeg

# Expose the port Gunicorn will listen on
EXPOSE 13579

# Create a non-root user
RUN addgroup -S appuser && adduser -S -G appuser appuser && chown -R appuser /app
USER appuser

# Command to run Gunicorn when the container launches
CMD ["gunicorn", "-b", "0.0.0.0:13579", "everytoolsapi:app"]
