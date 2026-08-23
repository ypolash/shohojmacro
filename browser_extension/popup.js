// Popup controller for Shohoj Browser Companion

document.addEventListener("DOMContentLoaded", () => {
  const statusBadge = document.getElementById("statusBadge");
  const inspectBtn = document.getElementById("inspectBtn");

  function updateStatus() {
    chrome.storage.local.get(["bridgeStatus"], (result) => {
      const status = result.bridgeStatus || "Disconnected";
      statusBadge.textContent = status;
      if (status === "Connected") {
        statusBadge.className = "badge connected";
      } else {
        statusBadge.className = "badge disconnected";
      }
    });
  }

  updateStatus();
  setInterval(updateStatus, 1500);

  inspectBtn.addEventListener("click", () => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs[0]) {
        chrome.tabs.sendMessage(tabs[0].id, { action: "START_ELEMENT_INSPECTOR" }, (res) => {
          window.close();
        });
      }
    });
  });
});
