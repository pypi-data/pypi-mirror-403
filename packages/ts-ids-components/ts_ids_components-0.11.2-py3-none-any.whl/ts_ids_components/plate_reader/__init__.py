"""
This module contains components for plate reader IDSs.

Plate reader samples and datacubes
==================================

A common data usage pattern for plate reader data is to read measurement data, such
as absorbance or fluorescence values, and analyse them along with metadata about the
sample which was being measured.

To do this, use the :external+ts-ids-core:ref:`samples common component <component_samples>`
to store information about the sample in each well of the plate, including a
:external+ts-ids-core:py:data:`UUID primary key <ts_ids_core.annotations.UUIDPrimaryKey>`
field named ``"pk"``.
In :external+ts-ids-core:ref:`datacubes <datacubes>`, include a foreign key
to ``samples`` with the name ``fk_samples``.
This structure is defined in :py:class:`PlateReaderSchema` below, and that class can be
used as a starting point for defining plate reader schemas.

When populating data into a plate reader IDS, store data from each well in a separate
element of the ``datacubes`` array.

This level of granularity makes it possible for data from many different plate readers
to be stored in the same format, which makes downstream data access easier.

Here is an example of defining a schema which inherits from
:py:class:`PlateReaderSchema` and populating it in Python.
This shows data being manually populated in the script itself, but in typical usage,
this data would be parsed from a raw data file.

.. literalinclude:: ../../../__tests__/unit/test_plate_reader.py
    :pyobject: test_complete_plate_reader_schema
    :language: python
    :dedent: 4
    :start-after: doc-start
    :end-before: doc-end

Then, the data could be dumped to JSON by calling ``instance.model_dump_json(indent=2)``
The resulting IDS JSON looks like this:

.. literalinclude:: ../../../__tests__/unit/snapshots/plate_reader_schema_demo
    :language: json

Other plate reader components
=============================

There are components in this module which don't have a predefined top-level path in
an IDS because they may be used in multiple places throughout a plate reader schema,
and their location in the schema may vary across data sources.

Typically, a specific instrument IDS can have more fields than the ones present in
these models. For example, if the instrument filter has an additional value-unit field,
such as a reference wavelength, this field can be added by inheriting from the Filter
component:

.. code-block:: python

    class ReferenceFilter(Filter):
        reference: ValueUnit

"""

from enum import Enum
from typing import List

from ts_ids_core.annotations import (
    Nullable,
    NullableString,
    Required,
    UUIDForeignKey,
    UUIDPrimaryKey,
    fixed_length,
)
from ts_ids_core.base.ids_element import IdsElement
from ts_ids_core.base.ids_field import IdsField
from ts_ids_core.schema import (
    DataCube,
    Dimension,
    Measure,
    Sample,
    System,
    TetraDataSchema,
    Time,
    ValueUnit,
)
from typing_extensions import Annotated, Literal

from ts_ids_components.plate_reader.methods import (
    PlateReaderMeasurementSetting,
    PlateReaderMethod,
    PlateReaderStep,
)

# Light sources


class LightSource(IdsElement):
    """Definition of a general light source system"""

    type_: Nullable[str] = IdsField(alias="type", description="Light source type")
    system: System = IdsField(description="Light source system information")


class Lamp(LightSource):
    """Lamp light source"""

    power: ValueUnit = IdsField(description="Nominal lamp power")


class LED(LightSource):
    """Light Emitting Diode light source

    Related Open Microscopy Environment model:
    https://www.openmicroscopy.org/Schemas/Documentation/Generated/OME-2016-06/ome_xsd.html#LightEmittingDiode
    """

    power: ValueUnit = IdsField(description="Nominal LED power")


# Optics


class Filter(IdsElement):
    """Optical filter properties"""

    position: Nullable[str] = IdsField(
        description="Position of this filter in a container like a filter wheel"
    )
    bandwidth: ValueUnit = IdsField(
        description="The range of frequencies associated with this filter"
    )
    wavelength: ValueUnit = IdsField(
        description="Characteristic wavelength of this filter"
    )


class BeamSplitter(System):
    """Beamsplitter properties"""


# Detection


class DetectorSystem(System, System.Id):
    """Definition of a detector system"""


# Sample environment


class EnvironmentRun(IdsElement):
    """Measured environment during a run"""

    measured_temperature: ValueUnit = IdsField(
        description="Measured temperature during a run"
    )


