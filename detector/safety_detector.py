import cv2
import numpy as np
from ultralytics import YOLO
from config import Config, PPE_LABELS, VIOLATION_MESSAGES


class SafetyDetector:
    def __init__(self, model_path: str = Config.MODEL_PATH):
        self.model = YOLO(model_path)
        self.lang = Config.LANGUAGE

    def detect(self, frame: np.ndarray):
        results = self.model(frame, conf=Config.CONFIDENCE_THRESHOLD)[0]
        detections = []
        for box in results.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
            cls_id = int(box.cls[0])
            label = self.model.names[cls_id]
            detections.append({
                "bbox": (x1, y1, x2, y2),
                "confidence": conf,
                "class_id": cls_id,
                "label": label,
            })
        return detections

    @staticmethod
    def check_ppe_violations(persons_detected: list, ppe_detected: list):
        violations = []
        for person in persons_detected:
            px1, py1, px2, py2 = person["bbox"]
            person_violations = []
            has_hat = False
            has_vest = False
            has_glasses = False
            for ppe in ppe_detected:
                bx1, by1, bx2, by2 = ppe["bbox"]
                cx = (bx1 + bx2) / 2
                cy = (by1 + by2) / 2
                if px1 <= cx <= px2 and py1 <= cy <= py2:
                    label = ppe["label"].lower()
                    if "hat" in label or "helmet" in label:
                        has_hat = True
                    elif "vest" in label:
                        has_vest = True
                    elif "glass" in label:
                        has_glasses = True
            if not has_hat:
                person_violations.append("no_hardhat")
            if not has_vest:
                person_violations.append("no_vest")
            if not has_glasses:
                person_violations.append("no_glasses")
            if person_violations:
                violations.append({
                    "person_bbox": person["bbox"],
                    "violations": person_violations,
                })
        return violations

    @staticmethod
    def draw_detections(frame: np.ndarray, detections: list, violations: list):
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            label = det["label"]
            conf = det["confidence"]
            is_person = label.lower() == "person"
            color = (0, 255, 0)
            if is_person:
                is_violating = any(
                    v["person_bbox"] == det["bbox"] for v in violations
                )
                if is_violating:
                    color = (0, 0, 255)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            text = f"{label} {conf:.2f}"
            cv2.putText(frame, text, (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        for v in violations:
            x1, y1, x2, y2 = v["person_bbox"]
            lang = Config.LANGUAGE
            msgs = [VIOLATION_MESSAGES[v_code][lang] for v_code in v["violations"]]
            for i, msg in enumerate(msgs):
                cv2.putText(frame, msg, (x1, y2 + 15 + i * 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        return frame

    @staticmethod
    def draw_ppe_legend(frame: np.ndarray):
        lang = Config.LANGUAGE
        items = list(PPE_LABELS.values())
        y_start = 30
        for i, item in enumerate(items):
            text = f"{item[lang]}"
            cv2.putText(frame, text, (10, y_start + i * 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        return frame

    @staticmethod
    def draw_violation_count(frame: np.ndarray, count: int):
        lang = Config.LANGUAGE
        text = f"Violations: {count}" if lang == "en" else f"การละเมิด: {count}"
        cv2.putText(frame, text, (Config.FRAME_WIDTH - 200, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        return frame

    def set_language(self, lang: str):
        self.lang = lang
