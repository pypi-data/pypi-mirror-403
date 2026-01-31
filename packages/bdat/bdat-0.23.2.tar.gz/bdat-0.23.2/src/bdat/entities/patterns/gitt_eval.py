import typing
from dataclasses import dataclass

from bdat.entities.patterns.pattern_eval import PatternEval
from bdat.entities.patterns.pulse_eval import PulseEval


@dataclass
class GITTEval(PatternEval):
    pulses: typing.List[PulseEval]
