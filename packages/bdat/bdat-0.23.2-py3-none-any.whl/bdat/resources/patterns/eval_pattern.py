import typing
from abc import ABC, abstractmethod

from bdat.entities import BatterySpecies, Cycling
from bdat.entities.patterns.pattern_eval import PatternEval
from bdat.entities.steps.step import Step
from bdat.entities.test.cycling_data import CyclingData
from bdat.steps.steplist_pattern import Match, SteplistPattern


class EvalPattern(ABC):
    @abstractmethod
    def pattern(self, species: BatterySpecies) -> SteplistPattern:
        pass

    @abstractmethod
    def eval(
        self,
        test: Cycling,
        match: Match,
        steps: typing.List[Step],
        df: CyclingData | None,
    ) -> PatternEval:
        pass

    def eval_needs_data(self) -> bool:
        return False
