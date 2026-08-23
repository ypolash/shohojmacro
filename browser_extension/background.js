// Shohoj Browser Companion - Background Service Worker
// Maintains WebSocket bridge with Shohoj Macro desktop app

let socket = null;
let isConnected = false;
const WS_URL = "ws://127.0.0.1:8765";

function connectWebSocket() {
  if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
    return;
  }

  try {
    socket = new WebSocket(WS_URL);

    socket.onopen = () => {
      isConnected = true;
      console.log("[Shohoj Companion] Connected to Desktop Macro Server");
      chrome.storage.local.set({ bridgeStatus: "Connected" });
    };

    socket.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.action === "HIGHLIGHT_ELEMENT") {
          chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            if (tabs[0]) {
              chrome.tabs.sendMessage(tabs[0].id, msg);
            }
          });
        }
      } catch (err) {
        console.error("[Shohoj Companion] Message parse error:", err);
      }
    };

    socket.onclose = () => {
      isConnected = false;
      chrome.storage.local.set({ bridgeStatus: "Disconnected" });
      setTimeout(connectWebSocket, 3000);
    };

    socket.onerror = () => {
      socket.close();
    };
  } catch (err) {
    console.error("[Shohoj Companion] Connection error:", err);
  }
}

// Keep-Alive Alarm (every 25s) to prevent MV3 worker termination
chrome.alarms.create("keepAlive", { periodInMinutes: 0.4 });
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === "keepAlive") {
    if (!isConnected) {
      connectWebSocket();
    } else if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ action: "PING", timestamp: Date.now() }));
    }
  }
});

// Forward picked elements from content script to Desktop App
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "SEND_TO_DESKTOP") {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({
        action: "ELEMENT_PICKED",
        data: request.data
      }));
      sendResponse({ status: "SENT" });
    } else {
      sendResponse({ status: "NOT_CONNECTED" });
    }
  }
});

connectWebSocket();
