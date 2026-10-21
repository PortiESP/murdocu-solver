import hashlib
import json
import os
from pathlib import Path

import google.genai as genai
from dotenv import load_dotenv
from pydantic import TypeAdapter

from MurdokuConstraints import ClueConstraints, ConstraintsDict

RESPONSE_ADAPTER = TypeAdapter(list[ClueConstraints])
MODEL = "gemini-3.5-flash-lite"
CACHE_DIR = Path(__file__).parent / "output" / "ai_cache"
load_dotenv(Path(__file__).parent / ".env")


def murdoku_constraints_ai(raw_clues, N, areas_names, objects_names) -> ConstraintsDict:
    prompt = json.dumps(raw_clues)
    instructions = \
        INTRODUCTION + \
        PROBLEM_CONTEXT(N, areas_names, objects_names, raw_clues) + \
        CONSTRAINTS + \
        ADDITIONAL_INFO(N) + \
        EXAMPLES

    constraints = {c.person: c.constraints for c in ask_ai(prompt, instructions)}
    missing = set(raw_clues) - set(constraints)
    assert not missing, f"AI returned no constraints for: {missing}"
    return constraints


def ask_ai(prompt: str, instructions: str) -> list[ClueConstraints]:
    # The key covers everything that shapes the answer, so any change triggers a fresh call
    schema = json.dumps(RESPONSE_ADAPTER.json_schema(), sort_keys=True)
    key = hashlib.sha256(f"{MODEL}\n{schema}\n{instructions}\n{prompt}".encode()).hexdigest()[:16]
    path = CACHE_DIR / f"{key}.json"

    if path.exists():
        return RESPONSE_ADAPTER.validate_json(path.read_text(encoding="utf-8"))

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    res = client.interactions.create(
        model=MODEL,
        input=prompt,
        system_instruction=instructions,
        stream=False,
        generation_config={"temperature": 0},
        response_mime_type="application/json",
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": RESPONSE_ADAPTER.json_schema(),
        },
    )
    text = res.output_text
    if not text:
        raise RuntimeError(f"Empty AI response: {res}")

    # Validate before caching so a bad response is never stored
    result = RESPONSE_ADAPTER.validate_json(text)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return result


# =============================================================================[ AI instructions ]>>>

INTRODUCTION = """
You convert clues from a Murdoku logic puzzle into structured constraints.
You receive a JSON object mapping each person's initial to their clue data.
Return one entry per person, with all the atoms of their clue. Do not solve the puzzle.
"""

PROBLEM_CONTEXT = lambda N, areas_names, objects_names, people_list: f"""
Board: {N}x{N}. Rows 0 (top) to {N-1} (bottom). Columns 0 (left) to {N-1} (right).
Areas: {", ".join(areas_names)}
Objects: {", ".join(objects_names)}
People: {", ".join(f"{c} ({p['name']}, {p['gender']})" for c, p in people_list.items())}
Use ONLY these exact names for areas and objects.
"""

CONSTRAINTS = """
- in_area: the person is in `area`.
- in_row / in_col: the person is in row/column `index`.
- on_object: the person is on a cell with `obj`.
- beside_object: the person is orthogonally adjacent (same area) to `obj`. negated=true means NOT beside.
- area_has_object: the person's area contains `obj`.
- area_has_person: some OTHER person is in the same area as the person, and that same other person
  matches every filter given: `gender`, and `obj` + `relation` ("on" = on a cell with `obj`,
  "beside" = orthogonally adjacent to `obj`). Always set `relation` when `obj` is set.
- area_count: exactly `count` people (including the person) are in the person's area.
"""

ADDITIONAL_INFO = lambda N: f"""
- "area" and "room" mean the same thing.
- "beside" means up, down, left or right, inside the same area. Never diagonal.
- "bottom row" = row {N-1}, "top row" = row 0.
- "someone else" / "a man" / "a woman" never refers to the clue's own person.
- A clue can produce several atoms. Return all of them.
- Every atom has `negated`. Words like "not", "never", "wasn't" set negated=true on the atom they apply to;
  otherwise negated=false.
- Pronouns like "it" refer to the object mentioned earlier in the same clue.
- Clue words may differ from object names: map them to the closest object in the list
  (e.g. "shelf" -> "bookshelf", "TV" -> "tv"). Use "unknown" only if no object fits.
- If a phrase cannot be expressed with these atoms, do not invent one: return an atom with kind "unknown".
"""


EXAMPLES = """
EXAMPLE (a different 6x6 board with areas OFFICE, GARAGE, GARDEN and objects plant, desk, sofa).
Never copy names from this example: use only the areas and objects of the real board above.

Input:
{"P": {"name": "Paula", "description": "She was in the Office.", "gender": "woman"},
 "R": {"name": "Robert", "description": "He was not beside a plant. He was in the top row.", "gender": "man"},
 "S": {"name": "Sara", "description": "There was a woman on a sofa in her room.", "gender": "woman"},
 "T": {"name": "Tom", "description": "There was a desk in his area. He was not beside it.", "gender": "man"},
 "Q": {"name": "Quinn", "description": "Someone else was beside a desk in his area.", "gender": "man"},
 "U": {"name": "Ulf", "description": "He was in the third column. He was older than Tom.", "gender": "man"},
 "V": {"name": "Vera", "description": "The Victim. She was alone with the murderer.", "gender": "woman"}}

Output:
[
 {"person": "P", "constraints": [{"kind": "in_area", "area": "OFFICE", "negated": false}]},
 {"person": "R", "constraints": [
   {"kind": "beside_object", "obj": "plant", "negated": true},
   {"kind": "in_row", "index": 0, "negated": false}]},
 {"person": "S", "constraints": [{"kind": "area_has_person", "gender": "woman", "obj": "sofa", "relation": "on", "negated": false}]},
 {"person": "T", "constraints": [
   {"kind": "area_has_object", "obj": "desk", "negated": false},
   {"kind": "beside_object", "obj": "desk", "negated": true}]},
 {"person": "Q", "constraints": [{"kind": "area_has_person", "obj": "desk", "relation": "beside", "negated": false}]},
 {"person": "U", "constraints": [
   {"kind": "in_col", "index": 2, "negated": false},
   {"kind": "unknown", "negated": false}]},
 {"person": "V", "constraints": [{"kind": "area_count", "count": 2, "negated": false}]}
]
"""