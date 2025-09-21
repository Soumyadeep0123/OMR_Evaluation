# --- Stage 1: Build Stage ---
# Use an official Python slim image for a smaller final image size.
FROM python:3.13-slim AS builder

# Set the working directory inside the container.
WORKDIR /app

# Set an environment variable to prevent Python from buffering stdout and stderr.
ENV PYTHONUNBUFFERED=1

# **FIXED HERE**: Using a more robust and standard set of dependencies for OpenCV.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container.
COPY requirements.txt .

# Install the Python dependencies.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application's source code into the container.
COPY . .

# Expose the port that Gunicorn will run on.
EXPOSE 8000

# Command now points to 'main:app' to match your filename.
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "main:app"]