# Flask Router Inventory API - Logging Example

This is a simple Flask-based REST API for managing a local inventory of network routers.  
Data is stored in a flat file (`db.txt`) as a list of JSON objects.  
The app supports basic `GET`, `POST`, and `DELETE` operations and logs activity to both the console (with Rich formatting) and a log file.

## Endpoints

- **GET /routers** → Retrieve a router by hostname
- **POST /routers** → Add a new router to the DB
- **DELETE /routers** → Delete a router by hostname
- **Rich Console Logging** and **Persistent File Logs**

> All logs are saved to `filename.log` in the same directory

## Usage

1. Start the App with:
```bash
python3 app.py
```

2. Test Endpoints
### Add a router

```bash
curl -X POST http://127.0.0.1:5000/routers \
     -H "Content-Type: application/json" \
     -d '{"hostname": "SW1", "model": "C9300", "mgmt_ip": "10.10.10.1"}'
```

### Get router by hostname

```bash
curl "http://127.0.0.1:5000/routers?hostname=SW1"
```

### Delete a router

```bash
curl -X DELETE http://127.0.0.1:5000/routers \
     -H "Content-Type: application/json" \
     -d '{"hostname": "SW1"}'
```

## Logging

- Console logs use **Rich** for colorful formatting
- File logs are saved in `filename.log` (rotating log support can be added later)
- Logging includes:
  - API requests
  - Warnings for invalid or missing input
  - Full traceback on exceptions
