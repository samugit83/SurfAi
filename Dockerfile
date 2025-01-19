# Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies for building Python C extensions and for pygraphviz
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    graphviz \
    libgraphviz-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your project
COPY . .

# Expose the port (Flask default)
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
