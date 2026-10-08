import threading
import time
import os
import datetime
from flask import Flask, jsonify, Response
from config import Config, VIOLATION_MESSAGES
from alert.alert_manager import AlertManager

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
.topbar a.btn{color:#94a3b8;text-decoration:none;border:1px solid #1e293b;padding:6px 12px;border-radius:6px;font-size:12px;margin-left:10px;transition:.2s}
.topbar a.btn:hover{color:#f1f5f9;border-color:#3b82f6}
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
#reportBox{white-space:pre-wrap;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px;line-height:1.6;max-height:360px;overflow:auto}
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
<div class="status"><span class="dot"></span><span>Live</span><a class="btn" href="/api/report" download="construction_report.md">ดาวน์โหลดรายงาน (.md)</a></div>
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
<div class="feed-box"><img src="/api/frame" alt="Feed" id="feed"></div>
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
<div class="card fullw">
<div class="card-hd"><h2>Analysis Report <span class="sm">(อัพเดตแบบเรียลไทม์)</span></h2><a class="btn" href="/api/report" download="construction_report.md">ดาวน์โหลด .md</a></div>
<div class="card-bd" id="reportBox">Loading...</div>
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
document.getElementById('totalPersons').textContent=d.persons||0;
document.getElementById('complianceRate').textContent=(typeof d.compliance==='number'?d.compliance:100)+'%';
}).catch(function(){});
fetch('/api/violations').then(r=>r.json()).then(function(d){
document.getElementById('logCount').textContent=d.violations.length+' entries';
var h='<table><tr><th>Time</th><th>Type</th><th>Message</th><th>#</th></tr>';
if(d.violations.length===0){h+='<tr><td colspan="4"><div class="empty">No violations</div></td></tr>'}
else{for(var i=0;i<d.violations.length;i++){var v=d.violations[i];h+='<tr><td class="sm">'+fmt(v.timestamp)+'</td><td><span class="tag">'+v.violation_type+'</span></td><td>'+v.message+'</td><td class="sm">#'+v.frame_number+'</td></tr>'}}
h+='</table>';document.getElementById('violations').innerHTML=h;
}).catch(function(){});
fetch('/api/report').then(r=>r.text()).then(function(t){
document.getElementById('reportBox').textContent=t;
}).catch(function(){});
}
function refresh(){
load();
document.getElementById('feed').src='/api/frame?_t='+Date.now();
}
load();setInterval(refresh,3000);
setInterval(function(){document.getElementById('feed').src='/api/frame?_t='+Date.now()},200);
</script>
</body>
</html>"""


def violation_label(code, lang=None):
    lang = lang or Config.LANGUAGE
    return VIOLATION_MESSAGES.get(code, {}).get(lang, code)


def build_report_text(source, fps, w, h, conf, stats):
    processed = stats["frame_count"]
    duration = processed / fps if fps else 0.0
    persons_total = stats["persons_total"]
    avg = persons_total / processed if processed else 0.0
    clean = processed - stats["frames_with_violation"]
    compliance = clean / processed * 100 if processed else 100.0
    counts = stats["violation_counts"]
    total_violations = sum(counts.values())

    lines = []
    lines.append("# รายงานสรุปผลตรวจจับความปลอดภัย (เรียลไทม์)")
    lines.append("")
    lines.append(f"- **ไฟล์คลิป:** `{source}`")
    lines.append(f"- **ความละเอียด:** {w}x{h} px" if w and h else "- **ความละเอียด:** -")
    lines.append(f"- **เฟรมที่ประมวลผลแล้ว:** {processed:,} เฟรม ({duration:.1f} วินาที)")
    lines.append(f"- **เกณฑ์ความมั่นใจ (conf):** {conf}")
    lines.append(f"- **เริ่มนับเมื่อ:** {stats['started_at']}")
    lines.append("")

    lines.append("## สถิติภาพรวม")
    lines.append("")
    lines.append("| รายการ | ค่า |")
    lines.append("|--------|-----|")
    lines.append(f"| จำนวนคนที่ตรวจจับได้ (รวม) | {persons_total:,} |")
    lines.append(f"| ค่าเฉลี่ยคนต่อเฟรม | {avg:.2f} |")
    lines.append(f"| จำนวนคนสูงสุดพร้อมกัน | {stats['persons_max']} |")
    lines.append(f"| เฟรมที่มีการละเมิด | {stats['frames_with_violation']:,} / {processed:,} |")
    lines.append(f"| อัตราการปฏิบัติตามกฎ (Compliance) | {compliance:.1f}% |")
    lines.append(f"| จำนวนการละเมิดรวม | {total_violations:,} |")
    lines.append("")

    lines.append("## สรุปการละเมิด PPE แยกตามประเภท")
    lines.append("")
    if counts:
        lines.append("| ประเภทการละเมิด | จำนวนครั้ง |")
        lines.append("|----------------|-----------|")
        for label, count in counts.items():
            lines.append(f"| {label} | {count:,} |")
    else:
        lines.append("ยังไม่พบการละเมิด")
    lines.append("")

    lines.append("## กิจกรรมล่าสุด")
    lines.append("")
    recent = stats["recent"][-20:]
    if recent:
        lines.append("| เวลา | ประเภท | เฟรม |")
        lines.append("|------|--------|------|")
        for r in recent:
            lines.append(f"| {r['timestamp']} | {r['violation_type']} | #{r['frame_number']} |")
    else:
        lines.append("ยังไม่มีข้อมูล")
    lines.append("")

    lines.append("## หมายเหตุ")
    lines.append("")
    lines.append(
        "- สถิติจะนับเริ่มต้นใหม่ทุกครั้งที่เปิดหรือรีเฟรชหน้าเว็บ (http://localhost:5050)"
    )
    lines.append(
        "- ใช้โมเดล YOLOv8 ทั่วไป (COCO) ตรวจจับตัวคน และประเมิน PPE จากตำแหน่งกล่อง (bbox)"
    )
    lines.append("")
    return "\n".join(lines)


class DashboardServer:
    def __init__(self, alert_manager: AlertManager, source=None, smooth_fps=0.0):
        self.alert_mgr = alert_manager
        self.source = source
        self.smooth_fps = smooth_fps
        self.app = Flask(__name__)
        self._lock = threading.Lock()
        self._epoch = 0
        self._frame_jpeg = None
        self._fps = 30.0
        self._w = 0
        self._h = 0
        self.report_file = "construction_report.md"
        self._stats = self._new_stats()
        self._setup_routes()
        if source is not None:
            threading.Thread(target=self._detection_loop, daemon=True).start()

    def _new_stats(self):
        return {
            "started_at": None,
            "frame_count": 0,
            "persons_total": 0,
            "persons_max": 0,
            "frames_with_violation": 0,
            "violation_counts": {},
            "recent": [],
        }

    def _reset_stats(self):
        with self._lock:
            self._stats = self._new_stats()
            self._stats["started_at"] = datetime.datetime.now().isoformat(timespec="seconds")
        self.alert_mgr.reset_log()
        self._write_report()

    def _bump_epoch(self):
        with self._lock:
            self._epoch += 1

    def _compliance(self):
        st = self._stats
        if not st["frame_count"]:
            return 100.0
        clean = st["frame_count"] - st["frames_with_violation"]
        return round(clean / st["frame_count"] * 100, 1)

    def _detection_loop(self):
        import cv2
        from detector.safety_detector import SafetyDetector
        from utils.video_utils import VideoStream

        detector = SafetyDetector()
        self._detector = detector
        stream = None
        last_epoch = None
        target_dt = 1.0 / self.smooth_fps if self.smooth_fps > 0 else 0
        t0 = time.time()
        while True:
            if target_dt:
                elapsed = time.time() - t0
                if elapsed < target_dt:
                    time.sleep(target_dt - elapsed)
                t0 = time.time()
            with self._lock:
                epoch = self._epoch
            if epoch != last_epoch:
                last_epoch = epoch
                if stream is not None:
                    stream.release()
                    stream = None
                self._reset_stats()
            if stream is None:
                stream = VideoStream(self.source)
                stream.open()
                self._fps = stream.get_fps() or 30.0
            ret, frame = stream.read()
            if not ret:
                stream.release()
                stream = None
                continue
            frame = VideoStream.resize_frame(frame)
            self._h, self._w = frame.shape[:2]
            detections = detector.detect(frame)
            persons = [d for d in detections if d["label"].lower() == "person"]
            ppe_items = [d for d in detections if d["label"].lower() != "person"]
            violations = detector.check_ppe_violations(persons, ppe_items)
            frame = detector.draw_detections(frame, detections, violations)
            frame = detector.draw_violation_count(frame, len(violations))
            self._record_frame(frame, persons, violations)
            if self._stats["frame_count"] % 30 == 0:
                self._write_report()

    def _record_frame(self, frame, persons, violations):
        import cv2
        with self._lock:
            st = self._stats
            st["frame_count"] += 1
            st["persons_total"] += len(persons)
            if len(persons) > st["persons_max"]:
                st["persons_max"] = len(persons)
            if violations:
                st["frames_with_violation"] += 1
            for v in violations:
                for code in v["violations"]:
                    label = violation_label(code)
                    st["violation_counts"][label] = st["violation_counts"].get(label, 0) + 1
                    st["recent"].append({
                        "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
                        "violation_type": label,
                        "message": label,
                        "frame_number": st["frame_count"],
                    })
            if len(st["recent"]) > 200:
                st["recent"] = st["recent"][-200:]
        ret, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if ret:
            with self._lock:
                self._frame_jpeg = buf.tobytes()

    def _setup_routes(self):
        @self.app.route("/")
        def index():
            self._bump_epoch()
            return HTML

        @self.app.route("/api/summary")
        def api_summary():
            st = self._stats
            return jsonify({
                "summary": st["violation_counts"],
                "total": sum(st["violation_counts"].values()),
                "persons": st["persons_total"],
                "max_persons": st["persons_max"],
                "compliance": self._compliance(),
            })

        @self.app.route("/api/violations")
        def api_violations():
            return jsonify({"violations": list(reversed(self._stats["recent"]))})

        @self.app.route("/api/frame")
        def api_frame():
            import cv2
            import numpy as np
            jpeg = self._frame_jpeg
            if jpeg is None:
                img = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(img, "No Camera Feed", (130, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 100, 100), 2)
                ret, buf = cv2.imencode(".jpg", img)
                jpeg = buf.tobytes()
            return Response(jpeg, mimetype="image/jpeg")

        @self.app.route("/api/report")
        def api_report():
            self._write_report()
            if not os.path.exists(self.report_file):
                return Response("", status=404)
            with open(self.report_file, encoding="utf-8") as f:
                text = f.read()
            resp = Response(text, mimetype="text/markdown; charset=utf-8")
            resp.headers["Content-Disposition"] = 'attachment; filename="construction_report.md"'
            return resp

    def update_frame(self, frame):
        import cv2
        ret, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if ret:
            self._frame_jpeg = buf.tobytes()

    def _write_report(self):
        try:
            with self._lock:
                st = {
                    "frame_count": self._stats["frame_count"],
                    "persons_total": self._stats["persons_total"],
                    "persons_max": self._stats["persons_max"],
                    "frames_with_violation": self._stats["frames_with_violation"],
                    "violation_counts": dict(self._stats["violation_counts"]),
                    "recent": list(self._stats["recent"]),
                    "started_at": self._stats["started_at"],
                }
            text = build_report_text(
                self.source, self._fps, self._w, self._h,
                Config.CONFIDENCE_THRESHOLD, st,
            )
            tmp = self.report_file + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(text)
            os.replace(tmp, self.report_file)
        except Exception:
            pass

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