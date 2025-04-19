# Use latest slim Python image
FROM python:3.11-slim

LABEL maintainer="Trevor Maco <tdog135@gmail.com>"

# Set working directory
WORKDIR /app

# Install dependencies
COPY ./app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY ./app .

# Expose port
EXPOSE 5000

# Start the app
CMD ["python", "main.py"]
