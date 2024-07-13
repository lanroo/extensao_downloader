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
                    a.download = response.headers.get('Content-Disposition').split('filename=')[1].replace(/"/g, '');
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(downloadUrl);
                    Swal.fire('Download concluído com sucesso!', '', 'success');
                } else {
                    console.error('Falha no download:', response.statusText);
                    Swal.fire('Falha no download', 'Por favor, tente novamente.', 'error');
                }
            } catch (error) {
                console.error('Erro:', error);
                Swal.fire('Erro ao tentar baixar o vídeo', 'Verifique a URL e tente novamente.', 'error');
            }

            document.getElementById('progress-container').style.display = 'none';
        });

        socket.on('progress', (data) => {
            const progressBar = document.getElementById('progress-bar');
            if (progressBar) {
                progressBar.value = data.percent;
                progressBar.innerText = `${data.percent}%`; // Adiciona a porcentagem ao texto
            }
        });
    }
});
