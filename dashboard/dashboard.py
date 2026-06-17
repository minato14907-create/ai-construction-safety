import threading
from flask import Flask, jsonify, Response, send_from_directory
from config import Config
from alert.alert_manager import AlertManager
import os

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Construction Site Safety Auditor</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root {
  --bg: #0a0e1a;
  --card: #111827;
  --card2: #1f2937;
  --primary: #3b82f6;
  --danger: #ef4444;
  --success: #22c55e;
  --warning: #f59e0b;
  --text: #f1f5f9;
  --text2: #94a3b8;
  --border: #1e293b;
}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',sans-serif;background:var(--bg);color:var(--text);min-height:100vh}
.topbar{background:var(--card);border-bottom:1px solid var(--border);padding:16px 32px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100}
.topbar h1{font-size:20px;font-weight:700;background:linear-gradient(135deg,#3b82f6,#8b5cf6);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.topbar h1 span{font-weight:300;background:none;-webkit-text-fill-color:var(--text2);font-size:14px;margin-left:8px}
.topbar .status{display:flex;align-items:center;gap:8px;font-size:13px;color:var(--text2)}
.topbar .dot{width:8px;height:8px;border-radius:50%;background:var(--success);animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
.container{max-width:1400px;margin:0 auto;padding:24px 32px}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:24px}
.stat-card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:20px;transition:transform .2s}
.stat-card:hover{transform:translateY(-2px)}
.stat-card .label{font-size:12px;font-weight:500;color:var(--text2);text-transform:uppercase;letter-spacing:.5px}
.stat-card .value{font-size:32px;font-weight:800;margin-top:8px;line-height:1}
.stat-card .sub{font-size:12px;color:var(--text2);margin-top:4px}
.stat-card.red .value{color:var(--danger)}
.stat-card.green .value{color:var(--success)}
.stat-card.blue .value{color:var(--primary)}
.stat-card.yellow .value{color:var(--warning)}
.grid{display:grid;grid-template-columns:1.5fr 1fr;gap:20px;margin-bottom:20px}
.card{background:var(--card);border:1px solid var(--border);border-radius:12px;overflow:hidden}
.card-header{padding:16px 20px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between}
.card-header h2{font-size:14px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;color:var(--text2)}
.card-body{padding:20px}
.feed-container{background:#000;min-height:400px;display:flex;align-items:center;justify-content:center;position:relative;overflow:hidden}
.feed-container img{width:100%;display:block}
.feed-placeholder{color:var(--text2);font-size:14px;text-align:center;padding:40px}
.feed-placeholder .icon{font-size:48px;margin-bottom:12px;opacity:.3}
table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:left;padding:10px 12px;color:var(--text2);font-weight:500;font-size:11px;text-transform:uppercase;letter-spacing:.5px;border-bottom:1px solid var(--border)}
td{padding:10px 12px;border-bottom:1px solid var(--border);color:var(--text)}
tr:hover td{background:var(--card2)}
.badge{padding:3px 10px;border-radius:20px;font-size:11px;font-weight:500;display:inline-block}
.badge-red{background:rgba(239,68,68,.15);color:var(--danger)}
.badge-yellow{background:rgba(245,158,11,.15);color:var(--warning)}
.badge-blue{background:rgba(59,130,246,.15);color:var(--primary)}
.empty{text-align:center;padding:40px;color:var(--text2);font-size:13px}
.full{grid-column:1/-1}
@media(max-width:900px){
  .stats{grid-template-columns:repeat(2,1fr)}
  .grid{grid-template-columns:1fr}
  .container{padding:16px}
  .topbar{padding:12px 16px}
}
</style>
</head>
<body>
<div class="topbar">
  <h1>Safety Auditor <span>| Construction Site AI</span></h1>
  <div class="status">
    <span class="dot"></span>
    <span>Live</span>
  </div>
</div>
<div class="container">
  <div class="stats" id="stats">
    <div class="stat-card blue"><div class="label">Total Persons</div><div class="value" id="totalPersons">0</div><div class="sub">detected</div></div>
    <div class="stat-card red"><div class="label">Violations</div><div class="value" id="totalViolations">0</div><div class="sub">total incidents</div></div>
    <div class="stat-card green"><div class="label">Compliance</div><div class="value" id="complianceRate">100<span style="font-size:18px">%</span></div><div class="sub">safety rate</div></div>
    <div class="stat-card yellow"><div class="label">Watchlist</div><div class="value" id="watchlist">0</div><div class="sub">active alerts</div></div>
  </div>
  <div class="grid">
    <div class="card">
      <div class="card-header"><h2>Live Camera Feed</h2></div>
      <div class="feed-container" id="feedContainer">
        <div class="feed-placeholder" id="feedPlaceholder">
          <div class="icon">&#x1F4F7;</div>
          <p>Waiting for camera feed...</p>
        </div>
        <img src="/video_feed" alt="Live Feed" id="feed" style="display:none" onload="document.getElementById('feedPlaceholder').style.display='none';this.style.display='block'">
      </div>
    </div>
    <div class="card">
      <div class="card-header"><h2>Violation Summary</h2></div>
      <div class="card-body" id="summary"><div class="empty">Loading...</div></div>
    </div>
  </div>
  <div class="card full">
    <div class="card-header"><h2>Violation Log</h2><span style="font-size:12px;color:var(--text2)" id="logCount">0 entries</span></div>
    <div class="card-body" id="violations"><div class="empty">No violations recorded</div></div>
  </div>
</div>
<script>
function fmtTime(ts){
  try{const d=new Date(ts);return d.toLocaleTimeString()+' '+d.toLocaleDateString()}catch(e){return ts}
}
function loadData(){
fetch('/api/summary').then(r=>r.json()).then(d=>{
  let total=0;let html='<table><tr><th>Type</th><th>Count</th></tr>';
  for(const[k,v]of Object.entries(d.summary)){total+=v;html+=`<tr><td><span class="badge badge-red">${k}</span></td><td><strong>${v}</strong></td></tr>`}
  if(Object.keys(d.summary).length===0)html+='<tr><td colspan="2"><div class="empty">All clear - no violations</div></td></tr>';
  html+='</table>';document.getElementById('summary').innerHTML=html;
  document.getElementById('totalViolations').textContent=total;
}).catch(()=>{});
fetch('/api/violations').then(r=>r.json()).then(d=>{
  document.getElementById('logCount').textContent=d.violations.length+' entries';
  let html='<table><tr><th>Time</th><th>Type</th><th>Message</th><th>Frame</th></tr>';
  if(d.violations.length===0){html+='<tr><td colspan="4"><div class="empty">No violations recorded</div></td></tr>'}
  else{d.violations.slice().reverse().forEach(v=>{
    html+=`<tr><td style="font-size:12px;color:var(--text2)">${fmtTime(v.timestamp)}</td><td><span class="badge badge-red">${v.violation_type}</span></td><td>${v.message}</td><td style="color:var(--text2)">#${v.frame_number}</td></tr>`})}
  html+='</table>';document.getElementById('violations').innerHTML=html;
}).catch(()=>{});
}
loadData();setInterval(loadData,3000);
</script>
</body>
</html>"""


class DashboardServer:
    def __init__(self, alert_manager: AlertManager):
        self.alert_mgr = alert_manager
        self.app = Flask(__name__)
        self.frame = None
        self._setup_routes()

    def _setup_routes(self):
        @self.app.route("/")
        def index():
            return HTML

        @self.app.route("/api/summary")
        def api_summary():
            summary = self.alert_mgr.get_violation_summary()
            return jsonify({"summary": summary, "total": sum(summary.values())})

        @self.app.route("/api/violations")
        def api_violations():
            return jsonify({"violations": self.alert_mgr.get_recent_violations(100)})

        @self.app.route("/video_feed")
        def video_feed():
            import cv2
            def generate():
                while True:
                    if self.frame is not None:
                        ret, buf = cv2.imencode(".jpg", self.frame)
                        if ret:
                            yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buf.tobytes() + b"\r\n")
            return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")

    def update_frame(self, frame):
        self.frame = frame

    def start(self, block=False):
        host = Config.DASHBOARD_HOST
        port = Config.DASHBOARD_PORT
        print(f" Dashboard: http://{host}:{port}")
        if block:
            self.app.run(host=host, port=port, debug=False, use_reloader=False)
        else:
            t = threading.Thread(target=self.app.run, args=(host, port),
                                 kwargs={"debug": False, "use_reloader": False},
                                 daemon=True)
            t.start()
