import json

import numpy as np


with open("output/walls.json", "r") as f:
    walls = json.load(f)

N = len(walls["V"])
areas = np.full((N, N), None)  # Area id of each cell
areas_lists: list[list[tuple[int, int]]] = []  # Cells of each area, in the order they were visited


def get_valid_neighbours(ij_coords: tuple[int, int]):
    i, j = ij_coords
    result = []

    # Top
    if i != 0 and walls["H"][i-1][j] == 0:
        result.append((i-1, j))
    # Right
    if j != N-1 and walls["V"][i][j] == 0:
        result.append((i, j+1))
    # Bottom
    if i != N-1 and walls["H"][i][j] == 0:
        result.append((i+1, j))
    # Left
    if j != 0 and walls["V"][i][j-1] == 0:
        result.append((i, j-1))

    return result


def propagate_tile(ij_coords: tuple[int, int], area_id: int):
    areas[ij_coords] = area_id
    areas_lists[area_id].append(ij_coords)

    for neighbour in get_valid_neighbours(ij_coords):
        if areas[neighbour] is None:
            propagate_tile(neighbour, area_id)


# Flood fill: every cell not yet assigned starts a new area that spreads until it hits a wall
area_id = 0
for i in range(N):
    for j in range(N):
        if areas[i, j] is not None:
            continue

        areas_lists.append([])
        propagate_tile((i, j), area_id)
        area_id += 1

for row in areas:
    print(row)

# Area ids only: step4.2 reads them to name each area
with open("output/areas-ids.json", "w") as f:
    json.dump({
        "areasMatrix": areas.tolist(),
        "areasLists": areas_lists,
    }, f)
