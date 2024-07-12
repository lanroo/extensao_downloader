chrome.runtime.onMessage.addListener(function (request, sender, sendResponse) {
    if (request.action == "download") {
      chrome.downloads.download({
        url: request.url,
        filename: request.filename
      });
    }
  });
  