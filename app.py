import re
import time
import json
from flask import Flask, request, jsonify, Response, render_template
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import yt_dlp
import os
import shutil
import urllib.parse
import threading

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*")

DOWNLOAD_DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')
download_lock = threading.Lock()
current_progress = {"percent": 0}
downloads = {}

def remove_pycache():
    for root, dirs, files in os.walk('.'):
        for dir in dirs:
            if dir == '__pycache__':
                shutil.rmtree(os.path.join(root, dir))

remove_pycache()

def generate(video_path):
    with open(video_path, 'rb') as f:
        while chunk := f.read(4096):
            yield chunk

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/test-cors', methods=['GET'])
def test_cors():
    response = jsonify({'message': 'CORS is working!'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

def clean_percentage_string(percent_str):
    """Remove caracteres ANSI e outros não numéricos."""
    # Remove caracteres ANSI
    percent_str = re.sub(r'\x1b\[[0-9;]*m', '', percent_str)
    # Remove qualquer coisa que não seja um dígito ou ponto
    percent_str = re.sub(r'[^\d.]', '', percent_str)
    return percent_str.strip()

def my_hook(d):
    if d['status'] == 'downloading':
        percent_str = d['_percent_str'].strip()
        # Limpar a string de porcentagem
        percent_str = clean_percentage_string(percent_str)
        
        try:
            percent = float(percent_str)
            current_progress["percent"] = percent
            print(f"Emitting progress: {percent}%")
            socketio.emit('progress', {'percent': percent})
        except ValueError as e:
            print(f"ValueError: Could not convert percent_str to float: {percent_str}")
            print(f"Exception: {e}")
    elif d['status'] == 'finished':
        print("Download finished")
        current_progress["percent"] = 100
        socketio.emit('progress', {'percent': 100})

def download_video(url, format, task_id):
    ydl_opts = {
        'format': 'bestaudio/best' if format == 'mp3' else 'bestvideo+bestaudio',
        'progress_hooks': [my_hook],
        'outtmpl': os.path.join(DOWNLOAD_DIRECTORY, f'{task_id}.%(ext)s'),
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        print(f"Download error: {e}")
    finally:
        downloads.pop(task_id, None)

@app.route('/download', methods=['POST'])
def start_download():
    data = request.json
    url = data['url']
    format = data['format']
    task_id = str(int(time.time() * 1000))
    downloads[task_id] = {'cancel': False}
    thread = threading.Thread(target=download_video, args=(url, format, task_id))
    thread.start()
    return jsonify({'task_id': task_id})

@app.route('/cancel', methods=['POST'])
def cancel_download():
    data = request.json
    task_id = data['task_id']
    if task_id in downloads:
        downloads[task_id]['cancel'] = True
        return jsonify({'status': 'canceled'})
    return jsonify({'status': 'not_found'})

@app.route('/progress', methods=['GET'])
def get_progress():
    return jsonify(current_progress)

if not os.path.exists(DOWNLOAD_DIRECTORY):
    os.makedirs(DOWNLOAD_DIRECTORY)

if __name__ == '__main__':
    socketio.run(app, debug=True)
