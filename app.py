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

@app.route('/download', methods=['POST'])
def download_video():
    with download_lock:
        try:
            data = request.json
            url = data['url']
            format = data['format']
            print(f"Received download request for URL: {url} and format: {format}")
            
            ydl_opts = {
                'format': 'bestaudio/best' if format == 'mp3' else 'bestvideo+bestaudio/best',
                'outtmpl': os.path.join(DOWNLOAD_DIRECTORY, '%(title)s.%(ext)s'),
                'merge_output_format': 'mp4' if format != 'mp3' else None,
                'progress_hooks': [my_hook],
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio' if format == 'mp3' else 'FFmpegVideoConvertor',
                    'preferredcodec': 'mp3' if format == 'mp3' else 'mp4',
                    'preferredquality': '192' if format == 'mp3' else None,
                }] if format == 'mp3' else [],
                'noplaylist': True,
                'continuedl': True,
                'ratelimit': None,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                title = info_dict.get('title', 'video')
                if format == 'mp3':
                    file_title = os.path.join(DOWNLOAD_DIRECTORY, f"{title}.mp3")
                else:
                    file_title = os.path.join(DOWNLOAD_DIRECTORY, f"{title}.mp4")
            
            if os.path.exists(file_title):
                encoded_title = urllib.parse.quote(os.path.basename(file_title))
                return Response(generate(file_title), headers={
                    'Content-Disposition': f'attachment; filename="{encoded_title}"',
                    'Content-Length': os.path.getsize(file_title),
                    'Access-Control-Allow-Origin': '*'
                })
            else:
                return jsonify({'error': f"Arquivo não encontrado: {file_title}"}), 500
        except yt_dlp.utils.DownloadError as e:
            print(f"Download error: {e}")
            return jsonify({'error': f"Erro ao baixar o vídeo: {e}"}), 500
        except Exception as e:
            print(f"Unexpected error: {e}")
            return jsonify({'error': f"Erro inesperado: {e}"}), 500

def my_hook(d):
    if d['status'] == 'downloading':
        percent_str = re.sub(r'\x1b\[[0-9;]*m', '', d['_percent_str']).replace('%', '').strip()
        percent_str = percent_str.replace('\x1b[0;94m', '').replace('\x1b[0m', '').strip()
        print(f"Download status: {d['status']}, Percent: {percent_str}")
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

@app.route('/progress', methods=['GET'])
def get_progress():
    return jsonify(current_progress)

if not os.path.exists(DOWNLOAD_DIRECTORY):
    os.makedirs(DOWNLOAD_DIRECTORY)

if __name__ == '__main__':
    socketio.run(app, debug=True)
