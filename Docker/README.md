# Simple Flask API (Dockerized)

This is a minimal Flask API example built for learning and quick prototyping. The application includes a single endpoint and is fully containerized using Docker.

## Features

- Python 3.11 (slim image)
- Flask web framework
- Rich console logging for development visibility
- Dockerized for portability

## API Endpoint

**GET** `/api/endpoint`  
Returns a JSON message confirming receipt.

Example response:
```json
{
  "message": "received"
}
```

## Getting Started

### Prerequisites

- Docker installed on your system

### Build and Run

```bash
docker build -t flask-api .
docker run -p 5000:5000 flask-api
```

### Test the Endpoint

After the container is running, access the endpoint:

```
http://localhost:5000/api/endpoint
```
