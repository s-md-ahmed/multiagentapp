FROM python:3.11-slim

# Install system dependencies including Git
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements from the backend folder and install python packages
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project files
COPY . .

# Expose port and run FastAPI via uvicorn
EXPOSE 10000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "10000"]
