import json
import sys

import cv2
import numpy as np

# 1. Read img
img = cv2.imread("../step1-capture/output/board-only.png")
if img is None:
    print("[Error] unable to read ../step1-capture/output/board-only.png")
    sys.exit(1)

# 2. Black pixel mask
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
mask = gray < 50
cv2.imwrite("output/mask.png", (1 - mask.astype(np.uint8)) * 255)

# 3. Projections: black pixels per column/row
cols = mask.sum(axis=0)
rows = mask.sum(axis=1)

# 4. Gridlines
# The board is square (NxN). The screenshot has a small white margin, then the borders, then the gridlines.
# A column/row is a gridline when at least 80% of its pixels are black
mask_height = mask.shape[0]
black_columns = np.where(cols > .8 * mask_height)[0]
black_rows = np.where(rows > .8 * mask_height)[0]
# Group consecutive indexes: each group is one line, several pixels thick
column_groups = np.split(black_columns, np.where(np.diff(black_columns) > 1)[0] + 1)
row_groups = np.split(black_rows, np.where(np.diff(black_rows) > 1)[0] + 1)
# The first and last groups are the board borders
column_gridlines = column_groups[1:-1]
row_gridlines = row_groups[1:-1]
N = len(column_gridlines) + 1

# 5. Coordinate of the last pixel of each gridline
gridlines_Jcoords = [int(g[-1]) for g in column_gridlines]
gridlines_Icoords = [int(g[-1]) for g in row_gridlines]
GRIDLINE_WIDTH = 6
THRESHOLD_WALL = GRIDLINE_WIDTH * 2  # Walls are drawn thicker than the regular gridlines
BORDER_WIDTH = 50                    # White margin + board border
OFFSET = 50                          # Distance from the cell edge to the sampled pixel

print("Gridlines J:", gridlines_Jcoords)
print("Gridlines I:", gridlines_Icoords)

# 6. Walls map
# A gridline is a wall when it is still black THRESHOLD_WALL pixels before its end
V_walls_map = np.full((N, N), False)  # Wall on the right of the cell
H_walls_map = np.full((N, N), False)  # Wall below the cell
cells_startJ = [BORDER_WIDTH, *gridlines_Jcoords]
cells_startI = [BORDER_WIDTH, *gridlines_Icoords]
for i in range(N):
    for j in range(N):
        if j < N-1:
            V_walls_map[i, j] = mask[cells_startI[i] + OFFSET][gridlines_Jcoords[j] - THRESHOLD_WALL]
        if i < N-1:
            H_walls_map[i, j] = mask[gridlines_Icoords[i] - THRESHOLD_WALL][cells_startJ[j] + OFFSET]

print(V_walls_map.astype(np.uint8))
print(H_walls_map.astype(np.uint8))

# One row per line, so the file reads like the board
with open("output/walls.json", "w") as f:
    f.write(json.dumps({
        "V": V_walls_map.astype(np.uint8).tolist(),
        "H": H_walls_map.astype(np.uint8).tolist()
    }).replace("],", "],\n").replace("[[", "[\n ["))
