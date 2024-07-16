import re
import time

import flask
from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO
from flask_cors import CORS
import yt_dlp
import os
import shutil
import threading
import uuid

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*")

DOWNLOAD_DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')
download_lock = threading.Lock()
downloads = {}


# TODO: remove duplicated code and transform into smaller functions nothing too silly is missing rn lol
# INFO: the trick for cancelling the download is raising the DownloadCancelled exception from yt_dlp
# INFO: PHook is called every time the download progress changes, so we can use it to update the progress bar
# INFO: PHook now uses a callback instead of a static function

class YtWrapperDownloader:
    def __init__(self, url, file_mime, progress_callback):
        self.url = url
        self.format = file_mime
        self.task_id = str(uuid.uuid4())
        self.__cancel_video = False
        self.progress_callback = progress_callback
        self.progress = 0

        self.ydl_opts = {
            'format': 'bestaudio/best' if self.format == 'mp3' else 'bestvideo+bestaudio',
            'progress_hooks': [self.__progress_hook],
            'outtmpl': os.path.join(DOWNLOAD_DIRECTORY, f'{self.task_id}.%(ext)s'),
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            },
        }
        self.instance = yt_dlp.YoutubeDL(self.ydl_opts)
        self.thread = threading.Thread(target=self.__execute)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.instance.close()
        self.wait_join()

    def execute(self, wait_join=False):
        with download_lock:
            try:
                self.thread.start()
                if wait_join:
                    self.thread.join()
            except Exception as e:
                print(f"Error: {e}")

    def wait_join(self):
        if self.thread.is_alive():
            self.thread.join()

    def __progress_hook(self, d):
        if d['status'] == 'downloading':
            if self.__cancel_video:
                raise yt_dlp.DownloadCancelled()

            percent_str = d['_percent_str'].strip()
            percent_str = clean_percentage_string(percent_str)

            try:
                self.percent = float(percent_str)
                if self.percent > 100:
                    self.percent = 100

                self.progress_callback(f"status", jsonify({'task_id': self.task_id, 'progress': self.percent}))
            except ValueError as e:
                print(f"ValueError: Could not convert percent_str to float: {percent_str}")
                print(f"Exception: {e}")
        elif d['status'] == 'finished':
            self.percent = 100
            self.progress_callback(f"status", jsonify({'task_id': self.task_id, 'progress': self.percent}))

    def __execute(self):
        try:
            self.instance.download([self.url])
        except Exception as e:
            print(f"Download error: {e}")
        finally:
            downloads.pop(self.task_id, None)

    def cancel(self):
        print(f"Canceling task {self.task_id}")
        self.instance.close()
        self.__cancel_video = True
        self.wait_join()
        print(f"Task {self.task_id} canceled.")


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


@app.route('/download', methods=['POST'])
def start_download():
    data = request.json
    downloader = YtWrapperDownloader(data['url'], data['format'], socketio.emit)
    print(f"Starting download for task_id: {downloader.task_id}")

    try:
        downloader.execute()
        downloads[downloader.task_id] = downloader
    except Exception as e:
        print(f"Error: {e}")
        return flask.abort(500, 'Error starting download')

    return jsonify({'task_id': downloader.task_id, 'code': 'started'})


@app.route('/cancel', methods=['POST'])
def cancel_download():
    data = request.json
    task_id = data['task_id']

    if task_id is None or task_id == '':
        return flask.abort(400, 'task_id is required')

    if not re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', task_id):
        return flask.abort(400, 'invalid task_id')

    if task_id in downloads:
        downloads[task_id].cancel()
        return jsonify({'code': 'canceled'})
    return flask.abort(400, 'task_id not found')


@app.route('/progress', methods=['POST'])
def get_progress():
    data = request.json
    task_id = data['task_id']

    if task_id is None or task_id == '':
        return flask.abort(400, 'task_id is required')

    if not re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', task_id):
        return flask.abort(400, 'invalid task_id')

    if task_id in downloads:
        return jsonify({'progress': downloads[task_id].progress})
    return flask.abort(400, 'task_id not found')


if not os.path.exists(DOWNLOAD_DIRECTORY):
    os.makedirs(DOWNLOAD_DIRECTORY)

if __name__ == '__main__':
    socketio.run(app, debug=True)
