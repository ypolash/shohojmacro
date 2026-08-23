// Shohoj Browser Companion - Stealth Content Script
// Inspects DOM elements and converts bounding rects to OS screen coordinates

let isInspectorActive = false;
let highlightBox = null;

function createHighlightBox() {
  if (highlightBox) return;
  highlightBox = document.createElement("div");
  highlightBox.id = "__shohoj_highlight_box__";
  highlightBox.style.position = "fixed";
  highlightBox.style.pointerEvents = "none";
  highlightBox.style.zIndex = "2147483647";
  highlightBox.style.border = "2px solid #00F0FF";
  highlightBox.style.borderRadius = "4px";
  highlightBox.style.backgroundColor = "rgba(0, 240, 255, 0.15)";
  highlightBox.style.boxShadow = "0 0 12px rgba(0, 240, 255, 0.5)";
  highlightBox.style.transition = "all 0.08s ease-out";
  highlightBox.style.display = "none";
  document.body.appendChild(highlightBox);
}

function getCssSelector(el) {
  if (el.id) return `#${el.id}`;
  if (el.className && typeof el.className === "string") {
    const classes = el.className.trim().split(/\s+/).filter(c => !c.startsWith("__")).slice(0, 2).join(".");
    if (classes) return `${el.tagName.toLowerCase()}.${classes}`;
  }
  return el.tagName.toLowerCase();
}

function onMouseMove(e) {
  if (!isInspectorActive) return;
  const target = document.elementFromPoint(e.clientX, e.clientY);
  if (!target || target.id === "__shohoj_highlight_box__") return;

  createHighlightBox();
  const rect = target.getBoundingClientRect();
  highlightBox.style.display = "block";
  highlightBox.style.left = `${rect.left}px`;
  highlightBox.style.top = `${rect.top}px`;
  highlightBox.style.width = `${rect.width}px`;
  highlightBox.style.height = `${rect.height}px`;
}

function onClick(e) {
  if (!isInspectorActive) return;
  e.preventDefault();
  e.stopPropagation();

  const target = document.elementFromPoint(e.clientX, e.clientY);
  if (!target) return;

  const rect = target.getBoundingClientRect();
  const screenX = Math.round(window.screenX + (window.outerWidth - window.innerWidth) + rect.left + rect.width / 2);
  const screenY = Math.round(window.screenY + (window.outerHeight - window.innerHeight) + rect.top + rect.height / 2);

  const payload = {
    tagName: target.tagName,
    cssSelector: getCssSelector(target),
    textContent: (target.innerText || target.value || "").slice(0, 30),
    screenX: screenX,
    screenY: screenY,
    width: Math.round(rect.width),
    height: Math.round(rect.height),
    url: window.location.href,
    title: document.title
  };

  chrome.runtime.sendMessage({ action: "SEND_TO_DESKTOP", data: payload });

  // Disable inspector after pick
  isInspectorActive = false;
  if (highlightBox) highlightBox.style.display = "none";
  window.removeEventListener("mousemove", onMouseMove, true);
  window.removeEventListener("click", onClick, true);
}

// Listen for messages from background/popup
chrome.runtime.onMessage.addListener((req, sender, sendResponse) => {
  if (req.action === "START_ELEMENT_INSPECTOR") {
    isInspectorActive = true;
    createHighlightBox();
    window.addEventListener("mousemove", onMouseMove, true);
    window.addEventListener("click", onClick, true);
    sendResponse({ status: "INSPECTOR_ACTIVE" });
  } else if (req.action === "STOP_ELEMENT_INSPECTOR") {
    isInspectorActive = false;
    if (highlightBox) highlightBox.style.display = "none";
    window.removeEventListener("mousemove", onMouseMove, true);
    window.removeEventListener("click", onClick, true);
    sendResponse({ status: "INSPECTOR_INACTIVE" });
  }
});
