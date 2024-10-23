FROM python:3.12-slim

WORKDIR /app

# Install system dependencies and PostgreSQL client
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Set Python to run in unbuffered mode
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Script to run Django
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

#EXPOSE 8000
EXPOSE 80

ENTRYPOINT ["/entrypoint.sh"]

