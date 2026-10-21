# Helper to build the object templates used by step5: click the cells with an object and press "q"
# to export a crop of each selected cell to ./objects (rename the files afterwards, e.g. "bed-1.png")
import sys
from pathlib import Path

import cv2

WINDOW = "Select objects"
SCREENSHOT_SIZE = 60  # Side of the square crop, centered in the cell
UNSELECTED = (255, 0, 0)
SELECTED = (0, 0, 255)

img = cv2.imread("../step1-capture/output/board-no-names.png")
if img is None:
    print("[Error] unable to read ../step1-capture/output/board-no-names.png")
    sys.exit(1)

N = len(list(Path("../step1-capture/output/characters").glob("*.png")))  # One person per row
CELL_SIZE = img.shape[0] // N

display_img = img.copy()
selection: set[tuple[int, int]] = set()


def cell_crop(image, i, j):
    centerI = CELL_SIZE//2 + CELL_SIZE*i
    centerJ = CELL_SIZE//2 + CELL_SIZE*j
    half = SCREENSHOT_SIZE//2
    return image[centerI-half:centerI+half, centerJ-half:centerJ+half]


def window_callback(event, j, i, flags, param):
    if event != cv2.EVENT_LBUTTONDOWN:
        return

    # Toggle the clicked cell
    pos = (i//CELL_SIZE, j//CELL_SIZE)
    if pos in selection:
        selection.remove(pos)
        cell_crop(display_img, *pos)[:] = UNSELECTED
    else:
        selection.add(pos)
        cell_crop(display_img, *pos)[:] = SELECTED

    print(selection)
    cv2.imshow(WINDOW, display_img)


# Mark every crop area and let the user select cells
for i in range(N):
    for j in range(N):
        cell_crop(display_img, i, j)[:] = UNSELECTED

cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
cv2.resizeWindow(WINDOW, 800, 800)
cv2.setMouseCallback(WINDOW, window_callback)
cv2.imshow(WINDOW, display_img)
while cv2.waitKey(20) & 0xFF != ord("q"):
    pass

# Save the selected cells, cropped from the original image
print("Exporting selection: ", selection)
Path("./objects").mkdir(exist_ok=True)
for i, j in selection:
    cv2.imwrite(f"./objects/object-{i}_{j}.png", cell_crop(img, i, j))
