from abc import ABC, abstractmethod
from typing import Tuple

import bdat.steps.steplist_pattern as steplist_pattern
from bdat.entities.steps.step import CCStep, CPStep, CVStep, Pause, Step


class StepPattern(steplist_pattern.SteplistPattern, ABC):
    @abstractmethod
    def matchStep(self, step: Step) -> bool:
        raise NotImplementedError

    def match_at_position(
        self, steplist: list[Step], position: int
    ) -> steplist_pattern.Match | None:
        if self.matchStep(steplist[position]):
            return steplist_pattern.Match(
                position, position + 1, 1, self, steplist[position : position + 1], []
            )
        else:
            return None


class StepType(StepPattern):
    stepType: type[Step]

    def __init__(self, stepType: type[Step]):
        self.stepType = stepType

    def matchStep(self, step: Step) -> bool:
        return isinstance(step, self.stepType)

    def to_str(self) -> str:
        return f"type: {self.stepType.__name__}"


class CCProperties(StepPattern):
    duration: Tuple[float, float] | None
    current: Tuple[float, float] | None
    voltageStart: Tuple[float, float] | None
    voltageEnd: Tuple[float, float] | None

    def __init__(
        self,
        duration: Tuple[float, float] | None = None,
        current: Tuple[float, float] | None = None,
        voltageStart: Tuple[float, float] | None = None,
        voltageEnd: Tuple[float, float] | None = None,
    ):
        self.duration = duration
        self.current = current
        self.voltageStart = voltageStart
        self.voltageEnd = voltageEnd

    def matchStep(self, step: Step) -> bool:
        if not isinstance(step, CCStep):
            return False
        if self.current and not (
            step.current >= self.current[0] and step.current <= self.current[1]
        ):
            return False
        if self.duration and not (
            step.duration >= self.duration[0] and step.duration <= self.duration[1]
        ):
            return False
        if self.voltageStart and not (
            step.voltageStart >= self.voltageStart[0]
            and step.voltageStart <= self.voltageStart[1]
        ):
            return False
        if self.voltageEnd and not (
            step.voltageEnd >= self.voltageEnd[0]
            and step.voltageEnd <= self.voltageEnd[1]
        ):
            return False
        return True

    def to_str(self) -> str:
        s = "type: CCStep"
        if self.duration:
            s += f", duration: ({self.duration[0]}, {self.duration[1]})"
        if self.current:
            s += f", current: ({self.current[0]}, {self.current[1]})"
        if self.voltageStart:
            s += f", voltageStart: ({self.voltageStart[0]}, {self.voltageStart[1]})"
        if self.voltageEnd:
            s += f", voltageEnd: ({self.voltageEnd[0]}, {self.voltageEnd[1]})"
        return s


class CVProperties(StepPattern):
    duration: Tuple[float, float] | None
    voltage: Tuple[float, float] | None
    currentStart: Tuple[float, float] | None
    currentEnd: Tuple[float, float] | None

    def __init__(
        self,
        duration: Tuple[float, float] | None = None,
        voltage: Tuple[float, float] | None = None,
        currentStart: Tuple[float, float] | None = None,
        currentEnd: Tuple[float, float] | None = None,
    ):
        self.duration = duration
        self.voltage = voltage
        self.currentStart = currentStart
        self.currentEnd = currentEnd

    def matchStep(self, step: Step) -> bool:
        if not isinstance(step, CVStep):
            return False
        if self.voltage and not (
            step.voltage >= self.voltage[0] and step.voltage <= self.voltage[1]
        ):
            return False
        if self.duration and not (
            step.duration >= self.duration[0] and step.duration <= self.duration[1]
        ):
            return False
        if self.currentStart and not (
            step.currentStart >= self.currentStart[0]
            and step.currentStart <= self.currentStart[1]
        ):
            return False
        if self.currentEnd and not (
            step.currentEnd >= self.currentEnd[0]
            and step.currentEnd <= self.currentEnd[1]
        ):
            return False
        return True

    def to_str(self) -> str:
        s = "type: CVStep"
        if self.duration:
            s += f", duration: ({self.duration[0]}, {self.duration[1]})"
        if self.currentStart:
            s += f", currentStart: ({self.currentStart[0]}, {self.currentStart[1]})"
        if self.currentEnd:
            s += f", currentEnd: ({self.currentEnd[0]}, {self.currentEnd[1]})"
        if self.voltage:
            s += f", voltage: ({self.voltage[0]}, {self.voltage[1]})"
        return s


