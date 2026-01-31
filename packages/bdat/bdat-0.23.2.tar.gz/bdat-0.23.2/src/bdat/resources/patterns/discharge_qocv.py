import datetime
import math
import typing
from dataclasses import dataclass
from typing import Tuple

import numpy as np
import scipy.stats

from bdat.entities import BatterySpecies, Cycling
from bdat.entities.patterns import DischargeQOCVEval
from bdat.entities.steps.step import Step
from bdat.entities.steps.steplist import Steplist
from bdat.entities.test.cycling_data import CyclingData
from bdat.resources.patterns.eval_pattern import EvalPattern
from bdat.steps.step_pattern import CCProperties, CVProperties, PauseProperties
from bdat.steps.steplist_pattern import Match, Optional, Series, SteplistPattern
from bdat.tools.misc import make_range


@dataclass
class DischargeQOCV(EvalPattern):
    eocVoltage: float | Tuple[float, float] | None = None
    eodVoltage: float | Tuple[float, float] | None = None
    chargeCurrent: float | Tuple[float, float] | None = None
    dischargeCurrent: float | Tuple[float, float] | None = None
    cutoffCurrent: float | Tuple[float, float] | None = None
    relaxationTime: float | Tuple[float, float] | None = None
    ccDuration: float | Tuple[float, float] | None = None
    #: Number of values in the OCV and DVA/ICA curves retuurned by the eval function. If this is None, the raw data will be used without any downsampling.
    numSamples: int | None = 200
    makeDerivatives: bool = True

    def pattern(self, species: BatterySpecies) -> SteplistPattern:
        if species.capacity is None:
            raise Exception("Battery species has no defined capacity")
        eocVoltage = make_range(
            [self.eocVoltage, species.endOfChargeVoltage, species.maximumVoltage],
            deltaAbs=(-0.01, 0.01),
        )
        eodVoltage = make_range(
            [self.eodVoltage, species.endOfDischargeVoltage, species.minimumVoltage],
            deltaAbs=(-0.01, 0.01),
        )
        chargeCurrent = make_range(
            [self.chargeCurrent, (0, 1e9)],
            (0.95, 1.05),
        )
        dischargeCurrent = make_range(
            [
                self.dischargeCurrent,
                (-0.11 * species.capacity, 0.0),
            ],
            (-1.05, -0.95),
        )
        cutoffCurrent = make_range(
            [self.cutoffCurrent, (0, chargeCurrent[1])], (0.95, 1.05)
        )
        relaxationTime = make_range([self.relaxationTime, (0, 1e9)], (0.95, 1.05))
        ccDuration = make_range([self.ccDuration], (0.95, 1.05), allowNone=True)

        self.chargeStep = CCProperties(
            current=chargeCurrent, voltageEnd=eocVoltage, duration=ccDuration
        )
        self.cvStep = CVProperties(voltage=eocVoltage, currentEnd=cutoffCurrent)
        self.pauseStep = PauseProperties(duration=relaxationTime)
        self.dischargeStep = CCProperties(
            current=dischargeCurrent, voltageEnd=eodVoltage
        )

        return Series(
            [
                self.chargeStep,
                Optional(self.cvStep),
                Optional(self.pauseStep),
                self.dischargeStep,
            ]
        )

    def eval_needs_data(self) -> bool:
        return True

    def eval(
        self,
        test: Cycling,
        match: Match,
        steps: typing.List[Step],
        data: CyclingData | None,
    ) -> DischargeQOCVEval:
        if data is None:
            raise Exception("Eval needs test data")

        chaStep = next(match.get_matches(self.chargeStep)).steps[0].asCC()
        cvMatch = next(match.get_matches(self.cvStep), None)
        cvStep = None if cvMatch is None else cvMatch.steps[0].asCV()
        pauseMatch = next(match.get_matches(self.pauseStep), None)
        pauseStep = None if pauseMatch is None else pauseMatch.steps[0].asPause()
        dchStep = next(match.get_matches(self.dischargeStep)).steps[0].asCC()

        rawVoltage = data.voltage[dchStep.rowStart : dchStep.rowEnd]
        rawCharge = (
            data.discharge[dchStep.rowStart : dchStep.rowEnd]
            - data.discharge[dchStep.rowStart]
        )
        if self.numSamples:
            charge = np.linspace(0, 1, self.numSamples) * abs(dchStep.charge)
            voltage = np.interp(charge, rawCharge, rawVoltage)
        else:
            charge = rawCharge
            voltage = rawVoltage

        if self.makeDerivatives:
            ## LEAN method - ICA
            dVidx = np.nonzero(
                np.diff(np.minimum.accumulate(rawVoltage), prepend=rawVoltage[0] + 1)
            )[0]
            v = rawVoltage[dVidx]
            dQ = np.hstack(
                [
                    rawCharge[dVidx[1:]] - rawCharge[dVidx[:-1]],
                    rawCharge[-1] - rawCharge[dVidx[-1]],
                ]
            )
            dV = np.hstack([v[1] - v[0], (v[2:] - v[:-2]) / 2, v[-1] - v[-2]])

            dQdV = dQ / dV
            ascIdx = np.argsort(v)
            v = v[ascIdx]
            dQdV = dQdV[ascIdx]

            windowsize = 201
            m = math.floor(windowsize / 2)
            kernel = np.ones(windowsize) / windowsize
            kernel = scipy.stats.norm.pdf(np.linspace(-1, 1, windowsize), scale=0.5)
            kernel /= sum(kernel)
            correctionWeights = np.cumsum(kernel[m + 1 :]) + np.sum(kernel[0:m])
            smootheddQdV = np.convolve(dQdV, kernel, "same")
            smootheddQdV[: len(correctionWeights)] /= correctionWeights
            smootheddQdV[-1 : -len(correctionWeights) - 1 : -1] /= correctionWeights

            if self.numSamples:
                icaX = np.linspace(v[0], v[-1], self.numSamples).tolist()
                icaY = np.interp(icaX, v, dQdV).tolist()
                smoothIcaY = np.interp(icaX, v, smootheddQdV).tolist()
            else:
                icaX = v.tolist()
                icaY = dQdV.tolist()
                smoothIcaY = smootheddQdV.tolist()

            # DVA
            dVdQvalid = np.nonzero(dQ)
            dVdQ = dV[dVdQvalid] / dQ[dVdQvalid]
            q = (rawCharge[np.hstack([dVidx[1:], -1])] + rawCharge[dVidx]) / 2
            q = q[dVdQvalid]

            smootheddVdQ = np.convolve(dVdQ, kernel, "same")
            smootheddVdQ[: len(correctionWeights)] /= correctionWeights
            smootheddVdQ[-1 : -len(correctionWeights) - 1 : -1] /= correctionWeights

            if self.numSamples:
                dvaX = np.linspace(q[0], q[-1], self.numSamples).tolist()
                dvaY = np.interp(dvaX, q, dVdQ).tolist()
                smoothDvaY = np.interp(dvaX, q, smootheddVdQ).tolist()
            else:
                dvaX = q.tolist()
                dvaY = dVdQ.tolist()
                smoothDvaY = smootheddVdQ.tolist()
        else:
            icaX = None
            icaY = None
            dvaX = None
            dvaY = None
            smoothIcaY = None
            smoothDvaY = None

        if test.object.type is None:
            soc = None
        else:
            soc = ((1 - charge / test.object.type.capacity) * 100).tolist()

        start = dchStep.start
        end = dchStep.end
        firstStep = dchStep.stepId
        lastStep = dchStep.stepId
        chargeCurrent = chaStep.current
        eocVoltage = chaStep.voltageEnd
        if pauseStep is None:
            pauseDuration = 0
            relaxedVoltage = None
        else:
            pauseDuration = pauseStep.duration
            relaxedVoltage = pauseStep.voltageEnd
        dischargeCurrent = dchStep.current
        dischargeDuration = dchStep.duration
        capacity = dchStep.charge
        eodVoltage = dchStep.voltageEnd
        age = dchStep.ageStart
        chargeThroughput = dchStep.dischargeStart
        if cvStep is None:
            cvDuration = 0
            cutoffCurrent = 0
        else:
            cvDuration = cvStep.duration
            cutoffCurrent = cvStep.currentEnd
        temperature = None
        if dchStep.temperatureMean is not None:
            temperature = dchStep.temperatureMean
        elif dchStep.temperatureMin is not None and dchStep.temperatureMax is not None:
            temperature = (dchStep.temperatureMin + dchStep.temperatureMax) / 2

        return DischargeQOCVEval(
            start=start,
            end=end,
            firstStep=firstStep,
            lastStep=lastStep,
            chargeCurrent=chargeCurrent,
            eocVoltage=eocVoltage,
            cvDuration=cvDuration,
            cutoffCurrent=cutoffCurrent,
            pauseDuration=pauseDuration,
            relaxedVoltage=relaxedVoltage,
            dischargeCurrent=dischargeCurrent,
            dischargeDuration=dischargeDuration,
            capacity=capacity,
            eodVoltage=eodVoltage,
            socNominal=soc,
            charge=charge.tolist(),
            voltage=voltage.tolist(),
            age=age,
            chargeThroughput=chargeThroughput,
            temperature=temperature,
            dvaX=dvaX,
            dvaY=dvaY,
            icaX=icaX,
            icaY=icaY,
            smoothDvaY=smoothDvaY,
            smoothIcaY=smoothIcaY,
            matchStart=chaStep.start,
            matchEnd=dchStep.end,
            starttime=(
                test.start + datetime.timedelta(seconds=start) if test.start else None
            ),
        )
