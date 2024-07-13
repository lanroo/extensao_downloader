from flask import Flask, request, send_file, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import yt_dlp
import os
import logging
import shutil

def remove_pycache():
    for root, dirs, files in os.walk('.'):
        for dir in dirs:
            if dir == '__pycache__':
                shutil.rmtree(os.path.join(root, dir))

# Remover __pycache__ antes de iniciar o servidor
remove_pycache()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Configure SocketIO to allow connections from the extension
socketio = SocketIO(app, cors_allowed_origins="*")

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
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',
        'progress_hooks': [my_hook],
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',  # Ensure the output format is mp4
        }],
    }

    try:
        print(f"Iniciando o download do vídeo da URL: {url}", flush=True)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            file_title = ydl.prepare_filename(info_dict)
        file_path = os.path.splitext(file_title)[0] + '.mp4'
        print(f"Download concluído. Enviando o arquivo {file_path}...", flush=True)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True, download_name=os.path.basename(file_path))
        else:
            print(f"Arquivo não encontrado: {file_path}", flush=True)
            return jsonify({'error': f"Arquivo não encontrado: {file_path}"}), 500
    except Exception as e:
        print(f"Erro ao baixar o vídeo: {e}", flush=True)
        return jsonify({'error': str(e)}), 500

def my_hook(d):
    if d['status'] == 'downloading':
        percent_str = d['_percent_str'].replace('%', '').strip()
        try:
            percent = float(percent_str)
            socketio.emit('progress', {'percent': percent})
        except ValueError:
            print(f"Erro ao converter {percent_str} para float.")
    elif d['status'] == 'finished':
        print("Download finished.", flush=True)

logging.basicConfig(level=logging.DEBUG)

if not os.path.exists(DOWNLOAD_DIRECTORY):
    print(f"Criando diretório de downloads: {DOWNLOAD_DIRECTORY}", flush=True)
    os.makedirs(DOWNLOAD_DIRECTORY)

if __name__ == '__main__':
    socketio.run(app, debug=True)