class CPProperties(StepPattern):
    duration: Tuple[float, float] | None
    power: Tuple[float, float] | None
    voltageStart: Tuple[float, float] | None
    voltageEnd: Tuple[float, float] | None
    currentStart: Tuple[float, float] | None
    currentEnd: Tuple[float, float] | None

    def __init__(
        self,
        duration: Tuple[float, float] | None = None,
        power: Tuple[float, float] | None = None,
        voltageStart: Tuple[float, float] | None = None,
        voltageEnd: Tuple[float, float] | None = None,
        currentStart: Tuple[float, float] | None = None,
        currentEnd: Tuple[float, float] | None = None,
    ):
        self.duration = duration
        self.power = power
        self.voltageStart = voltageStart
        self.voltageEnd = voltageEnd
        self.currentStart = currentStart
        self.currentEnd = currentEnd

    def matchStep(self, step: Step) -> bool:
        if not isinstance(step, CPStep):
            return False
        if self.power and not (
            step.power >= self.power[0] and step.power <= self.power[1]
        ):
            return False
        if self.duration and not (
            step.duration >= self.duration[0] and step.duration <= self.duration[1]
        ):
            return False
        if self.voltageStart and not (
            step.voltageStart >= self.voltageStart[0]
            and step.voltageStart <= self.voltageStart[1]
        ):
            return False
        if self.voltageEnd and not (
            step.voltageEnd >= self.voltageEnd[0]
            and step.voltageEnd <= self.voltageEnd[1]
        ):
            return False
        if self.currentStart and not (
            step.currentStart >= self.currentStart[0]
            and step.currentStart <= self.currentStart[1]
        ):
            return False
        if self.currentEnd and not (
            step.currentEnd >= self.currentEnd[0]
            and step.currentEnd <= self.currentEnd[1]
        ):
            return False
        return True

    def to_str(self) -> str:
        s = "type: CPStep"
        if self.duration:
            s += f", duration: ({self.duration[0]}, {self.duration[1]})"
        if self.power:
            s += f", power: ({self.power[0]}, {self.power[1]})"
        if self.voltageStart:
            s += f", voltageStart: ({self.voltageStart[0]}, {self.voltageStart[1]})"
        if self.voltageEnd:
            s += f", voltageEnd: ({self.voltageEnd[0]}, {self.voltageEnd[1]})"
        if self.currentStart:
            s += f", currentStart: ({self.currentStart[0]}, {self.currentStart[1]})"
        if self.currentEnd:
            s += f", currentEnd: ({self.currentEnd[0]}, {self.currentEnd[1]})"
        return s


class PauseProperties(StepPattern):
    duration: Tuple[float, float] | None
    voltageStart: Tuple[float, float] | None
    voltageEnd: Tuple[float, float] | None

    def __init__(
        self,
        duration: Tuple[float, float] | None = None,
        voltageStart: Tuple[float, float] | None = None,
        voltageEnd: Tuple[float, float] | None = None,
    ):
        self.duration = duration
        self.voltageStart = voltageStart
        self.voltageEnd = voltageEnd

    def matchStep(self, step: Step) -> bool:
        if not isinstance(step, Pause):
            return False
        if self.duration and not (
            step.duration >= self.duration[0] and step.duration <= self.duration[1]
        ):
            return False
        if self.voltageStart and not (
            step.voltageStart >= self.voltageStart[0]
            and step.voltageStart <= self.voltageStart[1]
        ):
            return False
        if self.voltageEnd and not (
            step.voltageEnd >= self.voltageEnd[0]
            and step.voltageEnd <= self.voltageEnd[1]
        ):
            return False
        return True

    def to_str(self) -> str:
        s = "type: Pause"
        if self.duration:
            s += f", duration: ({self.duration[0]}, {self.duration[1]})"
        if self.voltageStart:
            s += f", voltageStart: ({self.voltageStart[0]}, {self.voltageStart[1]})"
        if self.voltageEnd:
            s += f", voltageEnd: ({self.voltageEnd[0]}, {self.voltageEnd[1]})"
        return s


