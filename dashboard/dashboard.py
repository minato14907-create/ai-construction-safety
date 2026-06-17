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
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0a0e1a;color:#f1f5f9;min-height:100vh}
.topbar{background:#111827;border-bottom:1px solid #1e293b;padding:16px 32px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100}
.topbar h1{font-size:20px;font-weight:700;background:linear-gradient(135deg,#3b82f6,#8b5cf6);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.topbar h1 span{font-weight:300;background:none;-webkit-text-fill-color:#94a3b8;font-size:14px;margin-left:8px}
.topbar .status{display:flex;align-items:center;gap:8px;font-size:13px;color:#94a3b8}
.topbar .dot{width:8px;height:8px;border-radius:50%;background:#22c55e;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
.container{max-width:1400px;margin:0 auto;padding:24px 32px}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:24px}
.stat-card{background:#111827;border:1px solid #1e293b;border-radius:12px;padding:20px}
.stat-card .label{font-size:12px;font-weight:500;color:#94a3b8;text-transform:uppercase;letter-spacing:.5px}
.stat-card .value{font-size:32px;font-weight:800;margin-top:8px;line-height:1}
.stat-card .sub{font-size:12px;color:#94a3b8;margin-top:4px}
.stat-card .vred{color:#ef4444}
.stat-card .vgreen{color:#22c55e}
.stat-card .vblue{color:#3b82f6}
.stat-card .vyellow{color:#f59e0b}
.grid{display:grid;grid-template-columns:1.5fr 1fr;gap:20px;margin-bottom:20px}
.card{background:#111827;border:1px solid #1e293b;border-radius:12px;overflow:hidden}
.card-hd{padding:16px 20px;border-bottom:1px solid #1e293b;display:flex;align-items:center;justify-content:space-between}
.card-hd h2{font-size:14px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;color:#94a3b8}
.card-bd{padding:20px}
.feed-box{background:#000;min-height:350px;display:flex;align-items:center;justify-content:center;overflow:hidden}
.feed-box img{width:100%;display:block}
.feed-off{color:#94a3b8;font-size:14px;text-align:center;padding:40px}
table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:left;padding:10px 12px;color:#94a3b8;font-weight:500;font-size:11px;text-transform:uppercase;letter-spacing:.5px;border-bottom:1px solid #1e293b}
td{padding:10px 12px;border-bottom:1px solid #1e293b}
tr:hover td{background:#1f2937}
.tag{padding:3px 10px;border-radius:20px;font-size:11px;font-weight:500;display:inline-block;background:rgba(239,68,68,.15);color:#ef4444}
.empty{text-align:center;padding:40px;color:#94a3b8;font-size:13px}
.fullw{grid-column:1/-1}
.sm{color:#94a3b8;font-size:12px}
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
<div class="status"><span class="dot"></span><span>Live</span></div>
</div>
<div class="container">
<div class="stats">
<div class="stat-card"><div class="label">Total Persons</div><div class="value vblue" id="totalPersons">0</div><div class="sub">detected</div></div>
<div class="stat-card"><div class="label">Violations</div><div class="value vred" id="totalViolations">0</div><div class="sub">total incidents</div></div>
<div class="stat-card"><div class="label">Compliance</div><div class="value vgreen" id="complianceRate">100%</div><div class="sub">safety rate</div></div>
<div class="stat-card"><div class="label">Watchlist</div><div class="value vyellow" id="watchlist">0</div><div class="sub">active alerts</div></div>
</div>
<div class="grid">
<div class="card">
<div class="card-hd"><h2>Live Camera</h2></div>
<div class="feed-box"><img src="/video_feed" alt="Feed" id="feed"></div>
</div>
<div class="card">
<div class="card-hd"><h2>Violation Summary</h2></div>
<div class="card-bd" id="summary"><div class="empty">Loading...</div></div>
</div>
</div>
<div class="card fullw">
<div class="card-hd"><h2>Violation Log</h2><span class="sm" id="logCount">0 entries</span></div>
<div class="card-bd" id="violations"><div class="empty">No violations recorded</div></div>
</div>
</div>
<script>
function fmt(ts){try{return new Date(ts).toLocaleTimeString()+' '+new Date(ts).toLocaleDateString()}catch(e){return ts}}
function load(){
fetch('/api/summary').then(r=>r.json()).then(d=>{
let t=0,h='<table><tr><th>Type</th><th>Count</th></tr>';
for(const[k,v]of Object.entries(d.summary)){t+=v;h+='<tr><td><span class="tag">'+k+'</span></td><td><strong>'+v+'</strong></td></tr>'}
if(Object.keys(d.summary).length===0)h+='<tr><td colspan="2"><div class="empty">No violations</div></td></tr>';
h+='</table>';document.getElementById('summary').innerHTML=h;document.getElementById('totalViolations').textContent=t;
}).catch(function(){});
fetch('/api/violations').then(r=>r.json()).then(function(d){
document.getElementById('logCount').textContent=d.violations.length+' entries';
var h='<table><tr><th>Time</th><th>Type</th><th>Message</th><th>#</th></tr>';
if(d.violations.length===0){h+='<tr><td colspan="4"><div class="empty">No violations</div></td></tr>'}
else{for(var i=d.violations.length-1;i>=0;i--){var v=d.violations[i];h+='<tr><td class="sm">'+fmt(v.timestamp)+'</td><td><span class="tag">'+v.violation_type+'</span></td><td>'+v.message+'</td><td class="sm">#'+v.frame_number+'</td></tr>'}}
h+='</table>';document.getElementById('violations').innerHTML=h;
}).catch(function(){});
}
load();setInterval(load,3000);
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
            import numpy as np
            def generate():
                while True:
                    if self.frame is not None:
                        ret, buf = cv2.imencode(".jpg", self.frame)
                        if ret:
                            yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buf.tobytes() + b"\r\n")
                    else:
                        img = np.zeros((480, 640, 3), dtype=np.uint8)
                        cv2.putText(img, "No Camera Feed", (150, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                        ret, buf = cv2.imencode(".jpg", img)
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
