import json
import os
import sys
from pathlib import Path

import cv2
import numpy as np
import pytesseract

# Tesseract is not on PATH by default on Windows
TESSERACT_CMD = os.environ.get("TESSERACT_CMD", r"C:\Program Files\Tesseract-OCR\tesseract.exe")
if Path(TESSERACT_CMD).exists():
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

img = cv2.imread("../step1-capture/output/board-only-names.png")
if img is None:
    print("[Error] unable to read ../step1-capture/output/board-only-names.png")
    sys.exit(1)

# The area names are white text: keep bright, unsaturated pixels as black-on-white for the OCR
grayscale = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
sat = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)[:, :, 1]
mask = (grayscale > 225) & (sat < 30)
bw = np.where(mask, 0, 255).astype(np.uint8)

# OCR (psm 11: sparse text, the names are scattered over the board)
data = pytesseract.image_to_data(
    bw,
    config="--psm 11 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    output_type=pytesseract.Output.DICT
)

words_data = []
for k, word in enumerate(data["text"]):
    if word.strip():
        words_data.append({
            "text": word,
            "centerI": data["top"][k] + data["height"][k] // 2,
            "centerJ": data["left"][k] + data["width"][k] // 2,
        })

with open("output/areas-ids.json", "r") as f:
    areas = json.load(f)

# Each name belongs to the area of the cell under its center
N = len(areas["areasMatrix"])
CELL_SIZE = img.shape[0] // N
areas_names = {}
for w_data in words_data:
    row = w_data["centerI"] // CELL_SIZE
    col = w_data["centerJ"] // CELL_SIZE
    area_id = areas["areasMatrix"][row][col]
    areas_names[str(area_id)] = w_data["text"]
    print(f"AREA: {w_data['text']}, POS: {row}-{col}")

with open("output/areas-names.json", "w") as f:
    json.dump(areas_names, f, indent=2)

# Final areas file: same matrix with names instead of ids
with open("output/areas.json", "w") as f:
    json.dump({
        "areasMatrix": [[areas_names[str(a)] for a in row] for row in areas["areasMatrix"]],
        "areasLists": areas["areasLists"],
        "areasIndex": [areas_names[str(a)] for a in range(len(areas["areasLists"]))],
    }, f)
