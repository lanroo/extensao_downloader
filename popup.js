document.getElementById('downloadVideo').addEventListener('click', function () {
    chrome.tabs.query({active: true, currentWindow: true}, function (tabs) {
      chrome.tabs.sendMessage(tabs[0].id, {action: "getVideoInfo"}, function (response) {
        let videoUrl = response.url;
        let videoTitle = response.title;
        let downloadUrl = `https://www.y2mate.com/youtube/${videoUrl}`; // URL de um serviço de terceiros para download
  
        chrome.runtime.sendMessage({action: "download", url: downloadUrl, filename: videoTitle + '.mp4'});
      });
    });
  });
  