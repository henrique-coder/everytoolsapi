# Use an official Python runtime as a parent image
FROM python:3.12.3

# Set the working directory in the container to /app
WORKDIR /app

# Copy all files from the current directory to the container /app directory
COPY . .

# Install any needed packages specified in requirements.txt
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port Gunicorn will listen on
EXPOSE 13579

# Command to run Gunicorn when the container launches
CMD ["gunicorn", "-b", "0.0.0.0:13579", "everytoolsapi:app"]
