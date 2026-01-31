from dataclasses import dataclass, field

from bson import ObjectId

from bdat.entities.patterns.pattern_eval import PatternEval


@dataclass
class ErrorEval(PatternEval):
    error: str
