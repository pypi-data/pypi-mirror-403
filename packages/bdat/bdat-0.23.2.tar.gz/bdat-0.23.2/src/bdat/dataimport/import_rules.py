import bdat.entities as entities
from bdat.entities.dataspec.charge_spec import SeparateColumns
from bdat.entities.dataspec.column_spec import ColumnSpec
from bdat.entities.dataspec.data_spec import DataSpec
from bdat.entities.dataspec.unit import Unit
from bdat.exceptions import MissingDataspecException, NoCyclingDataException
from bdat.resources.dataspec.bdf import BDFDataSpec
from bdat.resources.dataspec.bm import BMDataSpec
from bdat.resources.dataspec.bm_converted import BMConvertedDataSpec
from bdat.resources.dataspec.neware import NewareAhjoDataSpec


def could_be_cycling(test: entities.Cycling) -> bool:
    if test.title.endswith("NoName_VA") or test.title.endswith("NoName_MSG"):
        return False
    if test.title.startswith("aux_data_"):
        return False
    if test.tool is not None and test.tool.title.startswith("Kreis"):
        if test.parent is None:
            return False
        if not "Format01" in test.title:
            return False
    if test.tool is not None and test.tool.title.lower().startswith("eis"):
        return False
    return True


# TODO: temporary solution, this should actually look at the data and the resulting dataspec should be pushed to the database
# TODO: this could directly return a CyclingData instance


def _get_dataspec(test: entities.Cycling, df) -> DataSpec:
    if test.title.endswith("NoName_VA") or test.title.endswith("NoName_MSG"):
        raise NoCyclingDataException(test)
    try:
        spec: DataSpec = NewareAhjoDataSpec(test, df)
        return spec
    except:
        pass
    try:
        temperatureName = "T1#C1#D" if "T1#C1#D" in df.columns else None
        spec = BMDataSpec(timeUnit=Unit.MILLI, temperatureName=temperatureName)
        if spec.tryOnTest(df):
            return spec
    except:
        pass
    try:
        temperatureName = "T1#degC" if "T1#degC" in df.columns else None
        spec = BMConvertedDataSpec(
            df, timeUnit=Unit.MILLI, temperatureName=temperatureName
        )
        if spec.tryOnTest(df):
            return spec
    except:
        pass
    try:
        spec = BDFDataSpec(df)
        if spec.tryOnTest(df):
            return spec
    except:
        pass

    raise MissingDataspecException(test, df.columns)


try:
    import bdat.custom.import_rules

    def get_dataspec(test: entities.Cycling, df) -> DataSpec:
        spec = bdat.custom.import_rules.get_dataspec(test, df)
        if not spec:
            spec = _get_dataspec(test, df)
        return spec

except:
    get_dataspec = _get_dataspec
