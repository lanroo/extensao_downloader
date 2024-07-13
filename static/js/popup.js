document.addEventListener('DOMContentLoaded', function () {
    const downloadButton = document.getElementById('download-button');
    const cancelButton = document.getElementById('cancel-button');
    const progressContainer = document.getElementById('progress-container');
    const progressBar = document.getElementById('progress-bar');
    const socket = io('http://127.0.0.1:5000');
    let taskId = null;

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
            downloadButton.style.display = 'none';
            cancelButton.style.display = 'block';

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

                const responseData = await response.json();
                taskId = responseData.task_id;

                if (!response.ok) {
                    const errorText = await response.text();
                    console.error('Download failed:', errorText);
                    Swal.fire('Falha no download', errorText, 'error');
                }
            } catch (error) {
                console.error('Download error:', error);
                Swal.fire('Erro ao tentar baixar o vídeo', error.message, 'error');
            }
        });
    }

    cancelButton.addEventListener('click', async () => {
        if (taskId) {
            try {
                const response = await fetch('http://127.0.0.1:5000/cancel', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ task_id: taskId }),
                });

                const responseData = await response.json();

                if (responseData.status === 'canceled') {
                    Swal.fire('Download cancelado', '', 'info');
                    downloadButton.style.display = 'block';
                    cancelButton.style.display = 'none';
                    progressContainer.style.display = 'none';
                    updateProgress(0);
                    localStorage.removeItem('savedUrl');
                    localStorage.removeItem('savedProgress');
                } else {
                    Swal.fire('Erro', 'Download não encontrado ou já finalizado', 'error');
                }
            } catch (error) {
                console.error('Cancel error:', error);
                Swal.fire('Erro ao tentar cancelar o download', error.message, 'error');
            }
        }
    });

    function updateProgress(percent) {
        progressBar.style.width = `${percent}%`;
        progressBar.innerText = `${percent.toFixed(2)}%`;
        console.log(`Progress updated: ${percent}%`);
    }
});
