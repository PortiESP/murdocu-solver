import json

from MurdokuClasses import MurdokuGame
from MurdokuCP_SAT import MurdokuSolver


def read_json(basename):
    with open(f"../step2-parse/output/{basename}.json", "r", encoding="utf-8") as f:
        return json.load(f)


areas = read_json("areas")
objects = read_json("objects")
murdoku_parsed_data = {
    "clues": read_json("clues"),
    "areasMatrix": areas["areasMatrix"],
    "areasIndex": areas["areasIndex"],
    "objName_2_cells": objects["objName_2_cells"],
    "cells_2_objName": objects["cells_2_objName"],
}

game = MurdokuGame(murdoku_parsed_data)
solver = MurdokuSolver()
solver.solve(game)
print(solver.solution)

with open("output/solution.json", "w") as f:
    json.dump(solver.solution, f)
