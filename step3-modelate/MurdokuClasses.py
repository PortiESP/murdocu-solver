from __future__ import annotations
from typing import Literal

from MurdokuConstraints import ConstraintsDict
from MurdokuConstraintsAI import murdoku_constraints_ai


# =============================================================================[ MurdokuGame Class ]>>>

Clue = dict[Literal["name", "description", "gender"], str]

class MurdokuGame:
    board: MurdokuBoard
    clues: dict[str, Clue]  # Key-value: [Person's initial]-[Clue]
    constraints: ConstraintsDict

    def __init__(self, data) -> None:
        N = len(data["areasMatrix"])
        self.board = MurdokuBoard(N, data["areasMatrix"], data["cells_2_objName"])

        # Translate the clues into constraints
        self.clues = data["clues"]
        self.constraints = murdoku_constraints_ai(self.clues, N, data["areasIndex"], data["objName_2_cells"].keys())


# =============================================================================[ MurdokuBoard Class ]>>>

class MurdokuBoard:
    N: int
    areas_dict: dict[str, list[MurdokuCell]]  # Key-value: [Area name]-[Cells of the area]
    cells_dict: dict[tuple[int, int], MurdokuCell]
    cells_matrix: list[list[MurdokuCell]]

    def __init__(self, N: int, areas_matrix, cells_2_objName) -> None:
        self.N = N
        self.areas_dict = {}
        self.cells_dict = {}
        self.cells_matrix = []

        for i in range(N):
            self.cells_matrix.append([])
            for j in range(N):
                area_name = areas_matrix[i][j]
                cell = MurdokuCell(self, (i, j), area_name, cells_2_objName[i][j])

                self.cells_dict[(i, j)] = cell
                self.cells_matrix[i].append(cell)
                self.areas_dict.setdefault(area_name, []).append(cell)

        # Neighbours can only be linked once every cell exists
        for row in self.cells_matrix:
            for cell in row:
                cell.setup_neighboring_cells()


# =============================================================================[ MurdokuCell Class ]>>>

class MurdokuCell:
    # Position (row, col)
    i: int
    j: int
    pos: tuple[int, int]
    # Object
    has_object: bool = False
    obj_name: str = "-"
    # Area
    area_name: str
    # Orthogonal neighbours inside the same area
    area_neighboring_cells: list[MurdokuCell]

    def __init__(self, board: MurdokuBoard, pos: tuple[int, int], area_name: str, object_name: str | None) -> None:
        self.board = board
        self.i, self.j = pos
        self.pos = pos
        self.area_name = area_name
        self.area_neighboring_cells = []

        if object_name is not None:
            self.obj_name = object_name
            self.has_object = True

    def is_same_area(self, cell: MurdokuCell | tuple[int, int]):
        if not isinstance(cell, MurdokuCell):
            cell = self.board.cells_dict[cell]
        return cell.area_name == self.area_name

    def setup_neighboring_cells(self):
        N = self.board.N
        for ni, nj in [(self.i-1, self.j), (self.i, self.j+1), (self.i+1, self.j), (self.i, self.j-1)]:
            if 0 <= ni < N and 0 <= nj < N and self.is_same_area((ni, nj)):
                self.area_neighboring_cells.append(self.board.cells_dict[(ni, nj)])
