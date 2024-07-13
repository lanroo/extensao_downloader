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
                    const contentDisposition = response.headers.get('Content-Disposition');
                    const fileName = contentDisposition ? contentDisposition.split('filename=')[1].replace(/["']/g, "") : 'video';
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
});
