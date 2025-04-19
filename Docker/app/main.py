from flask import Flask, jsonify
from rich.console import Console

app = Flask(__name__)
console = Console()


@app.route('/api/endpoint', methods=['GET'])
def get_data():
    """
    Handle GET request to /api/endpoint
    :return: JSON response
    """
    console.log("[green]GET request received[/green] at /api/endpoint")
    return jsonify({'message': 'received'}), 200


if __name__ == '__main__':
    console.log("[bold cyan]Starting Flask API on 0.0.0.0:5000[/bold cyan]")
    app.run(host='0.0.0.0', port=5000)
