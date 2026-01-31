import typing
from dataclasses import dataclass

import pandas as pd

from bdat.entities import BatterySpecies, Cycling
from bdat.entities.patterns import TestinfoEval
from bdat.entities.steps.step import CCStep, CVStep, Step
from bdat.entities.steps.steplist import Steplist
from bdat.entities.test.cycling_data import CyclingData
from bdat.resources.patterns.eval_pattern import EvalPattern
from bdat.steps.step_pattern import StepProperties
from bdat.steps.steplist_pattern import Match, Repeat, SteplistPattern


@dataclass
class Testinfo(EvalPattern):
    skipAhCounters: bool = False
    chargeAh: float | None = None
    dischargeAh: float | None = None
    totalAh: float | None = None
    lastCharge: float | None = None
    lastDischarge: float | None = None

    def pattern(self, species: BatterySpecies) -> SteplistPattern:
        return Repeat(StepProperties())

    def eval(
        self,
        test: Cycling,
        match: Match,
        steps: typing.List[Step],
        df: CyclingData | None,
    ) -> TestinfoEval:
        chargeAh = self.chargeAh
        dischargeAh = self.dischargeAh
        totalAh = self.totalAh
        lastCharge = self.lastCharge
        lastDischarge = self.lastDischarge

        if chargeAh is None:
            chargeAh = sum([max(s.charge, 0) for s in steps])
        if dischargeAh is None:
            dischargeAh = abs(sum([min(s.charge, 0) for s in steps]))
        if totalAh is None:
            totalAh = sum([abs(s.charge) for s in steps])
        if lastCharge is None:
            if self.skipAhCounters:
                lastCharge = steps[0].chargeStart
            else:
                lastCharge = steps[-1].chargeEnd
        if lastDischarge is None:
            if self.skipAhCounters:
                lastDischarge = steps[0].dischargeStart
            else:
                lastDischarge = steps[-1].dischargeEnd

        return TestinfoEval(
            duration=steps[-1].end - steps[0].start,
            rows=steps[-1].rowEnd,
            chargeAh=chargeAh,
            dischargeAh=dischargeAh,
            totalAh=totalAh,
            firstVoltage=steps[0].getStartVoltage(),
            lastVoltage=steps[-1].getEndVoltage(),
            minVoltage=min(
                [min(s.getStartVoltage(), s.getEndVoltage()) for s in steps]
            ),
            maxVoltage=max(
                [max(s.getStartVoltage(), s.getEndVoltage()) for s in steps]
            ),
            minCurrent=min(
                [min(s.getStartCurrent(), s.getEndCurrent()) for s in steps]
            ),
            maxCurrent=max(
                [max(s.getStartCurrent(), s.getEndCurrent()) for s in steps]
            ),
            totalStepCount=len(steps),
            CCStepCount=sum([1 if isinstance(s, CCStep) else 0 for s in steps]),
            CVStepCount=sum([1 if isinstance(s, CVStep) else 0 for s in steps]),
            firstStep=0,
            lastStep=steps[-1].stepId,
            start=steps[0].start,
            end=steps[-1].end,
            firstSoc=steps[0].socStart,
            lastSoc=steps[-1].socEnd,
            firstAge=steps[0].ageStart,
            lastAge=steps[-1].ageEnd,
            firstCapacity=steps[0].capacity,
            lastCapacity=steps[-1].capacity,
            firstCharge=steps[0].chargeStart,
            lastCharge=lastCharge,
            firstDischarge=steps[0].dischargeStart,
            lastDischarge=lastDischarge,
            age=steps[0].ageStart,
            chargeThroughput=steps[0].dischargeStart,
            matchStart=steps[0].start,
            matchEnd=steps[-1].end,
            starttime=test.start,
        )
