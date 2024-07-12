document.getElementById('download-button').addEventListener('click', async () => {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const url = tab.url;

    if (!url.includes('youtube.com/watch')) {
        alert('Por favor, abra um vídeo do YouTube.');
        return;
    }

    try {
        const response = await fetch('http://127.0.0.1:5000/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url: url }),
        });

        if (response.ok) {
            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = downloadUrl;
            a.download = 'video.mp4';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(downloadUrl);
            alert('Download concluído com sucesso!');
        } else {
            console.error('Falha no download:', response.statusText);
            alert('Falha no download. Por favor, tente novamente.');
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao tentar baixar o vídeo. Verifique a URL e tente novamente.');
    }
});
