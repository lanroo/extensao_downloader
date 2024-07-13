document.addEventListener('DOMContentLoaded', function () {
    const downloadButton = document.getElementById('download-button');
    const progressContainer = document.getElementById('progress-container');
    const progressBar = document.getElementById('progress-bar');
    const socket = io('http://127.0.0.1:5000');

    // Test CORS
    fetch('http://127.0.0.1:5000/test-cors')
        .then(response => response.json())
        .then(data => console.log(data.message))
        .catch(error => console.error('CORS test failed:', error));

    // Load previous URL and progress
    const savedUrl = localStorage.getItem('savedUrl');
    const savedProgress = localStorage.getItem('savedProgress');
    if (savedUrl) {
        document.getElementById('url-input').value = savedUrl;
    }
    if (savedProgress) {
        progressContainer.style.display = 'block';
        updateProgress(parseFloat(savedProgress));
    }

    socket.on('connect', () => {
        console.log('Connected to server');
    });

    socket.on('progress', function (data) {
        const percent = data.percent;
        console.log(`Received progress: ${percent}%`);
        updateProgress(percent);
        localStorage.setItem('savedProgress', percent); 
    });

    if (downloadButton) {
        downloadButton.addEventListener('click', async () => {
            downloadButton.disabled = true; // Disable the button during the download
            const url = document.getElementById('url-input').value;
            const format = document.querySelector('input[name="format"]:checked').value;
            progressContainer.style.display = 'block';
            updateProgress(0);
            localStorage.setItem('savedUrl', url); 

            try {
                console.log("Starting download...");
                const response = await fetch('http://127.0.0.1:5000/download', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ url: url, format: format }),
                });

                if (response.ok) {
                    console.log("Download started, waiting for completion...");
                    const blob = await response.blob();
                    const contentDisposition = response.headers.get('Content-Disposition');
                    let fileName = 'video.mp4';
                    if (contentDisposition) {
                        const matches = /filename\*?=['"]?([^'";]+)['"]?/.exec(contentDisposition);
                        if (matches != null && matches[1]) { 
                            fileName = decodeURIComponent(matches[1]);
                        }
                    }

                    const downloadUrl = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.style.display = 'none';
                    a.href = downloadUrl;
                    a.download = fileName;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(downloadUrl);
                    Swal.fire('Download concluído com sucesso!', '', 'success');
                    localStorage.removeItem('savedUrl'); 
                    localStorage.removeItem('savedProgress'); 
                } else {
                    const errorText = await response.text();
                    console.error('Download failed:', errorText);
                    Swal.fire('Falha no download', errorText, 'error');
                }
            } catch (error) {
                console.error('Download error:', error);
                Swal.fire('Erro ao tentar baixar o vídeo', error.message, 'error');
            } finally {
                downloadButton.disabled = false; 
            }
        });
    }

    function updateProgress(percent) {
        progressBar.style.width = `${percent}%`;
        progressBar.innerText = `${percent.toFixed(2)}%`;
        console.log(`Progress updated: ${percent}%`);
    }
});
