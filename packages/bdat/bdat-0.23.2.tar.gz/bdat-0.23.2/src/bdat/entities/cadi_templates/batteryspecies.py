import typing
from dataclasses import dataclass

from . import geometry, material
from .typeofobject import TypeOfObject


@dataclass
class BatterySpecies(TypeOfObject):
    parent: "BatterySpecies | None" = None
    geometry: "geometry.Geometry | None" = None
    anodeChemistry: "material.Material | None" = None
    cathodeChemistry: "material.Material | None" = None
    manufacturer: "str | None" = None
    typename: "str | None" = None
    version: "str | None" = None
    capacity: "float | None" = None
    minimumVoltage: "float | None" = None
    maximumVoltage: "float | None" = None
    endOfDischargeVoltage: "float | None" = None
    endOfChargeVoltage: "float | None" = None
    internalResistance: "float | None" = None
    countinuousChargeCurrent: "float | None" = None
    peakChargeCurrent: "float | None" = None
    continuousDischargeCurrent: "float | None" = None
    peakDischargeCurrent: "float | None" = None
    nominalCurrent: "float | None" = None
    minimumChargeTemperature: "float | None" = None
    maximumChargeTemperature: "float | None" = None
    minimumDischargeTemperature: "float | None" = None
    maximumDischargeTemperature: "float | None" = None
    weight: "float | None" = None
    energyDensity: "float | None" = None
