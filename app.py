from flask import Flask, request, send_file, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import yt_dlp
import os
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
    try:
        data = request.json
        url = data['url']
        format = data['format']
        
        if format == 'mp3':
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(DOWNLOAD_DIRECTORY, '%(title)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'progress_hooks': [my_hook],
            }
        else:
            ydl_opts = {
                'format': 'bestvideo+bestaudio/best',
                'outtmpl': os.path.join(DOWNLOAD_DIRECTORY, '%(title)s.%(ext)s'),
                'merge_output_format': 'mp4',
                'progress_hooks': [my_hook],
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            if format == 'mp3':
                file_title = ydl.prepare_filename(info_dict).rsplit('.', 1)[0] + '.mp3'
            else:
                file_title = ydl.prepare_filename(info_dict).rsplit('.', 1)[0] + '.mp4'
        
        if os.path.exists(file_title):
            return send_file(file_title, as_attachment=True, download_name=os.path.basename(file_title))
        else:
            return jsonify({'error': f"Arquivo não encontrado: {file_title}"}), 500
    except yt_dlp.utils.DownloadError as e:
        return jsonify({'error': f"Erro ao baixar o vídeo: {e}"}), 500
    except Exception as e:
        return jsonify({'error': f"Erro inesperado: {e}"}), 500

def my_hook(d):
    if d['status'] == 'downloading':
        percent_str = d['_percent_str'].replace('%', '').strip()
        try:
            percent = float(percent_str.replace(',', '.'))
            socketio.emit('progress', {'percent': percent})
        except ValueError:
            pass
    elif d['status'] == 'finished':
        pass

if not os.path.exists(DOWNLOAD_DIRECTORY):
    os.makedirs(DOWNLOAD_DIRECTORY)

if __name__ == '__main__':
    socketio.run(app, debug=False)
