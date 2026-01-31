import datetime
import typing
from dataclasses import dataclass
from typing import Tuple

import numpy as np

from bdat.entities import BatterySpecies, Cycling
from bdat.entities.patterns import GITTEval, PulseEval
from bdat.entities.steps.step import Step
from bdat.entities.steps.steplist import Steplist
from bdat.entities.test.cycling_data import CyclingData
from bdat.resources.patterns.eval_pattern import EvalPattern
from bdat.resources.patterns.pulse import Pulse
from bdat.steps.step_pattern import (
    And,
    CCProperties,
    CVProperties,
    Not,
    PauseProperties,
    StepProperties,
)
from bdat.steps.steplist_pattern import (
    Match,
    Optional,
    Or,
    Repeat,
    Series,
    SteplistPattern,
)
from bdat.tools.misc import make_range


@dataclass
class GITT(EvalPattern):
    """Pattern to match a GITT profile"""

    pulse: Pulse | None = None

    def pattern(self, species: BatterySpecies) -> SteplistPattern:
        if self.pulse is None:
            self.pulse = Pulse()
        self.pulsePattern = self.pulse.pattern(species)

        return Repeat(self.pulsePattern, min=1)

    def eval(
        self,
        test: Cycling,
        match: Match,
        steps: typing.List[Step],
        df: CyclingData | None,
    ) -> GITTEval:
        pulseMatches = match.get_matches(self.pulsePattern)
        if self.pulse is None:
            raise Exception()
        pulseEvals = [self.pulse.eval(test, m, steps, df) for m in pulseMatches]

        return GITTEval(
            firstStep=pulseEvals[0].firstStep,
            lastStep=pulseEvals[-1].lastStep,
            start=pulseEvals[0].start,
            end=pulseEvals[-1].end,
            age=pulseEvals[0].age,
            chargeThroughput=pulseEvals[0].chargeThroughput,
            matchStart=pulseEvals[0].matchStart,
            matchEnd=pulseEvals[-1].matchEnd,
            starttime=(
                test.start + datetime.timedelta(seconds=pulseEvals[0].start)
                if test.start
                else None
            ),
            pulses=pulseEvals,
        )