# Measurement protocol


class ShakingStep(IdsElement):
    """Shaker methods and metadata"""

    mode: Nullable[str] = IdsField(
        description="Shaking mode, such as 'orbital' or 'linear'"
    )
    speed: ValueUnit = IdsField(
        description="Shaking speed, the angular speed or frequency of shaking"
    )
    time: Time = IdsField(description="Shaking timing")


class InjectionStep(IdsElement):
    """Injection method for a single injection, including pump and volume settings"""

    pump_id: NullableString = IdsField(description="Identifier for pump being used")
    flow_rate: ValueUnit = IdsField(description="Flow speed of the injector pump")
    volume: ValueUnit = IdsField(description="Volume of injection")
    time: Time = IdsField(description="Injection timing")


class MeasurementPattern(IdsElement):
    """The measurement pattern, including which plate is being measured, which wells are
    measured, and in what order
    """

    plate: Nullable[str] = IdsField("Identifier for the plate being measured")
    wells: List[str] = IdsField(
        description="References to the wells being measured, in order"
    )


class MeasurementPatternByArea(MeasurementPattern):
    """Measurement pattern for plate readers which specify a plate area to measure"""

    area: Nullable[str] = IdsField(
        description="An area of the plate as a string, e.g. 'A1-F4'"
    )
    reading_direction: str = IdsField(
        description=("A description of the direction that wells are read from a plate")
    )


# Samples


class PlateReaderSample(Sample):
    """A sample stored in a well on a plate"""

    pk: UUIDPrimaryKey


# Datacubes


class PlateReaderDimensionNames(str, Enum):
    """A limited set of possible names for plate reader dimensions"""

    TIME = "time"
    WAVELENGTH = "wavelength"
    EXCITATION_WAVELENGTH = "excitation wavelength"
    EMISSION_WAVELENGTH = "emission wavelength"


class PlateReaderDimension(Dimension):
    """A plate reader dimension with a limited set of possible names"""

    name: Nullable[str]  # Use the PlateReaderDimensionNames enum for standard names


class Measure2D(Measure):
    """A two-dimensional datacube measure"""

    value: Required[List[List[Nullable[float]]]]


class Measure3D(Measure):
    """A three-dimensional datacube measure"""

    value: Required[List[List[List[Nullable[float]]]]]


class PlateReaderDatacube2D(DataCube):
    """A plate reader datacube containing two dimensions and one measure.

    The dimensions must be `time` and `wavelength`
    """

    fk_sample: UUIDForeignKey = IdsField(
        description="A foreign key linking datacubes to samples[*].",
        primary_key="/properties/samples/items/properties/pk",
    )
    fk_protocol_step: UUIDForeignKey = IdsField(
        description="A foreign key linking datacubes to protocol_steps[*].",
        primary_key="/properties/protocol_steps/items/properties/pk",
    )
    fk_method: UUIDForeignKey = IdsField(
        description="A foreign key linking datacubes to methods[*].",
        primary_key="/properties/methods/items/properties/pk",
    )
    dimensions: Required[Annotated[List[PlateReaderDimension], fixed_length(2)]]
    measures: Required[Annotated[List[Measure2D], fixed_length(1)]]


class PlateReaderDatacube3D(DataCube):
    """A plate reader datacube containing three dimensions and one measure."""

    fk_sample: UUIDForeignKey = IdsField(
        description="A foreign key linking datacubes to samples[*].",
        primary_key="/properties/samples/items/properties/pk",
    )
    fk_protocol_step: UUIDForeignKey = IdsField(
        description="A foreign key linking datacubes to protocol_steps[*].",
        primary_key="/properties/protocol_steps/items/properties/pk",
    )
    fk_method: UUIDForeignKey = IdsField(
        description="A foreign key linking datacubes to methods[*].",
        primary_key="/properties/methods/items/properties/pk",
    )

    dimensions: Required[Annotated[List[PlateReaderDimension], fixed_length(3)]]
    measures: Required[Annotated[List[Measure3D], fixed_length(1)]]


# Top-level schema including samples, datacubes and methods paths


class PlateReaderSchema(TetraDataSchema):
    """A schema for a plate reader."""

    methods: List[PlateReaderMethod]
    protocol_steps: List[PlateReaderStep]
    measurement_settings: List[PlateReaderMeasurementSetting]
    samples: List[PlateReaderSample]
    datacubes: List[PlateReaderDatacube2D]
