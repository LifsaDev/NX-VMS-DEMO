from flask import Flask, request, jsonify
import sqlite3
import os

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
    if not data or 'service' not in