from ortools.sat.python import cp_model

from MurdokuClasses import MurdokuGame
from MurdokuConstraints import Constraint


# Objects a person can stand on; any other object blocks its cell
OCCUPIABLE = {"chair", "bed", "car"}


class MurdokuSolver:
    x: dict
    in_area: dict
    solution: dict[str, tuple[int, int]]

    def solve(self, game: MurdokuGame):
        self.game = game
        self.solution = {}

        # 1. Model
        self.model = cp_model.CpModel()

        # 2. Params
        self.board = game.board
        self.people = game.clues.keys()
        self.genders = {p: game.clues[p]["gender"] for p in self.people}
        self.N = self.board.N
        assert len(self.people) == self.N

        self.walkable = [c.pos for c in self.board.cells_dict.values() if not c.has_object or c.obj_name in OCCUPIABLE]

        # 3. Variable definition

        # x[person, pos]: whether the person "p" is in the position "pos"
        # e.g.: x["A", (0, 1)]
        self.x = {(p, pos): self.model.new_bool_var(f"pos:{p}_in_{pos}") for p in self.people for pos in self.walkable}
        # in_area[person, area]: whether the person "p" is in the area "a"
        # e.g.: in_area["A", "KITCHEN"]
        self.in_area = {(p, a): self.model.new_bool_var(f"in_area:{p}_in_{a}") for p in self.people for a in self.board.areas_dict}

        # 4. Constraints

        # Each person occupies exactly one cell
        for p in self.people:
            self.model.add_exactly_one(self.x[p, pos] for pos in self.walkable)
        # Exactly one person per row/col (this also keeps two people out of the same cell)
        for k in range(self.N):
            self.model.add_exactly_one(self.x[p, pos] for p in self.people for pos in self.walkable if pos[0] == k)  # Check rows
            self.model.add_exactly_one(self.x[p, pos] for p in self.people for pos in self.walkable if pos[1] == k)  # Check cols
        # Bind the variable `in_area` to the area of the person
        for p in self.people:
            for a, cells in self.board.areas_dict.items():
                # `sum(... == ..)`: binds the in_area variable to the area in which the person is
                # `for cell in cells`: Iterate over all the cells of the current area
                # `if (p, (c.i, c.j)) in self.x`: filters out the non-walkable cells
                # So, when `p` is in the area `a` the sum will return `1`
                self.model.add(self.in_area[p, a] == sum(self.x[p, (c.i, c.j)] for c in cells if (p, (c.i, c.j)) in self.x))
        # Advanced constraints
        for p, constraints in game.constraints.items():
            for c in constraints:
                if c.kind == "unknown":
                    raise ValueError(f"Error while processing the clue: {p} - {c}")
                func_name = f"add_{c.kind}"
                if not hasattr(self, func_name):
                    raise ValueError(f"Error, {func_name} not implemented: {c}")

                # Dispatch to the add_<kind> helper below
                getattr(self, func_name)(p, c)

        # 5. Solve
        solver = cp_model.CpSolver()
        status = solver.solve(self.model)
        print(solver.status_name(status))

        # 6. Results: print the board ("o" = object)
        grid = [["." for _ in range(self.N)] for _ in range(self.N)]
        for (i, j), cell in self.board.cells_dict.items():
            if cell.has_object:
                grid[i][j] = "o"
        for (p, (i, j)), var in self.x.items():
            if solver.value(var):  # 1: the person is in this cell
                grid[i][j] = p
                self.solution[p] = (i, j)
        for row in grid:
            print(" ".join(row))


    # =============================================================================[ Constraint helpers ]>>>

    # If person "p" is in area "c.area"
    def add_in_area(self, p, c: Constraint):
        self.model.add(self.in_area[p, c.area] == (0 if c.negated else 1))

    # If person "p" is in row "c.index"
    def add_in_row(self, p, c: Constraint):
        # The operation "sum()" ensures that the person "p" is occupying just one of the candidate positions "pos"
        # Being "pos" the walkable cells of row "c.index"
        self.model.add(sum(self.x[p, pos] for pos in self.walkable if pos[0] == c.index) == (0 if c.negated else 1))

    # If person "p" is in col "c.index"
    def add_in_col(self, p, c: Constraint):
        # Same logic as "add_in_row"
        self.model.add(sum(self.x[p, pos] for pos in self.walkable if pos[1] == c.index) == (0 if c.negated else 1))

    # If person "p" is on a cell with object "c.obj"
    def add_on_object(self, p, c: Constraint):
        # Get a list of cells, walkable, and that contain object "c.obj"
        cells_with_obj = [pos for pos in self.walkable if self.board.cells_dict[pos].obj_name == c.obj]
        self.model.add(sum(self.x[p, pos] for pos in cells_with_obj) == (0 if c.negated else 1))

    # If person "p" is beside object "c.obj"
    def add_beside_object(self, p, c: Constraint):
        cells = []
        # From all the walkable cells
        for pos in self.walkable:
            # Get the neighboring cells of each walkable cell
            neighboring_cells = self.board.cells_dict[pos].area_neighboring_cells
            # If any of them has an object of kind "c.obj"
            if any([n.obj_name == c.obj for n in neighboring_cells]):
                # It is a candidate cell for person "p"
                cells.append(pos)
        # The "sum()" operation ensures that the person "p" is occupying just one of those cells (or 0 if negated)
        self.model.add(sum(self.x[p, pos] for pos in cells) == (0 if c.negated else 1))

    # If the person "p" is in an area "c.area" that contains an object "c.obj"
    def add_area_has_object(self, p, c: Constraint):
        # Get the areas with object "c.obj"
        areas = {a for a, cells in self.board.areas_dict.items() if any(cell.obj_name == c.obj for cell in cells)}
        # The person "p" must be in one of those areas (or none if negated)
        self.model.add(sum(self.in_area[p, a] for a in areas) == (0 if c.negated else 1))

    # If the person "p" is in an area with "c.count" people (including themselves)
    def add_area_count(self, p, c: Constraint):
        # For every area
        for a in self.board.areas_dict:
            # The area "a" must have exactly "c.count" people
            # Only enforce this restriction on the area where person "p" is located
            self.model.add(sum(self.in_area[q, a] for q in self.people) == c.count) \
            .only_enforce_if(self.in_area[p, a])

    # If the person "p" is in an area where there is another person that matches constraint "c"
    def add_area_has_person(self, p, c: Constraint):
        # 1. Iter over all the areas
        for a, cells in self.board.areas_dict.items():
            # 2. Find the cells that match the description
            if c.relation == "on":
                candidate_cells = [cell.pos for cell in cells if cell.obj_name == c.obj]
            elif c.relation == "beside":
                candidate_cells = [cell.pos for cell in cells if any(nei_cell.obj_name == c.obj for nei_cell in cell.area_neighboring_cells)]
            else:
                candidate_cells = [cell.pos for cell in cells]

            # 3. Filter by gender ("q != p" ensures that "p" does not match its own constraint)
            candidate_people = [q for q in self.people if q != p and (not c.gender or self.genders[q] == c.gender)]

            # 4. Merge all candidates
            # "(q, pos) in self.x" ensures that there are no candidates in non-walkable cells
            terms = [self.x[q, pos] for q in candidate_people for pos in candidate_cells if (q, pos) in self.x]

            # 5. Conditional restriction
            if terms:  # If candidates
                self.model.add(sum(terms) >= 1).only_enforce_if(self.in_area[p, a])
            else:      # If no candidate match
                self.model.add(self.in_area[p, a] == 0)
