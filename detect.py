# detect.py
# Minimal detector hook. Replace the body of detect_image() with your real model later.

from random import random

def detect_image(image_path: str) -> tuple[str, float]:
    """
    Return a tuple: (label, confidence_percent)
    label must be "REAL" or "FAKE"
    confidence_percent is a float between 0 and 100
    """
    # --- Dummy logic for now ---
    fake_score = random()
    label = "FAKE" if fake_score > 0.55 else "REAL"
    confidence = round(50 + abs(fake_score - 0.5) * 100, 2)
    return label, min(confidence, 99.99)