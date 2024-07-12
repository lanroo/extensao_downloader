from flask import Flask, request, send_file, jsonify
import yt_dlp
import os

app = Flask(__name__)

@app.route('/')
def index():
    return "Server is running. Use the extension to download videos."

@app.route('/download', methods=['POST'])
def download_video():
    data = request.json
    url = data['url']
    ydl_opts = {
        'outtmpl': 'downloads/video.mp4',
        'format': 'bestvideo+bestaudio/best',
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return send_file('downloads/video.mp4', as_attachment=True, download_name='video.mp4')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    app.run(debug=True)
