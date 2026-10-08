#!/usr/bin/env python3
"""Generate a summary report (Markdown) from the construction demo clip."""

import argparse
import os
import sys
import cv2
from collections import OrderedDict

os.environ["YOLO_VERBOSE"] = "False"

from config import Config, VIOLATION_MESSAGES
from detector.safety_detector import SafetyDetector
from utils.video_utils import VideoStream

LANG_LABELS = {
    "no_hardhat": "ไม่สวมหมวกนิรภัย (no_hardhat)",
    "no_vest": "ไม่สวมเสื้อกั๊กนิรภัย (no_vest)",
    "no_glasses": "ไม่สวมแว่นตานิรภัย (no_glasses)",
}


def main():
    parser = argparse.ArgumentParser(description="Build detection summary report")
    parser.add_argument("--source", default="videos/construction_demo.mp4")
    parser.add_argument("--output", default="construction_report.md")
    parser.add_argument("--conf", type=float, default=0.5)
    args = parser.parse_args()

    Config.CONFIDENCE_THRESHOLD = args.conf

    stream = VideoStream(args.source)
    cap = stream.open()
    fps = stream.get_fps() or 30.0
    total_frames = stream.get_frame_count()
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) if cap else 0
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) if cap else 0
    duration = total_frames / fps

    detector = SafetyDetector()

    violations = OrderedDict()
    frame_persons = []
    violation_frames = set()
    max_persons = 0
    total_persons = 0
    processed = 0

    while True:
        ret, frame = stream.read()
        if not ret:
            break
        frame = VideoStream.resize_frame(frame)
        processed += 1
        detections = detector.detect(frame)
        persons = [d for d in detections if d["label"].lower() == "person"]
        ppe = [d for d in detections if d["label"].lower() != "person"]
        viol = detector.check_ppe_violations(persons, ppe)

        frame_persons.append(len(persons))
        total_persons += len(persons)
        if len(persons) > max_persons:
            max_persons = len(persons)

        for v in viol:
            violation_frames.add(processed)
            for code in v["violations"]:
                rec = violations.setdefault(code, {"count": 0, "first": processed, "last": processed})
                rec["count"] += 1
                rec["last"] = processed

        sys.stdout.write(
            f"\r Frame: {processed}/{total_frames} | Persons: {len(persons)} "
            f"| Violations: {len(viol)}   "
        )
        sys.stdout.flush()
    stream.release()

    clean_frames = total_frames - len(violation_frames)
    compliance = (clean_frames / total_frames * 100) if total_frames else 0.0
    avg_persons = total_persons / processed if processed else 0.0

    segments = []
    start = None
    prev = None
    for f in sorted(violation_frames):
        if start is None:
            start = prev = f
        elif f == prev + 1:
            prev = f
        else:
            segments.append((start, prev))
            start = prev = f
    if start is not None:
        segments.append((start, prev))

    lines = []
    lines.append("# รายงานสรุปผลตรวจจับความปลอดภัยจากคลิปตัวอย่าง")
    lines.append("")
    lines.append(f"- **ไฟล์คลิป:** `{args.source}`")
    lines.append(f"- **ความละเอียด:** {w}x{h} px")
    lines.append(f"- **ระยะเวลา:** {duration:.1f} วินาที")
    lines.append(f"- **เฟรมรวม:** {total_frames} เฟรม ({fps:.0f} fps)")
    lines.append(f"- **เกณฑ์ความมั่นใจ (conf):** {Config.CONFIDENCE_THRESHOLD}")
    lines.append("")

    lines.append("## สถิติภาพรวม")
    lines.append("")
    lines.append("| รายการ | ค่า |")
    lines.append("|--------|-----|")
    lines.append(f"| จำนวนคนที่ตรวจจับได้ (รวมทุกเฟรม) | {total_persons} |")
    lines.append(f"| ค่าเฉลี่ยคนต่อเฟรม | {avg_persons:.2f} |")
    lines.append(f"| จำนวนคนสูงสุดพร้อมกัน | {max_persons} |")
    lines.append(f"| เฟรมที่มีการละเมิด | {len(violation_frames):,} / {total_frames:,} |")
    lines.append(f"| อัตราการปฏิบัติตามกฎ (Compliance) | {compliance:.1f}% |")
    lines.append(f"| จำนวนการละเมิดรวม | {sum(r['count'] for r in violations.values()):,} |")
    lines.append("")

    lines.append("## สรุปการละเมิด PPE แยกตามประเภท")
    lines.append("")
    if violations:
        lines.append("| ประเภทการละเมิด | จำนวนครั้ง | เฟรมแรก | เฟรมสุดท้าย |")
        lines.append("|----------------|-----------|---------|-------------|")
        for code, rec in violations.items():
            lines.append(
                f"| {LANG_LABELS[code]} | {rec['count']:,} | "
                f"{rec['first']} | {rec['last']} |"
            )
    else:
        lines.append("ไม่พบการละเมิด")
    lines.append("")

    lines.append("## ช่วงเวลาที่เกิดการละเมิด (Timeline)")
    lines.append("")
    if segments:
        lines.append("| ช่วงเฟรม | ช่วงเวลา (วินาที) |")
        lines.append("|----------|-------------------|")
        for a, b in segments:
            lines.append(f"| {a} – {b} | {a/fps:.1f} – {b/fps:.1f} |")
    else:
        lines.append("ไม่มีช่วงที่เกิดการละเมิด")
    lines.append("")

    lines.append("## หมายเหตุ")
    lines.append("")
    lines.append(
        "- การตรวจสอบนี้ใช้โมเดล YOLOv8 ทั่วไป (COCO) ตรวจจับเฉพาะตัวคน "
        "ส่วนการประเมิน PPE คำนวณจากบุคคลที่ตรวจพบบนพื้นฐานตำแหน่งกล่อง (bbox)"
    )
    lines.append("- ตัวเลขเกิดจากการรัน 1 รอบของคลิปตัวอย่างเท่านั้น")
    lines.append("")

    report = "\n".join(lines)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n\nรายงานถูกบันทึกที่: {args.output} ({os.path.getsize(args.output):,} bytes)")


if __name__ == "__main__":
    main()