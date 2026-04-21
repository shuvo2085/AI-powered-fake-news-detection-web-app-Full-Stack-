// Content script - runs on every page
// Extracts article text when requested by popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'getPageText') {
    const article = document.querySelector('article') ||
                    document.querySelector('[role="main"]') ||
                    document.querySelector('.article-body') ||
                    document.querySelector('.post-content') ||
                    document.body;
    sendResponse({ text: article ? article.innerText.slice(0, 3000) : '' });
  }
});
