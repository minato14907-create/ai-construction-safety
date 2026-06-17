import json
import threading
from flask import Flask, render_template_string, jsonify
from config import Config, PPE_LABELS
from alert.alert_manager import AlertManager

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Construction Site Safety Auditor</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
               background: #1a1a2e; color: #eee; padding: 20px; }
        h1 { color: #e94560; margin-bottom: 20px; }
        h2 { color: #0f3460; margin: 10px 0; }
        .container { max-width: 1200px; margin: 0 auto; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .card { background: #16213e; border-radius: 10px; padding: 20px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
        .card h2 { color: #e94560; border-bottom: 2px solid #e94560;
                   padding-bottom: 10px; margin-bottom: 15px; }
        .stat { font-size: 2em; color: #0f3460; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #333; }
        th { color: #e94560; }
        .badge { display: inline-block; padding: 3px 8px; border-radius: 5px;
                 font-size: 0.8em; }
        .badge-danger { background: #e94560; color: white; }
        .badge-warning { background: #f5a623; color: black; }
        .status-ok { color: #4ecca3; font-weight: bold; }
        .status-violation { color: #e94560; font-weight: bold; }
        .footer { text-align: center; margin-top: 20px; color: #666; font-size: 0.8em; }
        .img-container { text-align: center; }
        .img-container img { max-width: 100%; border-radius: 8px; }
        @media (max-width: 768px) { .grid { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
    <div class="container">
        <h1> AI Construction Site Safety Auditor</h1>
        <div class="grid">
            <div class="card">
                <h2> Live Feed</h2>
                <div class="img-container">
                    <img src="/video_feed" alt="Live Feed" id="feed">
                </div>
            </div>
            <div class="card">
                <h2> Violation Summary</h2>
                <div id="summary">
                    <p>Loading...</p>
                </div>
            </div>
            <div class="card" style="grid-column: 1 / -1;">
                <h2> Recent Violations</h2>
                <div id="violations">
                    <p>Loading...</p>
                </div>
            </div>
        </div>
        <div class="footer">
            <p>AI Construction Site Safety Auditor - KMITL</p>
        </div>
    </div>
    <script>
        function loadData() {
            fetch('/api/summary')
                .then(r => r.json())
                .then(d => {
                    let html = '<table><tr><th>Type</th><th>Count</th></tr>';
                    for (const [k, v] of Object.entries(d.summary)) {
                        html += `<tr><td>${k}</td><td>${v}</td></tr>`;
                    }
                    if (Object.keys(d.summary).length === 0) {
                        html += '<tr><td colspan="2">No violations</td></tr>';
                    }
                    html += '</table>';
                    document.getElementById('summary').innerHTML = html;
                });
            fetch('/api/violations')
                .then(r => r.json())
                .then(d => {
                    let html = '<table><tr><th>Time</th><th>Type</th><th>Message</th><th>Frame</th></tr>';
                    d.violations.forEach(v => {
                        html += `<tr>
                            <td>${v.timestamp}</td>
                            <td><span class="badge badge-danger">${v.violation_type}</span></td>
                            <td>${v.message}</td>
                            <td>${v.frame_number}</td>
                        </tr>`;
                    });
                    if (d.violations.length === 0) {
                        html += '<tr><td colspan="4">No violations</td></tr>';
                    }
                    html += '</table>';
                    document.getElementById('violations').innerHTML = html;
                });
        }
        loadData();
        setInterval(loadData, 3000);
    </script>
</body>
</html>
"""


class DashboardServer:
    def __init__(self, alert_manager: AlertManager):
        self.alert_mgr = alert_manager
        self.app = Flask(__name__)
        self.frame = None
        self._setup_routes()

    def _setup_routes(self):
        app = self.app

        @app.route("/")
        def index():
            return render_template_string(HTML_TEMPLATE)

        @app.route("/api/summary")
        def api_summary():
            summary = self.alert_mgr.get_violation_summary()
            total = sum(summary.values())
            return jsonify({"summary": summary, "total": total})

        @app.route("/api/violations")
        def api_violations():
            rows = self.alert_mgr.get_recent_violations(limit=50)
            return jsonify({"violations": rows})

        @app.route("/video_feed")
        def video_feed():
            from flask import Response
            def generate():
                import cv2
                while True:
                    if self.frame is not None:
                        ret, buf = cv2.imencode(".jpg", self.frame)
                        if ret:
                            yield (b"--frame\r\n"
                                   b"Content-Type: image/jpeg\r\n\r\n" +
                                   buf.tobytes() + b"\r\n")
            return Response(generate(),
                            mimetype="multipart/x-mixed-replace; boundary=frame")

    def update_frame(self, frame):
        self.frame = frame

    def start(self, host=Config.DASHBOARD_HOST, port=Config.DASHBOARD_PORT):
        threading.Thread(
            target=self.app.run,
            args=(host, port),
            kwargs={"debug": False, "use_reloader": False},
            daemon=True,
        ).start()
        lang = Config.LANGUAGE
        url = f"http://{host}:{port}"
        if lang == "th":
            print(f" แดชบอร์ดเปิดที่: {url}")
        else:
            print(f" Dashboard running at: {url}")
