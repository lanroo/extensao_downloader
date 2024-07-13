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
    extension = 'mp4' if format == 'mp4' else 'mp3'
    video_path = os.path.join(DOWNLOAD_DIRECTORY, f'video.{extension}')
    ydl_opts = {
        'outtmpl': video_path,
        'format': 'bestaudio/best' if format == 'mp3' else 'bestvideo+bestaudio/best',
        'progress_hooks': [my_hook],
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }] if format == 'mp3' else [],
    }

    try:
        print(f"Iniciando o download do vídeo da URL: {url}", flush=True)  # Log da URL
        print(f"Salvando o vídeo em: {video_path}", flush=True)  # Log do caminho do arquivo
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print(f"Download concluído. Enviando o arquivo {video_path}...", flush=True)
        if os.path.exists(video_path):
            return send_file(video_path, as_attachment=True, download_name=f'video.{extension}')
        else:
            print(f"Arquivo não encontrado: {video_path}", flush=True)
            return jsonify({'error': f"Arquivo não encontrado: {video_path}"}), 500
    except Exception as e:
        print(f"Erro ao baixar o vídeo: {e}", flush=True)  # Adicionando print para depuração
        return jsonify({'error': str(e)}), 500

def my_hook(d):
    if d['status'] == 'downloading':
        print(f"Progresso: {d['_percent_str']}", flush=True)  # Log do progresso
        socketio.emit('progress', {'percent': d['_percent_str']})

logging.basicConfig(level=logging.DEBUG)

if not os.path.exists(DOWNLOAD_DIRECTORY):
    print(f"Criando diretório de downloads: {DOWNLOAD_DIRECTORY}", flush=True)
    os.makedirs(DOWNLOAD_DIRECTORY)

if __name__ == '__main__':
    socketio.run(app, debug=True)