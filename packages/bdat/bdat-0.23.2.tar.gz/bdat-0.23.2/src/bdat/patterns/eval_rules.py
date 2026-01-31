from datetime import datetime
from typing import Type

import pytz

from bdat.entities.steps import Steplist
from bdat.resources.patterns.eval_pattern import EvalPattern

# TODO: temporary solution, this should be configured by database entities


def _get_pattern_args(steps: Steplist, evaltype: Type[EvalPattern]) -> dict:
    if steps.test.set is not None and steps.test.set.project.title == "J8027_DigiBatt":
        if evaltype.__name__ == "Captest":
            # avoid captest detection when setting SOC to 0% for aging
            return {
                "dischargeCurrent": (-1.1, -0.9),
                "ccRequired": False,
                "cvRequired": True,
            }

    return {}


try:
    import bdat.custom.eval_rules

    def get_pattern_args(steps: Steplist, evaltype: Type[EvalPattern]) -> dict:
        args = bdat.custom.eval_rules.get_pattern_args(steps, evaltype)
        if not args:
            args = _get_pattern_args(steps, evaltype)
        return args

except:
    get_pattern_args = _get_pattern_args
