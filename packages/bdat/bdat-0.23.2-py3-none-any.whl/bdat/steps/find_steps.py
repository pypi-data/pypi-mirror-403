from typing import List, Type, cast

import numpy as np

from bdat.entities.steps.step import CCStep, CPStep, CVStep, Pause, Step
from bdat.entities.steps.steplist import Steplist
from bdat.entities.test.cycling_data import CyclingData
from bdat.tools.cli import print_info


def steps_from_columns(data: CyclingData, *columns: str) -> Steplist:
    columnList = list(columns)
    stepId = 0
    rowStart = 0
    stepValues = data.df[columnList].iloc[0]
    steplist: List[Step] = []
    for rowIdx, row in data.df.iterrows():
        rowIdx = cast(int, rowIdx)
        if np.any(row[columnList] != stepValues):
            steplist.append(_get_step(data, stepId, rowStart, rowIdx))
            stepId += 1
            rowStart = rowIdx
            stepValues = row[columnList]
    steplist.append(_get_step(data, stepId, rowStart, len(data.df)))
    return Steplist(f"test steps - {data.test.title}", steplist, data.test)


def _get_step(
    data: CyclingData,
    stepId: int,
    rowStart: int,
    rowEnd: int,
    steptype: Type | None = None,
) -> Step:
    current = data.current
    voltage = data.voltage
    start = data.time[rowStart]
    end = data.time[rowEnd - 1]
    dI = current[rowEnd - 1] - current[rowStart]
    dV = voltage[rowEnd - 1] - voltage[rowStart]
    dt = end - start
    charge = data.diffcharge[rowEnd - 1] - data.diffcharge[rowStart]

    if data.temperature is not None:
        temperature = data.temperature
        temperatureStart = temperature[rowStart]
        temperatureEnd = temperature[rowEnd - 1]
        temperatureMin = temperature[rowStart:rowEnd].min()
        temperatureMax = temperature[rowStart:rowEnd].max()
        temperatureMean = temperature[rowStart:rowEnd].mean()
    else:
        temperatureStart = None
        temperatureEnd = None
        temperatureMin = None
        temperatureMax = None
        temperatureMean = None

    if steptype is None:
        if np.abs(dI) > np.abs(dV):
            steptype = CVStep
        else:
            steptype = CCStep

    if steptype == CCStep:
        if np.all(current[rowStart:rowEnd] == 0):
            steptype = Pause

    useMedian = rowEnd - rowStart >= 100

    if steptype == CVStep:
        values = voltage[rowStart:rowEnd]
        vMean = values.mean()
        vError = values - vMean
        return CVStep(
            stepId,
            start,
            end,
            rowStart,
            rowEnd,
            dt,
            charge,
            temperatureStart,
            temperatureEnd,
            temperatureMin,
            temperatureMax,
            temperatureMean,
            np.max(np.abs(vError)),
            np.sqrt(np.mean(np.square(vError))),
            vMean,
            current[rowStart],
            (
                np.median(current[rowEnd - 5 : rowEnd])
                if useMedian
                else current[rowEnd - 1]
            ),
        )
    elif steptype == CCStep:
        values = current[rowStart:rowEnd]
        vMean = values.mean()
        vError = values - vMean
        return CCStep(
            stepId,
            start,
            end,
            rowStart,
            rowEnd,
            dt,
            charge,
            temperatureStart,
            temperatureEnd,
            temperatureMin,
            temperatureMax,
            temperatureMean,
            np.max(np.abs(vError)),
            np.sqrt(np.mean(np.square(vError))),
            vMean,
            voltage[rowStart],
            (
                np.median(voltage[rowEnd - 5 : rowEnd])
                if useMedian
                else voltage[rowEnd - 1]
            ),
        )
    elif steptype == Pause:
        values = current[rowStart:rowEnd]
        vMean = values.mean()
        vError = values - vMean
        return Pause(
            stepId,
            start,
            end,
            rowStart,
            rowEnd,
            dt,
            charge,
            temperatureStart,
            temperatureEnd,
            temperatureMin,
            temperatureMax,
            temperatureMean,
            np.max(np.abs(vError)),
            np.sqrt(np.mean(np.square(vError))),
            voltage[rowStart],
            (
                np.median(voltage[rowEnd - 5 : rowEnd])
                if useMedian
                else voltage[rowEnd - 1]
            ),
        )
    elif steptype == CPStep:
        values = data.power[rowStart:rowEnd]
        vMean = values.mean()
        vError = values - vMean
        return CPStep(
            stepId,
            start,
            end,
            rowStart,
            rowEnd,
            dt,
            charge,
            temperatureStart,
            temperatureEnd,
            temperatureMin,
            temperatureMax,
            temperatureMean,
            np.max(np.abs(vError)),
            np.sqrt(np.mean(np.square(vError))),
            vMean,
            voltage[rowStart],
            voltage[rowEnd - 1],
            current[rowStart],
            current[rowEnd - 1],
        )

    else:
        raise NotImplementedError()


