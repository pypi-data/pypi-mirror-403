import datetime
import typing

import pandas as pd

from bdat.database.storage.entity import Entity
from bdat.database.storage.storage import Storage
from bdat.entities.group import EvalGroup
from bdat.entities.patterns import (
    ChargeQOCVEval,
    DischargeCapacityEval,
    DischargeQOCVEval,
    PulseEval,
    TestinfoEval,
)
from bdat.entities.plots import Plotdata
from bdat.plots.plot import plot
from bdat.tools.misc import make_round_function, round_to_n


@plot("evalgroup")
def plot_evalgroup(storage: Storage, evalgroup: Entity) -> Plotdata:
    if not isinstance(evalgroup, EvalGroup):
        raise Exception("Invalid resource type")
    capdata = []
    resdata = []
    qocvdata = []
    ctpdata = []

    qocvId = 0

    for pe in evalgroup.evaldata:
        if not isinstance(
            pe,
            (
                PulseEval,
                DischargeCapacityEval,
                ChargeQOCVEval,
                DischargeQOCVEval,
                TestinfoEval,
            ),
        ):
            continue
        e = pe.testEval
        if e is None:
            raise Exception("Missing TestEval in PatternEval")
        if pe.chargeThroughput is None:
            raise Exception("Missing charge throughput")
        if pe.age is None:
            raise Exception("Missing age")
        speciesName = None
        species = e.test.object.type
        if species:
            speciesName = f"{species.manufacturer} {species.typename}"
            if species.version:
                speciesName += f" ({species.version})"
        date = (
            datetime.datetime(0, 0, 0) if e.test.start is None else e.test.start
        ) + datetime.timedelta(0, pe.start)
        cellname = e.test.object.title
        ctp = pe.chargeThroughput
        if isinstance(pe, DischargeCapacityEval):
            capdata.append(
                {
                    "capacity": pe.capacity,
                    "specimen": cellname,
                    "species": speciesName,
                    "test": e.test.title,
                    "testeval": e.res_id_or_raise().to_str(),
                    "steplist": e.steps.res_id_or_raise().to_str(),
                    "age": pe.age,
                    "ctp": ctp,
                    "time": date,
                    "current": pe.dischargeCurrent,
                }
            )
        elif isinstance(pe, PulseEval):
            resdata.append(
                {
                    "impedance": pe.impedance,
                    "specimen": cellname,
                    "species": speciesName,
                    "test": e.test.title,
                    "testeval": e.res_id_or_raise().to_str(),
                    "steplist": e.steps.res_id_or_raise().to_str(),
                    "age": pe.age,
                    "ctp": ctp,
                    "time": date,
                    "current": pe.current,
                    "duration": pe.duration,
                    "soc": pe.soc,
                }
            )
        elif isinstance(pe, (DischargeQOCVEval, ChargeQOCVEval)):
            if pe.socNominal is not None:
                socRange = (min(*pe.socNominal), max(*pe.socNominal))
                socFactor = (socRange[1] - socRange[0]) / 100
                socActual = [(x - socRange[0]) / socFactor for x in pe.socNominal]
            else:
                socActual = None
            maxCharge = max(pe.charge)
            chargePercentage = [x / maxCharge * 100 for x in pe.charge]
            current = None
            if isinstance(pe, DischargeQOCVEval):
                current = abs(pe.dischargeCurrent)
            elif isinstance(pe, ChargeQOCVEval):
                current = pe.chargeCurrent
            qocvdata.append(
                pd.DataFrame(
                    {
                        "charge": pe.charge,
                        "chargePercentage": chargePercentage,
                        "socNominal": pe.socNominal,
                        "socActual": socActual,
                        "voltage": pe.voltage,
                        "specimen": e.test.object.title,
                        "species": speciesName,
                        "test": e.test.title,
                        "date": e.test.start,
                        "current": current,
                        "temperature": pe.temperature,
                        "testset": e.test.set.title if e.test.set is not None else None,
                        "qocvId": qocvId,
                    }
                )
            )
            qocvId += 1
        elif isinstance(pe, TestinfoEval):
            ctpdata.append(
                {
                    "specimen": cellname,
                    "species": speciesName,
                    "test": e.test.title,
                    "testeval": e.res_id_or_raise().to_str(),
                    "steplist": e.steps.res_id_or_raise().to_str(),
                    "age": pe.age,
                    "ctp": ctp,
                    "time": date,
                }
            )

    return Plotdata(
        "evalgroup plot",
        evalgroup,
        "evalgroup",
        {
            "capacity": pd.DataFrame.from_records(capdata).to_dict(orient="records"),
            "resistance": pd.DataFrame.from_records(resdata).to_dict(orient="records"),
            "qocv": pd.concat(qocvdata).to_dict(orient="records"),
            "ctp": pd.DataFrame.from_records(ctpdata).to_dict(orient="records"),
        },
    )
