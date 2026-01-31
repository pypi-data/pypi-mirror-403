import pandas as pd

from bdat.database.storage.entity import Entity
from bdat.database.storage.storage import Storage
from bdat.entities.group import EvalGroup
from bdat.entities.patterns import (
    ChargeQOCVEval,
    CPDischargeQOCVEval,
    DischargeQOCVEval,
)
from bdat.entities.plots import Plotdata
from bdat.plots.plot import plot


@plot("qocv")
def plot_qocv(storage: Storage, evalgroup: Entity) -> Plotdata:
    if not isinstance(evalgroup, EvalGroup):
        raise Exception("Invalid resource type")
    data = []

    for pe in evalgroup.evaldata:
        # if not isinstance(pe, (DischargeQOCVEval, ChargeQOCVEval)):
        if not isinstance(pe, CPDischargeQOCVEval):
            continue
        e = pe.testEval
        if e is None:
            raise Exception("Missing TestEval in PatternEval")
        speciesName = None
        species = e.test.object.type
        if species:
            speciesName = f"{species.manufacturer} {species.typename}"
            if species.version:
                speciesName += f" ({species.version})"
        cRate = None
        if species is not None and species.capacity is not None:
            cRate = abs(pe.dischargeCurrent / species.capacity)
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
        data.append(
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
                    "power": pe.dischargePower,
                    "cRate": cRate,
                    "temperature": pe.temperature,
                    "testset": e.test.set.title if e.test.set is not None else None,
                }
            )
        )

    df = pd.concat(data)
    return Plotdata(f"qocv plot", evalgroup, "qocv", {"qocv": df})
