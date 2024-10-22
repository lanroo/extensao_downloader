chrome.runtime.onMessage.addListener(function (request, sender, sendResponse) {
  if (request.action == "download") {
    chrome.downloads.download({
      url: request.url,
      filename: request.filename
    });
  }
});

chrome.runtime.onMessage.addListener(function (request, sender, sendResponse) {
  if (request.action == "getVideoInfo") {
    let videoTitle = document.querySelector('h1.title').innerText;
    let videoUrl = window.location.href;
    sendResponse({title: videoTitle, url: videoUrl});
  }
});
