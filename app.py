import re
import time
import json
from flask import Flask, request, jsonify, render_template, send_file
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import yt_dlp
import os
import shutil
import threading

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*")

DOWNLOAD_DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')
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

# Funções relacionadas a popup.html

def clean_percentage_string(percent_str):
    """Remove caracteres ANSI e outros não numéricos."""
    # Remove caracteres ANSI
    percent_str = re.sub(r'\x1b\[[0-9;]*m', '', percent_str)
    # Remove qualquer coisa que não seja um dígito ou ponto
    percent_str = re.sub(r'[^\d.]', '', percent_str)
    return percent_str.strip()

def my_hook(d):
    task_id = d['info_dict'].get('task_id')
    if task_id and is_canceled(task_id):
        raise yt_dlp.utils.DownloadError('Download canceled by user')
    
    if d['status'] == 'downloading':
        percent_str = d['_percent_str'].strip()
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

def is_canceled(task_id):
    return downloads.get(task_id, {}).get('cancel', False)

class MyLogger:
    def debug(self, msg):
        if 'download' in msg:
            print(msg)

    def warning(self, msg):
        print(msg)

    def error(self, msg):
        print(msg)

def custom_download(url, format, task_id):
    ydl_opts = {
        'format': 'bestaudio/best' if format == 'mp3' else 'bestvideo+bestaudio',
        'outtmpl': os.path.join(DOWNLOAD_DIRECTORY, f'{task_id}.%(ext)s'),
        'logger': MyLogger(),
        'progress_hooks': [my_hook],
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            info_dict['task_id'] = task_id  
            
            ydl.download([url])
    except yt_dlp.utils.DownloadError as e:
        if str(e) == 'Download canceled by user':
            print(f"Download {task_id} foi cancelado.")
        else:
            print(f"Erro no download: {e}")
    finally:
        downloads.pop(task_id, None)

@app.route('/download', methods=['POST'])
def start_download():
    data = request.json
    url = data['url']
    format = data['format']
    task_id = str(int(time.time() * 1000))
    downloads[task_id] = {'cancel': False}
    thread = threading.Thread(target=custom_download, args=(url, format, task_id))
    downloads[task_id]['thread'] = thread
    thread.start()
    return jsonify({'task_id': task_id})

@app.route('/downloaded-file/<task_id>', methods=['GET'])
def get_downloaded_file(task_id):
    file_path = os.path.join(DOWNLOAD_DIRECTORY, f'{task_id}.mp4')  
    return send_file(file_path, as_attachment=True)

@app.route('/cancel', methods=['POST'])
def cancel_download():
    data = request.json
    task_id = data['task_id']
    print(f"Cancel request received for task_id: {task_id}")  
    if task_id in downloads:
        downloads[task_id]['cancel'] = True
        thread = downloads[task_id].get('thread')
        if thread:
            thread.join(timeout=1)  
        print(f"Task {task_id} canceled.")  # Log para depuração
        return jsonify({'status': 'canceled'})
    print(f"Task {task_id} not found.")  # Log para depuração
    return jsonify({'status': 'not_found'})

@app.route('/progress', methods=['GET'])
def get_progress():
    return jsonify(current_progress)

if not os.path.exists(DOWNLOAD_DIRECTORY):
    os.makedirs(DOWNLOAD_DIRECTORY)

if __name__ == '__main__':
    socketio.run(app, debug=True)
