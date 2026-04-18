from flask import Flask, render_template_string, jsonify
import cv2
import numpy as np
import threading
import time
from datetime import datetime
import csv
import os

app = Flask(__name__)

# --- Shared state ---
state = {
    "score": 50,
    "level": "CLEAR",
    "color": "green",
    "timestamp": "",
    "history": [],
    "alert_count": 0,
}

LOG_FILE = "fog_alerts.csv"

# --- Fog Detection ---
def get_visibility_score(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.Laplacian(gray, cv2.CV_64F).var()
    contrast = gray.std()
    blur_norm = min(blur / 500.0 * 50, 50)
    contrast_norm = min(contrast / 80.0 * 50, 50)
    return round(min(blur_norm + contrast_norm, 100), 1)

def get_fog_level(score):
    if score >= 70:
        return "CLEAR", "green"
    elif score >= 40:
        return "MODERATE FOG", "orange"
    else:
        return "DENSE FOG", "red"

def log_event(score, level):
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), score, level])

# --- Background camera thread ---
def camera_loop():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Camera not found.")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        score = get_visibility_score(frame)
        level, color = get_fog_level(score)
        now = datetime.now().strftime("%H:%M:%S")

        state["score"] = score
        state["level"] = level
        state["color"] = color
        state["timestamp"] = now

        # Keep last 60 readings for graph
        state["history"].append({"time": now, "score": score})
        if len(state["history"]) > 60:
            state["history"].pop(0)

        if score < 40:
            state["alert_count"] += 1

        log_event(score, level)
        time.sleep(1)

    cap.release()

# --- HTML Dashboard ---
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>SmartFog Dashboard</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: Arial, sans-serif; background: #0f1117; color: #eee; padding: 24px; }
    h1 { font-size: 22px; font-weight: 500; margin-bottom: 4px; }
    .subtitle { font-size: 13px; color: #888; margin-bottom: 24px; }
    .grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 24px; }
    .card { background: #1a1d27; border-radius: 12px; padding: 20px; }
    .card-label { font-size: 12px; color: #888; margin-bottom: 8px; }
    .card-value { font-size: 32px; font-weight: 500; }
    .card-value.green { color: #00c864; }
    .card-value.orange { color: #ff9800; }
    .card-value.red { color: #ff3b3b; }
    .chart-card { background: #1a1d27; border-radius: 12px; padding: 20px; margin-bottom: 24px; }
    .chart-title { font-size: 14px; color: #aaa; margin-bottom: 16px; }
    .status-bar { padding: 14px 20px; border-radius: 10px; font-size: 15px; font-weight: 500; margin-bottom: 24px; }
    .status-bar.green { background: #0a2e1a; color: #00c864; border: 1px solid #00c86440; }
    .status-bar.orange { background: #2e1f00; color: #ff9800; border: 1px solid #ff980040; }
    .status-bar.red { background: #2e0000; color: #ff3b3b; border: 1px solid #ff3b3b40; }
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th { text-align: left; color: #888; font-weight: 400; padding: 8px 0; border-bottom: 1px solid #2a2d3a; }
    td { padding: 8px 0; border-bottom: 1px solid #1e2030; }
    .badge { display: inline-block; padding: 2px 10px; border-radius: 20px; font-size: 11px; }
    .badge.green { background: #0a2e1a; color: #00c864; }
    .badge.orange { background: #2e1f00; color: #ff9800; }
    .badge.red { background: #2e0000; color: #ff3b3b; }
  </style>
</head>
<body>
  <h1>SmartFog — Fog Detection Dashboard</h1>
  <p class="subtitle">NH-503 Dharamshala–Pathankot Highway &nbsp;|&nbsp; Live Monitoring</p>

  <div id="status-bar" class="status-bar green">Road status: Fetching...</div>

  <div class="grid">
    <div class="card">
      <div class="card-label">Visibility score</div>
      <div class="card-value" id="score">--</div>
    </div>
    <div class="card">
      <div class="card-label">Fog level</div>
      <div class="card-value" id="level" style="font-size:20px;padding-top:8px;">--</div>
    </div>
    <div class="card">
      <div class="card-label">Total alerts today</div>
      <div class="card-value red" id="alerts">0</div>
    </div>
  </div>

  <div class="chart-card">
    <div class="chart-title">Visibility score — last 60 seconds</div>
    <canvas id="chart" height="80"></canvas>
  </div>

  <div class="chart-card">
    <div class="chart-title">Recent readings</div>
    <table>
      <thead><tr><th>Time</th><th>Score</th><th>Level</th></tr></thead>
      <tbody id="log-body"></tbody>
    </table>
  </div>

  <script>
    const ctx = document.getElementById('chart').getContext('2d');
    const chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: [],
        datasets: [{
          label: 'Visibility %',
          data: [],
          borderColor: '#378ADD',
          backgroundColor: 'rgba(55,138,221,0.1)',
          borderWidth: 2,
          pointRadius: 0,
          tension: 0.4,
          fill: true,
        }]
      },
      options: {
        animation: false,
        scales: {
          y: { min: 0, max: 100, grid: { color: '#2a2d3a' }, ticks: { color: '#888' } },
          x: { grid: { color: '#2a2d3a' }, ticks: { color: '#888', maxTicksLimit: 10 } }
        },
        plugins: { legend: { display: false } }
      }
    });

    function update() {
      fetch('/data')
        .then(r => r.json())
        .then(d => {
          const color = d.color;
          document.getElementById('score').textContent = d.score + '%';
          document.getElementById('score').className = 'card-value ' + color;
          document.getElementById('level').textContent = d.level;
          document.getElementById('level').className = 'card-value ' + color;
          document.getElementById('alerts').textContent = d.alert_count;

          const bar = document.getElementById('status-bar');
          bar.className = 'status-bar ' + color;
          const msgs = { green: 'Road clear — normal driving conditions', orange: 'Moderate fog detected — drive carefully', red: 'DENSE FOG ALERT — slow down to 20 KM/H' };
          bar.textContent = 'Road status: ' + msgs[color];

          chart.data.labels = d.history.map(h => h.time);
          chart.data.datasets[0].data = d.history.map(h => h.score);
          chart.update();

          const tbody = document.getElementById('log-body');
          const recent = d.history.slice(-10).reverse();
          tbody.innerHTML = recent.map(h => {
            const lvl = h.score >= 70 ? 'CLEAR' : h.score >= 40 ? 'MODERATE FOG' : 'DENSE FOG';
            const c = h.score >= 70 ? 'green' : h.score >= 40 ? 'orange' : 'red';
            return '<tr><td>' + h.time + '</td><td>' + h.score + '%</td><td><span class="badge ' + c + '">' + lvl + '</span></td></tr>';
          }).join('');
        });
    }

    setInterval(update, 1000);
    update();
  </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(DASHBOARD_HTML)

@app.route("/data")
def data():
    return jsonify({
        "score": state["score"],
        "level": state["level"],
        "color": state["color"],
        "timestamp": state["timestamp"],
        "history": state["history"],
        "alert_count": state["alert_count"],
    })

if __name__ == "__main__":
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", newline="") as f:
            csv.writer(f).writerow(["Timestamp", "Score", "Level"])

    print("SmartFog Dashboard")
    print("==================")
    print("Starting camera...")
    t = threading.Thread(target=camera_loop, daemon=True)
    t.start()
    time.sleep(2)
    print("Opening dashboard at http://127.0.0.1:5000")
    print("Press Ctrl+C to stop")
    app.run(debug=False)