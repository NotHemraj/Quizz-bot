FROM python:3.10-slim

# System dependencies
RUN apt-get update && apt-get install -y gcc libpq-dev

# Create working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Run the bot
CMD ["python", "main.py"]
