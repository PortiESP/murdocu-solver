import json
import os
from pathlib import Path

import cv2
import pytesseract

# Tesseract is not on PATH by default on Windows
TESSERACT_CMD = os.environ.get("TESSERACT_CMD", r"C:\Program Files\Tesseract-OCR\tesseract.exe")
if Path(TESSERACT_CMD).exists():
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
# Background color of the portrait card (BGR), sampled at GENDER_PIXEL
GENDER_COLORS = {(249, 238, 230): "man", (233, 230, 252): "woman"}
GENDER_PIXEL = (15, 225)


def extract_text_from_img(img, psm=6, only_letters=False):
    # Binarize so Tesseract only sees the text
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    whitelist = f"-c tessedit_char_whitelist={LETTERS}" if only_letters else ""
    text = pytesseract.image_to_string(bw, config=f"--psm {psm} {whitelist}")
    return text.replace("\n", " ").strip()


def get_character_data(img):
    # Fixed regions of the portrait card: name banner, then the clue below it
    name = extract_text_from_img(img[168:210, 90:200], psm=8, only_letters=True)  # psm 8: a single word
    clue = extract_text_from_img(img[210:])
    return name, clue


clues = {}
for path in Path("../step1-capture/output/characters").glob("*.png"):
    img = cv2.imread(str(path))
    if img is None:
        continue

    name, clue = get_character_data(img)
    gender_color = tuple(img[GENDER_PIXEL].tolist())
    if gender_color not in GENDER_COLORS:
        raise ValueError(f"Gender not detected in {path.name}: {gender_color}")

    # People are identified by their initial, as in the clues
    clues[name[0]] = {"name": name, "description": clue, "gender": GENDER_COLORS[gender_color]}

with open("output/clues.json", "w", encoding="utf-8") as f:
    json.dump(clues, f, indent=4, ensure_ascii=False)
