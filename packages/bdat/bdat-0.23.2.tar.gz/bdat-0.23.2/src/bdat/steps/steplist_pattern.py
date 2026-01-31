import math
import typing
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

if typing.TYPE_CHECKING:
    from bdat.steps.step_pattern import StepPattern

from bdat.entities.steps.step import Step
from bdat.entities.steps.steplist import Steplist


@dataclass
class Match:
    start: int
    end: int
    length: int
    pattern: "SteplistPattern"
    steps: typing.List[Step]
    subMatches: typing.List["Match"] = field(default_factory=list)

    def get_matches(self, pattern: "SteplistPattern"):
        for m in self.subMatches:
            if m.pattern is pattern:
                yield m
            for x in m.get_matches(pattern):
                yield x


class SteplistPattern(ABC):
    def match(self, steplist: Steplist) -> typing.Iterator[Match]:
        firstStep = 0
        for i in range(len(steplist.steps)):
            if i < firstStep:
                continue
            match = self.match_at_position(steplist.steps, i)
            if match is not None:
                yield match
                firstStep = i + match.length

    @abstractmethod
    def match_at_position(self, steplist: list[Step], position: int) -> Match | None:
        raise NotImplementedError

    @abstractmethod
    def to_str(self) -> str:
        pass


class Series(SteplistPattern):
    patterns: list[SteplistPattern]
    duration: typing.Tuple[float, float] | None = None

    def __init__(
        self,
        patterns: list[SteplistPattern],
        duration: typing.Tuple[float, float] | None = None,
    ):
        self.patterns = patterns
        self.duration = duration

    def match_at_position(self, steplist: list[Step], position: int) -> Match | None:
        length = 0
        subMatches = []
        for i in range(len(self.patterns)):
            if length + position >= len(steplist):
                return None
            m = self.patterns[i].match_at_position(steplist, position + length)
            if m is not None:
                length += m.length
                subMatches.append(m)
            else:
                return None
        if self.duration:
            totalDuration = sum(
                [s.duration for s in steplist[position : position + length]]
            )
            if not (
                totalDuration >= self.duration[0] and totalDuration <= self.duration[1]
            ):
                return None
        return Match(
            position,
            position + length,
            length,
            self,
            steplist[position : position + length],
            subMatches,
        )

    def to_str(self) -> str:
        return "[" + "\n".join([p.to_str() for p in self.patterns]) + "]"


class Repeat(SteplistPattern):
    pattern: SteplistPattern
    min: int | None
    max: int | None

    def __init__(
        self, pattern: SteplistPattern, min: int | None = None, max: int | None = None
    ):
        self.pattern = pattern
        self.min = min
        self.max = max

    def match_at_position(self, steplist: list[Step], position: int) -> Match | None:
        matchLength = 0
        repeats = 0
        subMatches = []
        while position + matchLength < len(steplist):
            m = self.pattern.match_at_position(steplist, position + matchLength)
            if m is None:
                break
            matchLength += m.length
            subMatches.append(m)
            repeats += 1
            if self.max and repeats >= self.max:
                break
        if self.min and repeats < self.min:
            return None
        else:
            return Match(
                position,
                position + matchLength,
                matchLength,
                self,
                steplist[position : position + matchLength],
                subMatches,
            )

    def to_str(self) -> str:
        min = self.min
        max: typing.Any = self.max
        if not min:
            min = 0
        if not max:
            max = "-"
        return f"{self.pattern.to_str()}{{{min},{max}}}"


class RepeatSteps(SteplistPattern):
    pattern: SteplistPattern
    conditions: """typing.List[
        typing.Tuple[
            StepPattern,
            typing.Dict[str, typing.Tuple[float | None, float | None]]
        ]
    ]"""
    min: int | None
    max: int | None

    def __init__(
        self,
        pattern: SteplistPattern,
        conditions: "typing.List[typing.Tuple[StepPattern, typing.Dict[str, typing.Tuple[float | None, float | None]]]]",
        min: int | None = None,
        max: int | None = None,
    ):
        self.pattern = pattern
        self.conditions = conditions
        self.min = min
        self.max = max

    def __check_conditions(
        self, steplist: list[Step], matchA: Match, matchB: Match
    ) -> bool:
        if not (matchA.pattern is matchB.pattern):
            return False
        if not (matchA.length == matchB.length):
            return False
        for p, c in self.conditions:
            if p is matchA.pattern:
                stepA = steplist[matchA.start]
                stepB = steplist[matchB.start]
                for key, (rel_tol, abs_tol) in c.items():
                    if rel_tol is None:
                        rel_tol = 1e-9
                    if abs_tol is None:
                        abs_tol = 0
                    if not math.isclose(
                        getattr(stepA, key),
                        getattr(stepB, key),
                        rel_tol=rel_tol,
                        abs_tol=abs_tol,
                    ):
                        return False
        if not (len(matchA.subMatches) == len(matchB.subMatches)):
            return False
        return all(
            [
                self.__check_conditions(steplist, subA, subB)
                for subA, subB in zip(matchA.subMatches, matchB.subMatches)
            ]
        )

    def match_at_position(self, steplist: list[Step], position: int) -> Match | None:
        matchLength = 0
        repeats = 0
        subMatches = []
        firstMatch = None
        while position + matchLength < len(steplist):
            m = self.pattern.match_at_position(steplist, position + matchLength)
            if m is None:
                break
            if firstMatch is not None:
                if not self.__check_conditions(steplist, firstMatch, m):
                    break
            else:
                firstMatch = m
            matchLength += m.length
            subMatches.append(m)
            repeats += 1
            if self.max and repeats >= self.max:
                break
        if self.min and repeats < self.min:
            return None
        else:
            return Match(
                position,
                position + matchLength,
                matchLength,
                self,
                steplist[position : position + matchLength],
                subMatches,
            )

    def to_str(self) -> str:
        min = self.min
        max: typing.Any = self.max
        if not min:
            min = 0
        if not max:
            max = "-"
        return f"{self.pattern.to_str()}{{{min},{max}}}"


class Optional(Repeat):
    def __init__(self, pattern: SteplistPattern):
        super().__init__(pattern, 0, 1)


class Or(SteplistPattern):
    patterns: list[SteplistPattern]

    def __init__(
        self,
        *patterns: SteplistPattern,
    ):
        self.patterns = list(patterns)

    def match_at_position(self, steplist: list[Step], position: int) -> Match | None:
        for i in range(len(self.patterns)):
            m = self.patterns[i].match_at_position(steplist, position)
            if m is not None:
                return Match(
                    position,
                    position + m.length,
                    m.length,
                    self,
                    steplist[position : position + m.length],
                    [m],
                )
        return None

    def to_str(self) -> str:
        return f"or({','.join([p.to_str() for p in self.patterns])})"
