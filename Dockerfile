# Use the official Python image from the Docker Hub
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create and set the working directory
WORKDIR /app

# Install system dependencies, including git
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install Python dependencies
#COPY requirements.txt .
#
## Install Python dependencies
COPY . .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt
RUN pip install uvicorn
# Copy the rest of the application code#
#COPY . .

# Expose the port that Uvicorn will run on
EXPOSE 8000
#RUN pwd && ls
### Command to run the application using Uvicorn
CMD ["uvicorn", "project.asgi:application", "--host", "0.0.0.0", "--port", "8000"]
