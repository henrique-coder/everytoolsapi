# Use an official Python runtime as a parent image
FROM python:3.12.3

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Copy all files from the current directory to the container /app directory
COPY . .

# Install any needed packages specified in requirements.txt
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r requirements.txt

# Expose the port Gunicorn will listen on
EXPOSE 13579

# Create a non-root user
RUN useradd -r -u 1001 appuser \
    && chown -R appuser /app
USER appuser

# Command to run Gunicorn when the container launches
CMD ["gunicorn", "-b", "0.0.0.0:13579", "everytoolsapi:app"]
