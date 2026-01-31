import datetime
import typing
from dataclasses import dataclass
from typing import Tuple

import numpy as np

from bdat.entities import BatterySpecies, Cycling
from bdat.entities.patterns import UniformCyclingEval
from bdat.entities.steps.step import Step
from bdat.entities.steps.steplist import Steplist
from bdat.entities.test.cycling_data import CyclingData
from bdat.resources.patterns.eval_pattern import EvalPattern
from bdat.steps.step_pattern import (
    CCProperties,
    CPProperties,
    CVProperties,
    Or,
    PauseProperties,
)
from bdat.steps.steplist_pattern import (
    Match,
    Optional,
    RepeatSteps,
    Series,
    SteplistPattern,
)
from bdat.tools.misc import make_range


class UniformCycling(EvalPattern):
    def __init__(self):
        self.charge = CCProperties(current=(0.01, 1e9))
        self.upperCV = CVProperties()
        self.upperPause = PauseProperties()
        self.ccDischarge = CCProperties(current=(-1e9, -0.01))
        self.cpDischarge = CPProperties(power=(-1e9, -0.01))
        self.discharge = Or(self.ccDischarge, self.cpDischarge)
        self.lowerCV = CVProperties()
        self.lowerPause = PauseProperties()

    def pattern(self, species: BatterySpecies) -> SteplistPattern:
        return RepeatSteps(
            Series(
                [
                    self.charge,
                    Optional(self.upperCV),
                    Optional(self.upperPause),
                    self.discharge,
                    Optional(self.lowerCV),
                    Optional(self.lowerPause),
                ]
            ),
            [
                (
                    self.charge,
                    {
                        "current": (0.02, None),
                        "voltageEnd": (None, 0.05),
                    },
                ),
                (self.upperCV, {"voltage": (None, 0.05)}),
                (self.upperPause, {"duration": (0.02, None)}),
                (
                    self.ccDischarge,
                    {
                        "current": (0.02, None),
                        "charge": (0.02, None),
                    },
                ),
                (
                    self.cpDischarge,
                    {
                        "power": (0.02, None),
                        "charge": (0.02, None),
                    },
                ),
                (self.lowerCV, {"voltage": (None, 0.05)}),
                (self.lowerPause, {"duration": (0.02, None)}),
            ],
            min=2,
        )

    def eval(
        self,
        test: Cycling,
        match: Match,
        steps: typing.List[Step],
        _: CyclingData | None,
    ) -> UniformCyclingEval:
        chargeSteps = [m.steps[0].asCC() for m in match.get_matches(self.charge)]
        ccDischargeSteps = [
            m.steps[0].asCC() for m in match.get_matches(self.ccDischarge)
        ]
        cpDischargeSteps = [
            m.steps[0].asCP() for m in match.get_matches(self.cpDischarge)
        ]
        dischargeSteps = [*ccDischargeSteps, *cpDischargeSteps]
        upperPauseSteps = [m.steps[0] for m in match.get_matches(self.upperPause)]
        lowerPauseSteps = [m.steps[0] for m in match.get_matches(self.lowerPause)]

        chargeCurrent = np.mean([s.current for s in chargeSteps])
        maxVoltage = np.mean([s.getEndVoltage() for s in chargeSteps])
        dischargePower = (
            np.mean([s.power for s in cpDischargeSteps]) if cpDischargeSteps else None
        )
        dischargeCurrent = (
            np.mean([s.current for s in ccDischargeSteps]) if ccDischargeSteps else None
        )
        if dischargeSteps[0].socStart is not None:
            minSoc = np.mean([s.socEnd for s in dischargeSteps])
            maxSoc = np.mean([s.socStart for s in dischargeSteps])
            dod = np.mean([s.socStart - s.socEnd for s in dischargeSteps])
        else:
            minSoc = None
            maxSoc = None
            dod = None
        charge = np.mean([s.charge for s in dischargeSteps])

        upperPauseDuration = None
        if len(upperPauseSteps) > 0:
            upperPauseDuration = np.mean([s.duration for s in upperPauseSteps])
        lowerPauseDuration = None
        if len(lowerPauseSteps) > 0:
            lowerPauseDuration = np.mean([s.duration for s in lowerPauseSteps])

        if steps[0].temperatureMean is not None:
            minTemperature = np.min([s.temperatureMin for s in steps])
            maxTemperature = np.min([s.temperatureMax for s in steps])
            meanTemperature = np.average(
                [s.temperatureMean for s in steps], weights=[s.duration for s in steps]
            )
        else:
            minTemperature = None
            maxTemperature = None
            meanTemperature = None

        return UniformCyclingEval(
            start=steps[0].start,
            end=steps[-1].end,
            firstStep=steps[0].stepId,
            lastStep=steps[-1].stepId,
            age=steps[0].ageStart,
            chargeThroughput=steps[0].dischargeStart,
            cyclecount=len(match.subMatches),
            chargeCurrent=chargeCurrent,
            dischargeCurrent=dischargeCurrent,
            dischargePower=dischargePower,
            minVoltage=None,
            maxVoltage=maxVoltage,
            minSoc=minSoc,
            maxSoc=maxSoc,
            dod=dod,
            charge=charge,
            upperPauseDuration=upperPauseDuration,
            lowerPauseDuration=lowerPauseDuration,
            minTemperature=minTemperature,
            maxTemperature=maxTemperature,
            meanTemperature=meanTemperature,
            matchStart=steps[0].start,
            matchEnd=steps[-1].end,
            starttime=(
                test.start + datetime.timedelta(seconds=steps[0].start)
                if test.start
                else None
            ),
        )
