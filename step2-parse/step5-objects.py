import json
import sys
from pathlib import Path

import cv2
import numpy as np
from cv2.typing import MatLike


board = cv2.imread("../step1-capture/output/board-no-names.png")
if board is None:
    print("[Error] unable to read ../step1-capture/output/board-no-names.png")
    sys.exit(1)

N = len(list(Path("../step1-capture/output/characters").glob("*.png")))  # One person per row
CELL_SIZE = board.shape[0] // N

DEFAULT_TOLERANCE = 0.015
# Per-template tolerances, tuned by hand
TOLERANCES = {
    "shelf": 0.1,
    "bed-2": 0.001,
    "bush": 0.1
}


def object_find_all(template: MatLike, tolerance=DEFAULT_TOLERANCE):
    # TM_SQDIFF_NORMED: 0 is a perfect match, so keep the positions below the tolerance
    res = cv2.matchTemplate(board, template, cv2.TM_SQDIFF_NORMED)  # type: ignore
    Is, Js = np.where(res < tolerance)
    return list({(int(i) // CELL_SIZE, int(j) // CELL_SIZE) for i, j in zip(Is, Js)})


# Templates are named "<object>.png" or "<object>-<variant>.png"
objects_dict: dict[str, list[tuple[int, int]]] = {}
for path in Path("./objects").glob("*.png"):
    template = cv2.imread(str(path))
    if template is None:
        raise ValueError(f"Unable to read {path}")

    cells = object_find_all(template, TOLERANCES.get(path.stem, DEFAULT_TOLERANCE))
    obj_name = path.stem.split("-")[0]
    objects_dict[obj_name] = list(set(objects_dict.get(obj_name, []) + cells))

for obj_name, cells in objects_dict.items():
    print(obj_name, cells)

cells_2_objName = np.full((N, N), None)
for obj_name, cells in objects_dict.items():
    for cell in cells:
        cells_2_objName[cell] = obj_name

with open("./output/objects.json", "w") as f:
    json.dump({
        "objName_2_cells": objects_dict,
        "cells_2_objName": cells_2_objName.tolist()
    }, f)
