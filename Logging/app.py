import json
import os
import logging
from flask import Flask, request, jsonify
from rich.logging import RichHandler

# Initialize Flask app
app = Flask(__name__)

# Determine the directory path this script is running in
script_dir = os.path.dirname(os.path.realpath(__file__))

# ----------------------------
# Logging Configuration
# ----------------------------

LOG_LEVEL = logging.DEBUG
log_format = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

# File handler
file_handler = logging.FileHandler(os.path.join(script_dir, "filename.log"))
file_handler.setLevel(LOG_LEVEL)
file_handler.setFormatter(logging.Formatter(log_format))

# Rich console handler
console_handler = RichHandler(rich_tracebacks=True)
console_handler.setLevel(LOG_LEVEL)
console_handler.setFormatter(logging.Formatter(log_format, datefmt="%H:%M:%S"))

# Root logger setup
logging.basicConfig(level=LOG_LEVEL, handlers=[file_handler, console_handler])
LOG = logging.getLogger("flask-app")

LOG.info(f"script directory: {script_dir}")
LOG.info(f"DB file: {os.path.join(script_dir, 'db.txt')}")


# ----------------------------
# Routes
# ----------------------------

@app.route('/')
def index():
    """Return personal contact info"""
    return jsonify({
        'name': 'trevor',
        'email': 'tmaco@cisco.com',
        'locale': 'https://www.youtube.com/channel/UChRmUH4H5hiYzPiFhvNoCIg'
    })


@app.route('/routers', methods=['GET'])
def get_router():
    """
    Retrieve router details by hostname
    Usage: GET /routers?hostname=SW1
    """
    try:
        hostname = request.args.get('hostname')
        if not hostname:
            LOG.warning('No hostname specified')
            raise ValueError("Hostname is required")

        with open(os.path.join(script_dir, 'db.txt'), 'r') as f:
            records = json.load(f)

        for record in records:
            if record['hostname'] == hostname:
                LOG.info('Router found and returned')
                return jsonify(record), 200

        LOG.warning('No matching router found')
        return jsonify({"response": "No match"}), 200

    except ValueError as ve:
        LOG.error(f"Invalid request: {ve}")
        return jsonify({"error": "NO_HOSTNAME_SPECIFIED"}), 400
    except Exception as err:
        LOG.exception(f'Unexpected error during GET: {err}')
        return jsonify({"error": str(err)}), 500


@app.route('/routers', methods=['POST'])
def add_router():
    """
    Add a new router to the database
    Usage: POST /routers with JSON body
    """
    try:
        record = request.get_json(force=True)
        LOG.info(f'inbound record: {record}')

        with open(os.path.join(script_dir, 'db.txt'), 'r') as f:
            records = json.load(f)

        if record in records:
            LOG.warning(f'Device already exists: {record["hostname"]}')
            return jsonify({"status": "Device already exists"}), 200

        records.append(record)
        LOG.warning(f'Router added: {record.get("hostname")}')

        with open(os.path.join(script_dir, 'db.txt'), 'w') as f:
            json.dump(records, f, indent=2)

        return jsonify(record), 201

    except Exception as err:
        LOG.exception(f'Error during ADD: {err}')
        return jsonify({"error": str(err)}), 500


@app.route('/routers', methods=['DELETE'])
def delete_router():
    """
    Delete a router from the database by hostname
    Usage: DELETE /routers with JSON body { "hostname": "SW1" }
    """
    try:
        target = request.get_json(force=True)
        hostname = target.get("hostname")
        new_records = []

        with open(os.path.join(script_dir, 'db.txt'), 'r') as f:
            records = json.load(f)

        for r in records:
            if r['hostname'] == hostname:
                LOG.warning(f'Deleted router: {hostname}')
                continue
            new_records.append(r)

        with open(os.path.join(script_dir, 'db.txt'), 'w') as f:
            json.dump(new_records, f, indent=2)

        return jsonify({"deleted": hostname}), 204

    except Exception as err:
        LOG.exception(f'Error during DELETE: {err}')
        return jsonify({"error": str(err)}), 500


# ----------------------------
# App Runner
# ----------------------------
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
