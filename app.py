from flask import Flask, request, send_file, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import yt_dlp
import os
import logging

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

socketio = SocketIO(app)

# Diretório absoluto para a pasta downloads
DOWNLOAD_DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')

@app.route('/')
def index():
    return "Server is running. Use the extension to download videos."

@app.route('/download', methods=['POST'])
def download_video():
    data = request.json
    url = data['url']
    format = data['format']
    ydl_opts = {
        'outtmpl': os.path.join(DOWNLOAD_DIRECTORY, '%(title)s.%(ext)s'),
        'format': 'bestvideo+bestaudio/best' if format == 'mp4' else 'bestaudio/best',
        'progress_hooks': [my_hook],
    }

    try:
        print(f"Iniciando o download do vídeo da URL: {url}", flush=True)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.download([url])
            video_info = ydl.extract_info(url, download=False)
            video_title = video_info['title']
            video_extension = 'mp4' if format == 'mp4' else 'webm'
            video_path = os.path.join(DOWNLOAD_DIRECTORY, f'{video_title}.{video_extension}')

        print(f"Download concluído. Enviando o arquivo {video_path}...", flush=True)
        if os.path.exists(video_path):
            return send_file(video_path, as_attachment=True, download_name=f'{video_title}.{video_extension}')
        else:
            print(f"Arquivo não encontrado: {video_path}", flush=True)
            return jsonify({'error': f"Arquivo não encontrado: {video_path}"}), 500
    except Exception as e:
        print(f"Erro ao baixar o vídeo: {e}", flush=True)
        return jsonify({'error': str(e)}), 500

def my_hook(d):
    if d['status'] == 'downloading':
        percent_str = d['_percent_str'].replace('\x1b[0;94m', '').replace('\x1b[0m', '').strip()
        try:
            percent = float(percent_str.strip('%'))
            print(f"Progresso: {d['_percent_str']}", flush=True)
            socketio.emit('progress', {'percent': percent})
        except ValueError as e:
            print(f"Erro ao converter a string de progresso: {e}", flush=True)

logging.basicConfig(level=logging.DEBUG)

if not os.path.exists(DOWNLOAD_DIRECTORY):
    print(f"Criando diretório de downloads: {DOWNLOAD_DIRECTORY}", flush=True)
    os.makedirs(DOWNLOAD_DIRECTORY)

if __name__ == '__main__':
    socketio.run(app, debug=True)
