import datetime
import typing
from dataclasses import dataclass
from typing import Tuple

import numpy as np

from bdat.entities import BatterySpecies, Cycling
from bdat.entities.patterns import PulseEval
from bdat.entities.steps.step import Step
from bdat.entities.steps.steplist import Steplist
from bdat.entities.test.cycling_data import CyclingData
from bdat.resources.patterns.eval_pattern import EvalPattern
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
class Pulse(EvalPattern):
    """Pattern to match a current pulse"""

    #: Current of the pulse in A. If this is a tuple, the current must lie between the two values. If this is a float, a tuple will be constructed by multiplying the value with 0.95 and 1.05.
    current: float | Tuple[float, float] | None = None

    #: Duration of the pulse in seconds. If this is a tuple, the duration must lie between the two values. If this is a float, a tuple will be constructed by multiplying the value with 0.95 and 1.05.
    duration: float | Tuple[float, float] | None = None

    #: Duration of the rest time before the pulse in seconds. If this is a tuple, the duration must lie between the two values. If this is a float, a tuple will be constructed by multiplying the value with 0.95 and 1.05.
    relaxationTime: float | Tuple[float, float] | None = None

    #: Allow a short transition step between pause and pulse to account for imperfect edges at the start of the pulse.
    allowTransitionStep: bool = False

    #: Allow the pulse to go into a CV phase after reaching the end of charge voltage.
    allowCVStep: bool = False

    #: Voltage of the cv phase if it exists. Only relevant if allowCV is True.
    cvVoltage: float | Tuple[float, float] | None = None

    def pattern(self, species: BatterySpecies) -> SteplistPattern:
        current = make_range(
            [self.current, (-1e9, 1e9)],
            (0.95, 1.05),
        )
        duration = make_range([self.duration, (0.5, 60)], (0.95, 1.05))
        relaxationTime = make_range([self.relaxationTime, (60, 1e9)], (0.95, 1.05))
        if self.allowCVStep:
            cvVoltage = make_range(
                [self.cvVoltage, species.endOfChargeVoltage, species.maximumVoltage],
                deltaAbs=(-0.01, 0.02),
            )

        self.pauseStep = PauseProperties(duration=relaxationTime)
        self.transitionStep = StepProperties(duration=(0, 0.5))

        series: typing.List[SteplistPattern] = [self.pauseStep]
        if self.allowTransitionStep:
            series.append(Repeat(self.transitionStep, 0, 3))
        if self.allowCVStep:
            self.pulseStep = And(
                CCProperties(current=current),
                Not(CCProperties(current=(-0.01, 0.01))),
            )
            self.cvStep: CVProperties | None = CVProperties(voltage=cvVoltage)
            series.append(
                Or(
                    Series([self.pulseStep, Optional(self.cvStep)], duration=duration),
                    Series([Optional(self.pulseStep), self.cvStep], duration=duration),
                )
            )
        else:
            self.pulseStep = And(
                CCProperties(current=current, duration=duration),
                Not(CCProperties(current=(-0.01, 0.01), duration=duration)),
            )
            self.cvStep = None
            series.append(self.pulseStep)

        return Series(series)

    def eval(
        self,
        test: Cycling,
        match: Match,
        steps: typing.List[Step],
        df: CyclingData | None,
    ) -> PulseEval:
        pauseStep = next(match.get_matches(self.pauseStep)).steps[0].asPause()
        pulseMatch = next(match.get_matches(self.pulseStep), None)
        pulseStep = None if pulseMatch is None else pulseMatch.steps[0].asCC()
        if self.cvStep is not None:
            cvMatch = next(match.get_matches(self.cvStep), None)
            cvStep = None if cvMatch is None else cvMatch.steps[0].asCV()
        else:
            cvStep = None

        if cvStep is None:
            if pulseStep is None:
                raise Exception("pulseStep and cvStep cannot both be None")
            else:
                start = pulseStep.start
                end = pulseStep.end
                lastStep = pulseStep.stepId
                current = pulseStep.current
                duration = pulseStep.duration
                endVoltage = pulseStep.voltageEnd
                impedance = (
                    pulseStep.voltageEnd - pauseStep.voltageEnd
                ) / pulseStep.current
                soc = pulseStep.socStart
                age = pulseStep.ageStart
                chargeThroughput = pulseStep.dischargeStart
        else:
            end = cvStep.end
            lastStep = cvStep.stepId
            endVoltage = cvStep.voltage
            impedance = np.nan
            if pulseStep is None:
                start = cvStep.start
                current = np.nan
                duration = cvStep.duration
                soc = cvStep.socStart
                age = cvStep.ageStart
                chargeThroughput = cvStep.dischargeStart
            else:
                start = pulseStep.start
                current = pulseStep.current
                duration = pulseStep.duration + cvStep.duration
                soc = pulseStep.socStart
                age = pulseStep.ageStart
                chargeThroughput = pulseStep.dischargeStart

        if self.allowTransitionStep:
            transitionMatch = next(match.get_matches(self.transitionStep), None)
            if transitionMatch:
                for step in transitionMatch.steps:
                    duration += step.duration
                    start = min(start, step.start)

        return PulseEval(
            start=start,
            end=end,
            firstStep=pauseStep.stepId,
            lastStep=lastStep,
            relaxationTime=pauseStep.duration,
            current=current,
            duration=duration,
            relaxedVoltage=pauseStep.voltageEnd,
            endVoltage=endVoltage,
            impedance=impedance,
            soc=soc,
            age=age,
            chargeThroughput=chargeThroughput,
            matchStart=pauseStep.start,
            matchEnd=end,
            starttime=(
                test.start + datetime.timedelta(seconds=start) if test.start else None
            ),
        )
