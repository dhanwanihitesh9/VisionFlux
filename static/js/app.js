// VisionFlux Frontend JavaScript

class VisionFluxApp {
  constructor() {
    this.ws = null;
    this.cameras = [];
    this.alerts = [];
    this.prompts = [];
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;

    this.init();
  }

  init() {
    this.connectWebSocket();
    this.loadDashboardData();
    this.setupEventListeners();

    // Refresh data every 30 seconds
    setInterval(() => this.loadDashboardData(), 30000);
  }

  connectWebSocket() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log("WebSocket connected");
        this.reconnectAttempts = 0;
        this.updateSystemStatus(true);
      };

      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        this.handleWebSocketMessage(data);
      };

      this.ws.onclose = () => {
        console.log("WebSocket disconnected");
        this.updateSystemStatus(false);
        this.attemptReconnect();
      };

      this.ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        this.updateSystemStatus(false);
      };
    } catch (error) {
      console.error("Failed to connect WebSocket:", error);
      this.updateSystemStatus(false);
    }
  }

  attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(
        `Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`
      );
      setTimeout(() => this.connectWebSocket(), 5000 * this.reconnectAttempts);
    }
  }

  handleWebSocketMessage(data) {
    switch (data.type) {
      case "alert":
        this.handleNewAlert(data.data);
        break;
      default:
        console.log("Unknown WebSocket message type:", data.type);
    }
  }

  handleNewAlert(alert) {
    this.alerts.unshift(alert);
    this.updateAlertsDisplay();
    this.showNotification(alert);
  }

  async loadDashboardData() {
    try {
      const response = await fetch("/api/dashboard/status");
      const data = await response.json();

      this.cameras = data.cameras;
      this.alerts = data.recent_alerts;
      this.prompts = data.custom_prompts;

      this.updateCamerasDisplay();
      this.updateAlertsDisplay();
      this.updatePromptsDisplay();
      this.updateSystemStats(data.system);
    } catch (error) {
      console.error("Failed to load dashboard data:", error);
      this.showError("Failed to load dashboard data");
    }
  }

  updateSystemStatus(online) {
    const statusElement = document.getElementById("system-status");
    if (online) {
      statusElement.innerHTML =
        '<i class="fas fa-circle text-success"></i> System Online';
    } else {
      statusElement.innerHTML =
        '<i class="fas fa-circle text-danger"></i> System Offline';
    }
  }

  updateSystemStats(stats) {
    document.getElementById("total-cameras").textContent = stats.total_cameras;
    document.getElementById("total-alerts").textContent = this.alerts.length;
  }

  updateCamerasDisplay() {
    const cameraGrid = document.getElementById("camera-grid");

    if (this.cameras.length === 0) {
      cameraGrid.innerHTML = `
                <div class="col-12">
                    <div class="no-cameras">
                        <i class="fas fa-video-slash fa-3x mb-3"></i>
                        <h5>No cameras configured</h5>
                        <p>Add your first camera to start monitoring</p>
                    </div>
                </div>
            `;
      return;
    }

    cameraGrid.innerHTML = this.cameras
      .map(
        (camera) => `
            <div class="col-lg-4 col-md-6 camera-grid-item">
                <div class="card camera-card">
                    <div class="card-body position-relative">
                        <div class="camera-status status-${camera.status}">
                            ${camera.status.toUpperCase()}
                        </div>
                        <h6 class="card-title">${camera.name}</h6>
                        ${this.renderCameraStream(camera)}
                        <div class="camera-controls">
                            <button class="btn btn-sm btn-success" onclick="app.startCamera('${
                              camera.id
                            }')">
                                <i class="fas fa-play"></i> Start
                            </button>
                            <button class="btn btn-sm btn-warning" onclick="app.stopCamera('${
                              camera.id
                            }')">
                                <i class="fas fa-stop"></i> Stop
                            </button>
                            <button class="btn btn-sm btn-danger" onclick="app.removeCamera('${
                              camera.id
                            }')">
                                <i class="fas fa-trash"></i> Remove
                            </button>
                        </div>
                        ${
                          camera.error_message
                            ? `<div class="text-danger mt-2"><small>${camera.error_message}</small></div>`
                            : ""
                        }
                    </div>
                </div>
            </div>
        `
      )
      .join("");
  }

  renderCameraStream(camera) {
    if (camera.status === "connected") {
      return `<img src="/api/cameras/${camera.id}/stream" class="camera-stream" alt="${camera.name} stream" onerror="this.src='/static/images/no-signal.png'">`;
    } else {
      return `
                <div class="camera-stream d-flex align-items-center justify-content-center bg-dark text-white">
                    <div class="text-center">
                        <i class="fas fa-video-slash fa-2x mb-2"></i>
                        <div>No Signal</div>
                    </div>
                </div>
            `;
    }
  }

  updateAlertsDisplay() {
    const alertsContainer = document.getElementById("recent-alerts");

    if (this.alerts.length === 0) {
      alertsContainer.innerHTML =
        '<div class="text-muted text-center">No recent alerts</div>';
      return;
    }

    alertsContainer.innerHTML = this.alerts
      .slice(0, 10)
      .map(
        (alert) => `
            <div class="alert-item ${
              alert.acknowledged ? "alert-acknowledged" : ""
            }" onclick="app.acknowledgeAlert('${alert.id}')">
                <div class="d-flex justify-content-between">
                    <strong>${alert.message}</strong>
                    <span class="confidence-display">${(
                      alert.confidence * 100
                    ).toFixed(0)}%</span>
                </div>
                <div class="alert-timestamp">${this.formatTimestamp(
                  alert.timestamp
                )}</div>
            </div>
        `
      )
      .join("");
  }

  updatePromptsDisplay() {
    const promptsTable = document.getElementById("prompts-table");

    if (this.prompts.length === 0) {
      promptsTable.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center text-muted">No custom prompts configured</td>
                </tr>
            `;
      return;
    }

    promptsTable.innerHTML = this.prompts
      .map(
        (prompt) => `
            <tr>
                <td>${prompt.name}</td>
                <td>${prompt.prompt}</td>
                <td>${(prompt.confidence_threshold * 100).toFixed(0)}%</td>
                <td>
                    <span class="prompt-status-${
                      prompt.enabled ? "enabled" : "disabled"
                    }">
                        <i class="fas fa-circle"></i> ${
                          prompt.enabled ? "Enabled" : "Disabled"
                        }
                    </span>
                </td>
                <td>
                    <button class="btn btn-sm btn-outline-danger" onclick="app.removePrompt('${
                      prompt.id
                    }')">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `
      )
      .join("");
  }

  setupEventListeners() {
    // Confidence threshold slider
    const confidenceSlider = document.getElementById("confidence-threshold");
    const confidenceValue = document.getElementById("confidence-value");

    if (confidenceSlider && confidenceValue) {
      confidenceSlider.addEventListener("input", (e) => {
        confidenceValue.textContent = e.target.value;
      });
    }
  }

  async addCamera() {
    const name = document.getElementById("camera-name").value;
    const rtspUrl = document.getElementById("rtsp-url").value;

    if (!name || !rtspUrl) {
      this.showError("Please fill in all fields");
      return;
    }

    try {
      const response = await fetch("/api/cameras/", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: `name=${encodeURIComponent(name)}&rtsp_url=${encodeURIComponent(
          rtspUrl
        )}`,
      });

      if (response.ok) {
        const result = await response.json();
        this.showSuccess("Camera added successfully");
        this.closeModal("addCameraModal");
        document.getElementById("add-camera-form").reset();

        // Start the camera automatically
        await this.startCamera(result.camera_id);

        this.loadDashboardData();
      } else {
        throw new Error("Failed to add camera");
      }
    } catch (error) {
      console.error("Error adding camera:", error);
      this.showError("Failed to add camera");
    }
  }

  async addCustomPrompt() {
    const name = document.getElementById("prompt-name").value;
    const prompt = document.getElementById("prompt-text").value;
    const confidenceThreshold = parseFloat(
      document.getElementById("confidence-threshold").value
    );

    if (!name || !prompt) {
      this.showError("Please fill in all fields");
      return;
    }

    try {
      const response = await fetch("/api/prompts/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: name,
          prompt: prompt,
          confidence_threshold: confidenceThreshold,
          enabled: true,
        }),
      });

      if (response.ok) {
        this.showSuccess("Custom prompt added successfully");
        this.closeModal("addPromptModal");
        document.getElementById("add-prompt-form").reset();
        document.getElementById("confidence-value").textContent = "0.7";
        this.loadDashboardData();
      } else {
        throw new Error("Failed to add custom prompt");
      }
    } catch (error) {
      console.error("Error adding custom prompt:", error);
      this.showError("Failed to add custom prompt");
    }
  }

  async startCamera(cameraId) {
    try {
      const response = await fetch(`/api/cameras/${cameraId}/start`, {
        method: "POST",
      });

      if (response.ok) {
        this.showSuccess("Camera started successfully");
        this.loadDashboardData();
      } else {
        throw new Error("Failed to start camera");
      }
    } catch (error) {
      console.error("Error starting camera:", error);
      this.showError("Failed to start camera");
    }
  }

  async stopCamera(cameraId) {
    try {
      const response = await fetch(`/api/cameras/${cameraId}/stop`, {
        method: "POST",
      });

      if (response.ok) {
        this.showSuccess("Camera stopped successfully");
        this.loadDashboardData();
      } else {
        throw new Error("Failed to stop camera");
      }
    } catch (error) {
      console.error("Error stopping camera:", error);
      this.showError("Failed to stop camera");
    }
  }

  async removeCamera(cameraId) {
    if (!confirm("Are you sure you want to remove this camera?")) {
      return;
    }

    try {
      const response = await fetch(`/api/cameras/${cameraId}`, {
        method: "DELETE",
      });

      if (response.ok) {
        this.showSuccess("Camera removed successfully");
        this.loadDashboardData();
      } else {
        throw new Error("Failed to remove camera");
      }
    } catch (error) {
      console.error("Error removing camera:", error);
      this.showError("Failed to remove camera");
    }
  }

  async removePrompt(promptId) {
    if (!confirm("Are you sure you want to remove this custom prompt?")) {
      return;
    }

    try {
      const response = await fetch(`/api/prompts/${promptId}`, {
        method: "DELETE",
      });

      if (response.ok) {
        this.showSuccess("Custom prompt removed successfully");
        this.loadDashboardData();
      } else {
        throw new Error("Failed to remove custom prompt");
      }
    } catch (error) {
      console.error("Error removing custom prompt:", error);
      this.showError("Failed to remove custom prompt");
    }
  }

  async acknowledgeAlert(alertId) {
    try {
      const response = await fetch(`/api/alerts/${alertId}/acknowledge`, {
        method: "POST",
      });

      if (response.ok) {
        // Update local alert state
        const alert = this.alerts.find((a) => a.id === alertId);
        if (alert) {
          alert.acknowledged = true;
        }
        this.updateAlertsDisplay();
      }
    } catch (error) {
      console.error("Error acknowledging alert:", error);
    }
  }

  closeModal(modalId) {
    const modal = bootstrap.Modal.getInstance(document.getElementById(modalId));
    if (modal) {
      modal.hide();
    }
  }

  showNotification(alert) {
    // Show browser notification if permitted
    if (Notification.permission === "granted") {
      new Notification("VisionFlux Alert", {
        body: alert.message,
        icon: "/static/images/logo.png",
      });
    }
  }

  showSuccess(message) {
    this.showToast(message, "success");
  }

  showError(message) {
    this.showToast(message, "danger");
  }

  showToast(message, type) {
    // Create a simple toast notification
    const toast = document.createElement("div");
    toast.className = `alert alert-${type} position-fixed top-0 end-0 m-3`;
    toast.style.zIndex = "9999";
    toast.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <span>${message}</span>
                <button type="button" class="btn-close" onclick="this.parentElement.parentElement.remove()"></button>
            </div>
        `;

    document.body.appendChild(toast);

    // Auto-remove after 5 seconds
    setTimeout(() => {
      if (toast.parentElement) {
        toast.remove();
      }
    }, 5000);
  }

  formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString();
  }
}

// Global functions
function refreshData() {
  app.loadDashboardData();
}

function addCamera() {
  app.addCamera();
}

function addCustomPrompt() {
  app.addCustomPrompt();
}

// Initialize app when DOM is loaded
let app;
document.addEventListener("DOMContentLoaded", () => {
  app = new VisionFluxApp();

  // Request notification permission
  if ("Notification" in window && Notification.permission === "default") {
    Notification.requestPermission();
  }
});
