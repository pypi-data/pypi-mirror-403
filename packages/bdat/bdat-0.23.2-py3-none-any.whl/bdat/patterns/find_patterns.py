import typing

from bdat.entities.patterns.discharge_capacity_eval import DischargeCapacityEval
from bdat.entities.patterns.test_eval import TestEval
from bdat.entities.steps.steplist import Steplist
from bdat.entities.test.cycling_data import CyclingData
from bdat.resources.patterns import EvalPattern


def find_patterns(
    steplist: Steplist, patterntypes: typing.List[EvalPattern], data: CyclingData
) -> TestEval:
    if steplist.test.object.type is None:
        raise Exception("Unknown battery species")
    testresult = []
    for pt in patterntypes:
        pattern = pt.pattern(steplist.test.object.type)
        matches = pattern.match(steplist)
        test_evals = [
            pt.eval(steplist.test, match, steplist[match.start : match.end], data)
            for match in matches
        ]
        for e in test_evals:
            if isinstance(e, DischargeCapacityEval):
                dch_step = steplist[e.lastStep]
                dch_step.capacity = abs(e.capacity)
                dch_step.socEnd = 0
                if len(steplist) > dch_step.stepId + 1:
                    steplist.continue_soc(
                        dch_step.socEnd, dch_step.capacity, dch_step.stepId + 1
                    )
        testresult += test_evals
    testeval = TestEval(
        f"test eval - {steplist.test.title}", steplist.test, steplist, testresult
    )
    for tr in testresult:
        tr.testEval = testeval
    return testeval