class StepProperties(StepPattern):
    stepType: type[Step] | None
    duration: Tuple[float, float] | None
    current: Tuple[float, float] | None
    voltage: Tuple[float, float] | None

    def __init__(
        self,
        stepType: type[Step] | None = None,
        duration: Tuple[float, float] | None = None,
        current: Tuple[float, float] | None = None,
        voltage: Tuple[float, float] | None = None,
    ):
        self.stepType = stepType
        self.duration = duration
        self.current = current
        self.voltage = voltage

    def matchStep(self, step: Step) -> bool:
        if self.stepType and not isinstance(step, self.stepType):
            return False
        if self.duration and not (
            step.duration >= self.duration[0] and step.duration <= self.duration[1]
        ):
            return False
        if self.voltage:
            if isinstance(step, CCStep):
                if (
                    step.voltageStart < self.voltage[0]
                    or step.voltageStart > self.voltage[1]
                    or step.voltageEnd < self.voltage[0]
                    or step.voltageEnd > self.voltage[1]
                ):
                    return False
            elif isinstance(step, CVStep):
                if step.voltage < self.voltage[0] or step.voltage > self.voltage[1]:
                    return False
            else:
                raise NotImplementedError()
        if self.current:
            if isinstance(step, CCStep):
                if step.current < self.current[0] or step.current > self.current[1]:
                    return False
            elif isinstance(step, CVStep):
                if (
                    step.currentStart < self.current[0]
                    or step.currentStart > self.current[1]
                    or step.currentEnd < self.current[0]
                    or step.currentEnd > self.current[1]
                ):
                    return False
            else:
                raise NotImplementedError()
        return True

    def to_str(self) -> str:
        if self.stepType:
            s = f"type: {self.stepType.__name__}"
        else:
            s = "type: Any"
        if self.duration:
            s += f", duration: ({self.duration[0]}, {self.duration[1]})"
        if self.current:
            s += f", current: ({self.current[0]}, {self.current[1]})"
        if self.voltage:
            s += f", voltage: ({self.voltage[0]}, {self.voltage[1]})"
        return s


class StepValue(StepPattern):
    min: float
    max: float

    def __init__(self, min: float, max: float):
        self.min = min
        self.max = max

    def matchStep(self, step: Step) -> bool:
        if isinstance(step, CCStep):
            return step.current >= self.min and step.current <= self.max
        elif isinstance(step, CVStep):
            return step.voltage >= self.min and step.voltage <= self.max
        else:
            raise NotImplementedError


class StepDuration(StepPattern):
    min: float
    max: float

    def __init__(self, min: float, max: float):
        self.min = min
        self.max = max

    def matchStep(self, step: Step) -> bool:
        return step.duration >= self.min and step.duration <= self.max


class And(StepPattern):
    a: StepPattern
    b: StepPattern

    def __init__(self, a: StepPattern, b: StepPattern):
        self.a = a
        self.b = b

    def matchStep(self, step: Step) -> bool:
        return self.a.matchStep(step) and self.b.matchStep(step)

    def match_at_position(
        self, steplist: list[Step], position: int
    ) -> steplist_pattern.Match | None:
        matchA = self.a.match_at_position(steplist, position)
        matchB = self.b.match_at_position(steplist, position)
        if matchA is not None and matchB is not None:
            return steplist_pattern.Match(
                position,
                position + 1,
                1,
                self,
                steplist[position : position + 1],
                [matchA, matchB],
            )
        else:
            return None

    def to_str(self) -> str:
        return f"and({self.a.to_str()},{self.b.to_str()})"


class Or(StepPattern):
    a: StepPattern
    b: StepPattern

    def __init__(self, a: StepPattern, b: StepPattern):
        self.a = a
        self.b = b

    def matchStep(self, step: Step) -> bool:
        return self.a.matchStep(step) or self.b.matchStep(step)

    def match_at_position(
        self, steplist: list[Step], position: int
    ) -> steplist_pattern.Match | None:
        matchA = self.a.match_at_position(steplist, position)
        matchB = self.b.match_at_position(steplist, position)
        if matchA is not None or matchB is not None:
            return steplist_pattern.Match(
                position,
                position + 1,
                1,
                self,
                steplist[position : position + 1],
                [x for x in [matchA, matchB] if x is not None],
            )
        else:
            return None

    def to_str(self) -> str:
        return f"or({self.a.to_str()},{self.b.to_str()})"


class Not(StepPattern):
    a: StepPattern

    def __init__(self, a: StepPattern):
        self.a = a

    def matchStep(self, step: Step) -> bool:
        return not self.a.matchStep(step)

    def to_str(self) -> str:
        return "!" + self.a.to_str()
