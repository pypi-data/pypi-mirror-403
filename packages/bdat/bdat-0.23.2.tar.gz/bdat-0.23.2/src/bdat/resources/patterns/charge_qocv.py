import datetime
import math
import typing
from dataclasses import dataclass
from typing import Tuple

import numpy as np
import scipy

from bdat.entities import BatterySpecies, Cycling
from bdat.entities.patterns import ChargeQOCVEval
from bdat.entities.steps.step import Step
from bdat.entities.test.cycling_data import CyclingData
from bdat.resources.patterns.eval_pattern import EvalPattern
from bdat.steps.step_pattern import CCProperties, PauseProperties
from bdat.steps.steplist_pattern import Match, Optional, Series, SteplistPattern
from bdat.tools.misc import make_range


@dataclass
class ChargeQOCV(EvalPattern):
    eocVoltage: float | Tuple[float, float] | None = None
    eodVoltage: float | Tuple[float, float] | None = None
    chargeCurrent: float | Tuple[float, float] | None = None
    dischargeCurrent: float | Tuple[float, float] | None = None
    relaxationTime: float | Tuple[float, float] | None = None
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
            [self.chargeCurrent, (0.0, 0.2 * species.capacity)],
            (0.95, 1.05),
        )
        dischargeCurrent = make_range(
            [
                self.dischargeCurrent,
                (-1e9, 0.0),
            ],
            (-1.05, -0.95),
        )
        relaxationTime = make_range([self.relaxationTime, (0, 1e9)], (0.95, 1.05))

        self.dischargeStep = CCProperties(
            current=dischargeCurrent, voltageEnd=eodVoltage
        )
        self.pauseStep = PauseProperties(duration=relaxationTime)
        self.chargeStep = CCProperties(current=chargeCurrent, voltageEnd=eocVoltage)

        return Series([self.dischargeStep, Optional(self.pauseStep), self.chargeStep])

    def eval_needs_data(self) -> bool:
        return True

    def eval(
        self,
        test: Cycling,
        match: Match,
        steps: typing.List[Step],
        data: CyclingData | None,
    ) -> ChargeQOCVEval:
        if data is None:
            raise Exception("Eval needs test data")

        dchStep = next(match.get_matches(self.dischargeStep)).steps[0].asCC()
        pauseMatch = next(match.get_matches(self.pauseStep), None)
        pauseStep = None if pauseMatch is None else pauseMatch.steps[0].asPause()
        chaStep = next(match.get_matches(self.chargeStep)).steps[0].asCC()

        rawVoltage = data.voltage[chaStep.rowStart : chaStep.rowEnd]
        rawCharge = (
            data.charge[chaStep.rowStart : chaStep.rowEnd]
            - data.charge[chaStep.rowStart]
        )
        if self.numSamples:
            charge = np.linspace(0, 1, self.numSamples) * abs(chaStep.charge)
            voltage = np.interp(charge, rawCharge, rawVoltage)
        else:
            charge = rawCharge
            voltage = rawVoltage

        if self.makeDerivatives:
            ## LEAN method - ICA
            dVidx = np.nonzero(
                np.diff(np.maximum.accumulate(rawVoltage), prepend=rawVoltage[0] - 1)
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
            soc = (charge / test.object.type.capacity * 100).tolist()

        start = chaStep.start
        end = chaStep.end
        firstStep = chaStep.stepId
        lastStep = chaStep.stepId
        chargeCurrent = chaStep.current
        chargeDuration = chaStep.duration
        eocVoltage = chaStep.voltageEnd
        pauseDuration = None if pauseStep is None else pauseStep.duration
        relaxedVoltage = None if pauseStep is None else pauseStep.voltageEnd
        dischargeCurrent = dchStep.current
        dischargeDuration = dchStep.duration
        capacity = chaStep.charge
        eodVoltage = dchStep.voltageEnd
        age = chaStep.ageStart
        chargeThroughput = chaStep.dischargeStart
        temperature = None
        if dchStep.temperatureMean is not None:
            temperature = dchStep.temperatureMean
        elif dchStep.temperatureMin is not None and dchStep.temperatureMax is not None:
            temperature = (dchStep.temperatureMin + dchStep.temperatureMax) / 2

        return ChargeQOCVEval(
            start=start,
            end=end,
            firstStep=firstStep,
            lastStep=lastStep,
            chargeCurrent=chargeCurrent,
            chargeDuration=chargeDuration,
            eocVoltage=eocVoltage,
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
            matchStart=dchStep.start,
            matchEnd=chaStep.end,
            starttime=(
                test.start + datetime.timedelta(seconds=chaStep.start)
                if test.start
                else None
            ),
        )
