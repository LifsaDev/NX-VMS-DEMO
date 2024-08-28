from flask import Flask, request, jsonify
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

DB_PATH = '/data/errors.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS error_logs
                 (timestamp TEXT, service TEXT, message TEXT)''')
    conn.commit()
    conn.close()

@app.route('/log', methods=['POST'])
def log_error():
    data = request.json
    if not data or 'service' not in data or 'message' not in data:
        return jsonify({'error': 'Invalid request'}), 400

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO error_logs VALUES (?, ?, ?)",
              (datetime.now().isoformat(), data['service'], data['message']))
    conn.commit()
    conn.close()

    return jsonify({'status': 'success'}), 200

@app.route('/logs', methods=['GET'])
def get_logs():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM error_logs ORDER BY timestamp DESC LIMIT 100")
    logs = [{'timestamp': row[0], 'service': row[1], 'message': row[2]} for row in c.fetchall()]
    conn.close()

    return jsonify(logs), 200

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
