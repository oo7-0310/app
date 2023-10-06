import json 
import re 
import subprocess
import requests

from flask import Flask, request, jsonify
from flask_cors import CORS

from whois import bp as whois_bp

app = Flask(__name__)
CORS(app)

@app.route('/test')
def users():
    return "This is from Backend Flask Server"
@app.route('/test', methods=['POST'])
def process_data():
    data = request.json
    print("Received data:", data)
    return jsonify({'result': 'success', 'data': data})

app.register_blueprint(whois_bp)

if __name__ == '__main__':
    app.run(host = '0.0.0.0', debug=True)