from typing import Literal, Optional
from pydantic import BaseModel


ConstraintKind = Literal[
    "in_area", "in_row", "in_col", "on_object", "beside_object",
    "area_has_object", "area_has_person", "area_count", "unknown",
]

class Constraint(BaseModel):
    kind: ConstraintKind
    area: Optional[str] = None
    index: Optional[int] = None
    obj: Optional[str] = None
    count: Optional[int] = None
    gender: Optional[Literal["man", "woman"]] = None
    relation: Optional[Literal["on", "beside"]] = None  # area_has_person only: how the other person relates to `obj`
    negated: bool  # no default: forces the AI to decide it for every atom

ConstraintsList = list[Constraint]

# The AI returns a list of these (Gemini rejects dict schemas with free keys)
class ClueConstraints(BaseModel):
    person: str
    constraints: ConstraintsList

ConstraintsDict = dict[str, ConstraintsList]