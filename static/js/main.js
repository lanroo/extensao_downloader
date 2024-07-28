document.addEventListener('DOMContentLoaded', function () {
    const downloadButton = document.getElementById('downloadBtn');
    const progressContainer = document.querySelector('.progress');
    const progressBar = document.querySelector('.progress-bar');
    const refreshButton = document.getElementById('refreshBtn');

    if (downloadButton) {
        downloadButton.addEventListener('click', async () => {
            const url = document.getElementById('url').value;
            const format = document.querySelector('input[name="format"]:checked').value;
            progressContainer.style.display = 'block';
            updateProgress(0);

            try {
                const response = await fetch('http://127.0.0.1:5000/download', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ url: url, format: format }),
                });

                if (response.ok) {
                    const reader = response.body.getReader();
                    const contentLength = +response.headers.get('Content-Length');
                    let receivedLength = 0;
                    const chunks = [];

                    while (true) {
                        const { done, value } = await reader.read();
                        if (done) break;
                        chunks.push(value);
                        receivedLength += value.length;

                        let percent = (receivedLength / contentLength) * 100;
                        updateProgress(percent);
                    }

                    const blob = new Blob(chunks);
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
                } else {
                    const errorText = await response.text();
                    Swal.fire('Falha no download', errorText, 'error');
                }
            } catch (error) {
                Swal.fire('Erro ao tentar baixar o vídeo', error.message, 'error');
            }
        });
    }

    if (refreshButton) {
        refreshButton.addEventListener('click', () => {
            localStorage.clear();
            sessionStorage.clear();
            resetForm();
        });
    }

    function updateProgress(percent) {
        progressBar.style.width = `${percent}%`;
        progressBar.innerText = `${percent.toFixed(2)}%`;
    }

    function resetForm() {
        document.getElementById('url').value = '';
        document.querySelector('input[name="format"][value="mp4"]').checked = true;
        updateProgress(0);
        progressContainer.style.display = 'none';
    }
});
