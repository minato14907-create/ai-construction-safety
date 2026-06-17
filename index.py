#!/usr/bin/env python3
"""
AI Construction Site Safety Auditor
ระบบตรวจจับความปลอดภัยในเขตก่อสร้างอัจฉริยะ

Usage:
  python index.py                          # Webcam + Dashboard
  python index.py --source video.mp4       # Video file
  python index.py --source 0 --lang th     # Webcam + Thai
  python index.py --source photo.jpg --image  # Single image
  python index.py --dashboard-only         # Dashboard only (no detection)
"""

import argparse
import sys
import os

os.environ["YOLO_VERBOSE"] = "False"

from config import Config
from detector.safety_detector import SafetyDetector
from utils.video_utils import VideoStream
from alert.alert_manager import AlertManager
from dashboard.dashboard import DashboardServer


def parse_args():
    parser = argparse.ArgumentParser(
        description="AI Construction Site Safety Auditor"
    )
    parser.add_argument("--source", type=str, default=None,
                        help="Source: camera index (0), video file, or image")
    parser.add_argument("--image", action="store_true",
                        help="Process single image instead of stream")
    parser.add_argument("--lang", type=str, choices=["th", "en"], default="en",
                        help="Language (th/en)")
    parser.add_argument("--conf", type=float, default=0.5,
                        help="Confidence threshold")
    parser.add_argument("--dashboard-only", action="store_true",
                        help="Run dashboard only")
    parser.add_argument("--no-display", action="store_true",
                        help="Don't show display window")
    parser.add_argument("--no-dashboard", action="store_true",
                        help="Don't start dashboard")
    parser.add_argument("--save", action="store_true",
                        help="Save output video")
    return parser.parse_args()


def process_image(detector, alert_mgr, source_path):
    import cv2
    frame = cv2.imread(source_path)
    if frame is None:
        print(f" Cannot read image: {source_path}")
        return
    frame = VideoStream.resize_frame(frame)
    detections = detector.detect(frame)
    persons = [d for d in detections if d["label"].lower() == "person"]
    ppe_items = [d for d in detections if d["label"].lower() != "person"]
    violations = detector.check_ppe_violations(persons, ppe_items)
    alert_mgr.log_violations(violations)
    frame = detector.draw_detections(frame, detections, violations)
    frame = detector.draw_violation_count(frame, len(violations))
    cv2.imshow("AI Safety Auditor", frame)
    print(f" Detected {len(persons)} person(s), {len(violations)} violation(s)")
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def process_stream(detector, alert_mgr, source, no_display, no_dashboard):
    import cv2
    stream = VideoStream(source)
    cap = stream.open()
    fps = stream.get_fps()
    total_frames = stream.get_frame_count()
    frame_number = 0
    dashboard = None
    if not no_dashboard:
        dashboard = DashboardServer(alert_mgr)
        dashboard.start()
    out = None
    if hasattr(args, "save") and args.save and not source == 0:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter("output_safety.mp4", fourcc, fps or 30,
                              (Config.FRAME_WIDTH, Config.FRAME_HEIGHT))
    while True:
        ret, frame = stream.read()
        if not ret:
            break
        frame = VideoStream.resize_frame(frame)
        frame_number += 1
        detections = detector.detect(frame)
        persons = [d for d in detections if d["label"].lower() == "person"]
        ppe_items = [d for d in detections if d["label"].lower() != "person"]
        violations = detector.check_ppe_violations(persons, ppe_items)
        alert_mgr.log_violations(violations, frame_number)
        frame = detector.draw_detections(frame, detections, violations)
        frame = detector.draw_violation_count(frame, len(violations))
        if dashboard:
            dashboard.update_frame(frame)
        if out:
            out.write(frame)
        if not no_display:
            lang = Config.LANGUAGE
            title = "AI Construction Site Safety Auditor" if lang == "en" else "ระบบตรวจจับความปลอดภัยในเขตก่อสร้างอัจฉริยะ"
            cv2.imshow(title, frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        progress = ""
        if total_frames > 0:
            pct = (frame_number / total_frames) * 100
            progress = f" [{pct:.0f}%]"
        sys.stdout.write(f"\r Frame: {frame_number}{progress} | "
                         f"Persons: {len(persons)} | Violations: {len(violations)}   ")
        sys.stdout.flush()
    stream.release()
    if out:
        out.release()
    if not no_display:
        cv2.destroyAllWindows()
    print("\n Done.")


def main():
    global args
    args = parse_args()
    Config.LANGUAGE = args.lang
    Config.CONFIDENCE_THRESHOLD = args.conf
    source = args.source
    if source is not None and source.isdigit():
        source = int(source)
    alert_mgr = AlertManager()
    lang = Config.LANGUAGE
    if lang == "th":
        print(" AI Construction Site Safety Auditor")
        print("=" * 50)
    else:
        print("=" * 50)
        print(" AI Construction Site Safety Auditor")
        print("=" * 50)
    if args.dashboard_only:
        dashboard = DashboardServer(alert_mgr)
        print(" Dashboard-only mode")
        print(" Open http://localhost:5050 in your browser")
        dashboard.start(block=True)
        return
    detector = SafetyDetector()
    if args.image:
        if source is None:
            print("Error: --image requires --source <path>")
            sys.exit(1)
        process_image(detector, alert_mgr, source)
    else:
        process_stream(
            detector, alert_mgr,
            source if source is not None else Config.SOURCE,
            args.no_display, args.no_dashboard
        )


if __name__ == "__main__":
    main()
