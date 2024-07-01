# Use an official Python runtime as a parent image
FROM python:3.12

# Set the working directory in the container to root
WORKDIR /

# Install any needed packages specified in requirements.txt
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Run everytoolsapi.py when the container launches
CMD ["gunicorn", "-b", "0.0.0.0:13579", "everytoolsapi:app"]