def find_steps(
    data: CyclingData,
    maxCurrentError=0.05,
    maxCurrentRMSE=0.002,
    maxVoltageError=0.005,
    maxVoltageRMSE=0.00125,
    maxPowerError=0.01,
    maxPowerRMSE=0.002,
) -> Steplist:
    steps: List[Step] = []
    stepId = 0
    startIdx = 0
    while startIdx < len(data.df):
        step = __find_best_step(
            data,
            maxCurrentError,
            maxCurrentRMSE,
            maxVoltageError,
            maxVoltageRMSE,
            maxPowerError,
            maxPowerRMSE,
            startIdx,
            stepId,
        )
        if step is None:
            startIdx += 1
            continue

        for _ in range(5):
            if startIdx + 1 < len(data.df):
                step2 = __find_best_step(
                    data,
                    maxCurrentError,
                    maxCurrentRMSE,
                    maxVoltageError,
                    maxVoltageRMSE,
                    maxPowerError,
                    maxPowerRMSE,
                    startIdx + 1,
                    stepId,
                )
                if step2 is None:
                    break
                if step2.duration > step.duration:
                    step = step2
                elif (
                    step2.duration > 0.95 * step.duration
                    and step.rmse is not None
                    and step2.rmse is not None
                    and step2.rmse / step2.duration < step.rmse / step.duration
                ):
                    step = step2
                startIdx += 1
            else:
                break
        if step.duration > 0.0:
            steps.append(step)
            stepId += 1
        startIdx = step.rowEnd
    return Steplist(f"test steps - {data.test.title}", steps, data.test)


find_linear_steps = find_steps


def __find_best_step(
    data: CyclingData,
    maxCurrentError: float,
    maxCurrentRMSE: float,
    maxVoltageError: float,
    maxVoltageRMSE: float,
    maxPowerError: float,
    maxPowerRMSE: float,
    startIdx: int,
    stepId: int,
) -> Step | None:
    steptype: Type | None = None
    if data.current[startIdx] == 0:
        stepLength = np.argmax(data.current[startIdx:] != 0).item()
        if stepLength == 0:
            stepLength = data.current.size - startIdx
        steptype = Pause
    else:
        currentLength = _find_step_length(
            data.current[startIdx:], maxCurrentError, maxCurrentRMSE
        )
        voltageLength = _find_step_length(
            data.voltage[startIdx:], maxVoltageError, maxVoltageRMSE
        )
        powerLength = _find_step_length(
            data.power[startIdx:], maxPowerError, maxPowerRMSE
        )
        stepLength = max(currentLength, voltageLength, powerLength)
        if currentLength == stepLength:
            steptype = CCStep
        elif voltageLength == stepLength:
            steptype = CVStep
        elif powerLength == stepLength:
            steptype = CPStep
    if stepLength == 0:
        return None
    return _get_step(data, stepId, startIdx, startIdx + stepLength, steptype)


def _find_step_length(values: np.ndarray, maxError: float, maxRMSE: float) -> int:
    minLength = 0
    # maxLength = values.size
    searchLength = min(500, values.size - 1)
    maxLength = searchLength
    while maxLength >= searchLength and maxLength < values.size:
        searchLength = min(2 * searchLength, values.size)
        maxLength = searchLength
        vSearch = values[:searchLength]
        if len(vSearch) == 0:
            return 0
        maxLength = np.argmax(np.abs(vSearch - values[0]) > 2 * maxError).item()
        if maxLength == 0:
            maxLength = searchLength
        while minLength != maxLength:
            testLength = int(((minLength + maxLength) / 2) + 0.5)
            v = vSearch[:testLength]
            m = np.mean(v)
            rmse = np.sqrt(np.mean(np.square(v - m)))
            if np.all(np.abs(v - m) <= maxError) and rmse <= maxRMSE:
                minLength = testLength
            else:
                maxLength = testLength - 1
    return maxLength
