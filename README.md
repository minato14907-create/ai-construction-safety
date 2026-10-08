# AI Construction Site Safety Auditor

ระบบตรวจจับความปลอดภัยในเขตก่อสร้างอัจฉริยะ (AI Safety Auditor Dashboard)
- AI ตรวจจับคน/การละเมิด PPE ด้วย YOLOv8
- Dashboard แบบเรียลไทม์ พร้อมรายงานสรุปอัตโนมัติ
- ตรวจจับจากคลิปตัวอย่างวนไปเรื่อยๆ โดยสถิตินับใหม่ทุกครั้งที่เปิดหน้าเว็บ

## ลิงก์เว็บ (Hosted)

**URL สาธารณะ (Cloudflare Quick Tunnel):**

```
https://furnishings-mississippi-senior-shakira.trycloudflare.com
```

> หมายเหตุ: Quick tunnel เป็น URL ชั่วคราว — ถ้า restart tunnel/เครื่อง URL จะเปลี่ยน

## วิธีรัน

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Host Dashboard + ตรวจจับจากคลิป
.venv/bin/python index.py --dashboard-only --source videos/construction_demo.mp4 --smooth-fps 15

# สรุปรายงานเต็มคลิป (ไฟล์ construction_report.md)
.venv/bin/python report.py
```

## โครงสร้าง

```
index.py                ตัวรันหลัก (dashboard / stream / loop)
config.py               ค่าตั้งค่า (port, PPE classes, ภาษา)
detector/               YOLO detector + ตรวจ PPE violation
alert/                  AlertManager (log violations)
dashboard/              Flask Dashboard + รายงานเรียลไทม์
report.py               สร้างรายงานสรุปจากคลิป
utils/                  VideoStream utility
```

## หมายเหตุ

- โมเดลเริ่มต้น YOLOv8 (COCO) ตรวจจับตัวคน; การประเมิน PPE คำนวณจากตำแหน่ง bbox
- สถิติและ violations.csv จะรีเซ็ตเมื่อเปิด/รีเฟรชหน้าเว็บ