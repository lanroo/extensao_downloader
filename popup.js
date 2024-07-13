document.addEventListener('DOMContentLoaded', function () {
    const socket = io('http://127.0.0.1:5000');

    const downloadButton = document.getElementById('download-button');
    if (downloadButton) {
        downloadButton.addEventListener('click', async () => {
            const url = document.getElementById('url-input').value;
            const format = document.querySelector('input[name="format"]:checked').value;
            document.getElementById('progress-container').style.display = 'block';

            try {
                const response = await fetch('http://127.0.0.1:5000/download', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ url: url, format: format }),
                });

                if (response.ok) {
                    const blob = await response.blob();
                    const downloadUrl = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.style.display = 'none';
                    a.href = downloadUrl;
                    a.download = `video.${format}`;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(downloadUrl);
                    Swal.fire({
                        icon: 'success',
                        title: 'Download concluído com sucesso!',
                        showConfirmButton: false,
                        timer: 1500
                    });
                } else {
                    console.error('Falha no download:', response.statusText);
                    Swal.fire({
                        icon: 'error',
                        title: 'Falha no download',
                        text: 'Por favor, tente novamente.',
                    });
                }
            } catch (error) {
                console.error('Erro:', error);
                Swal.fire({
                    icon: 'error',
                    title: 'Erro ao tentar baixar o vídeo',
                    text: 'Verifique a URL e tente novamente.',
                });
            }

            document.getElementById('progress-container').style.display = 'none';
        });

        socket.on('progress', (data) => {
            const progressBar = document.getElementById('progress-bar');
            if (progressBar) {
                const percentString = data.percent.replace('%', '').trim();
                const percent = parseFloat(percentString);
                if (!isNaN(percent) && isFinite(percent)) {
                    progressBar.value = percent;
                } else {
                    console.error('Invalid progress percent:', data.percent);
                }
            }
        });
    }
});
