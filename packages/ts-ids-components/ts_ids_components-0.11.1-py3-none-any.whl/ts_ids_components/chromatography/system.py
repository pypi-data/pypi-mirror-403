from enum import Enum

from ts_ids_core.annotations import (
    NullableString,
    Required,
    UUIDForeignKey,
    UUIDPrimaryKey,
)
from ts_ids_core.base.ids_element import IdsElement
from ts_ids_core.base.ids_field import IdsField
from ts_ids_core.lakehouse_schema import System as _System
from ts_ids_core.schema import RawValueUnit


class Module(IdsElement):
    """Properties of the modules in the chromatography unit. Modules may include
    e.g. column compartments, detectors, autosamplers, or pumps."""

    pk: UUIDPrimaryKey = IdsField(description="Primary key for system modules.")
    fk_system: UUIDForeignKey = IdsField(
        primary_key="/properties/systems/items/properties/pk",
        description="Foreign key to the system.",
    )
    name: NullableString = IdsField(
        description="Module name as specified by the audit trail."
    )
    manufacturer: NullableString = IdsField(description="Module manufacturer.")
    type: NullableString = IdsField(description="Type of module.")
    detector_type: NullableString = IdsField(
        description=(
            "Type of detector; defined only when the module is identified as a detector."
        ),
    )
    part_number: NullableString = IdsField(
        description="Part number or model number of the module."
    )
    serial_number: NullableString = IdsField(description="Module serial number.")
    firmware_version: NullableString = IdsField(description="Module firmware version.")
    driver_version: NullableString = IdsField(description="Module driver version.")


class Column(IdsElement):
    """Properties of the column(s) in the chromatography system."""

    pk: UUIDPrimaryKey = IdsField(
        description="Primary key for columns in the chromatography system."
    )
    fk_system: UUIDForeignKey = IdsField(
        primary_key="/properties/systems/items/properties/pk",
        description="Foreign key to the system.",
    )
    fk_module: UUIDForeignKey = IdsField(
        description="A foreign key that links a column to its respective column compartment",
        primary_key="/properties/modules/items/properties/pk",
    )
    name: NullableString = IdsField(
        description="Name for the column entered by the user."
    )
    product_number: NullableString = IdsField(
        description="Manufacturer's product/catalog number for the column."
    )
    serial_number: NullableString = IdsField(description="Column serial number.")
    batch_number: NullableString = IdsField(
        description="Manufacturer's batch number for column production."
    )
    void_volume: RawValueUnit = IdsField(
        description=(
            "Void volume of the column, equal to the volume of mobile phase in the column."
        ),
    )
    length: RawValueUnit = IdsField(description="Column length.")
    diameter: RawValueUnit = IdsField(description="Column diameter.")
    max_pressure: RawValueUnit = IdsField(
        description="Manufacturer's maximum rating for the column pressure."
    )
    max_temperature: RawValueUnit = IdsField(
        description="Manufacturer's maximum rating for the column temperature."
    )


class ChromatographyType(str, Enum):
    """Possible values are Ion Chromatography, 2D High Performance Liquid Chromatography, High Performance Liquid Chromatography, or Gas Chromatography."""

    ION_CHROMATOGRAPHY = "Ion Exchange Chromatography"
    HPLC = "High Performance Liquid Chromatography"
    TWO_D_HPLC = "2D High Performance Liquid Chromatography"
    GC = "Gas Chromatography"


class System(_System):
    """
    Metadata regarding the equipment, software, and firmware used in a run of an
    instrument or experiment.
    """

    # This a minimal system component containing primary keys which are needed for the
    # chromatography methods component.
    pk: UUIDPrimaryKey = IdsField(description="Primary key for the system.")
    type_: Required[NullableString] = IdsField(
        alias="type",
        description="Type of chromatography system.",
        json_schema_extra={
            "example_values": [type_.value for type_ in ChromatographyType]
        },
    )
