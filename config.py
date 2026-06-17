LANG_THAI = "th"
LANG_EN = "en"

class Config:
    MODEL_PATH = "yolov8s.pt"
    CONFIDENCE_THRESHOLD = 0.5
    SOURCE = 0
    LANGUAGE = LANG_EN
    SAVE_VIOLATIONS = True
    VIOLATION_LOG = "violations.csv"
    ALERT_SOUND = True
    DASHBOARD_HOST = "0.0.0.0"
    DASHBOARD_PORT = 5050
    FRAME_WIDTH = 1280
    FRAME_HEIGHT = 720

PPE_CLASSES = {
    0: {"en": "person", "th": "บุคคล"},
}

PPE_REQUIRED = ["hardhat", "safety_vest", "safety_glasses"]

PPE_LABELS = {
    "hardhat": {"en": "Hardhat", "th": "หมวกนิรภัย"},
    "safety_vest": {"en": "Safety Vest", "th": "เสื้อกั๊กนิรภัย"},
    "safety_glasses": {"en": "Safety Glasses", "th": "แว่นตานิรภัย"},
    "person": {"en": "Person", "th": "บุคคล"},
}

VIOLATION_MESSAGES = {
    "no_hardhat": {"en": "Missing hardhat!", "th": "ไม่สวมหมวกนิรภัย!"},
    "no_vest": {"en": "Missing safety vest!", "th": "ไม่สวมเสื้อกั๊กนิรภัย!"},
    "no_glasses": {"en": "Missing safety glasses!", "th": "ไม่สวมแว่นตานิรภัย!"},
}
