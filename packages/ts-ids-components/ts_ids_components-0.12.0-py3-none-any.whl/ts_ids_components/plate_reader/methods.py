"""
This module contains components for plate reader methods or protocols.

For plate readers, users typically define what is known as a “method” or a "protocol" which outlines the
steps that are performed during an experiment.
These steps can be measurements, like absorbance of fluorescence readings, or other
actions on the plate, like shaking the plate.

The order in which steps are performed matters.
For instance, a scientist may want to first perform a specific measurement on a sample,
and then perform another measurement on the same sample.
When reviewing the experimental data, the order of the measurements is important context
that must be preserved to interpret the results.

When considering a method, there are a few levels of the hierarchy to consider:

- A method is the top level, and outlines a list of steps to follow.
- A step outlines a specific action or measurement(s) to be performed.
- A measurement setting outlines the instrument setup for a particular measurement performed by a step, of which there can be multiple.

Modeling Plate Reader Methods in IDS
=========================================

To capture this hierarchy within our IDSs, we define the following top-level arrays:

- ``methods``: Contains 1 item per method.
- ``protocol_steps``: Contains 1 item per step performed by a method.
- ``measurement_settings``: Contains 1 item per measurement setting used by the steps in the method.

To preserve which steps belong to which method, and which measurement settings belong to which step, primary-foreign keys are used to link these arrays.
Each item contains a primary key ``pk``, as well as the following foreign keys:

- Items in the ``protocol_steps`` array have a foreign key ``fk_method`` to the method they belong to.
- Items in the ``measurement_settings`` array have a foreign key ``fk_method`` and ``fk_protocol_step`` to the method and step they belong to.

The ``measurement_settings`` array can be customized depending on the types of measurements an IDS supports.
This is achieved through a structure similar to the ``System`` component.

In the example below, the ``MyMeasurementSettings`` class is defined to contain the fields which are common to all measurement settings by inheriting from ``MeasurementSetting``.
As well as these, the absorbance and fluorescence fields are added by inheriting from ``MeasurementSetting.Absorbance`` and ``MeasurementSetting.Fluorescence`` respectively.

.. literalinclude:: ../../../__tests__/unit/test_plate_reader_methods.py
    :pyobject: test_plate_reader_customized_methods
    :language: python
    :dedent: 4
    :start-after: doc-start
    :end-before: doc-end

If you wish to simply add all the measurement settings fields from the component for all modalities, you can use the ``PlateReaderMeasurementSetting`` type instead of ``MyMeasurementSettings`` above.
This contains all the fields for the supported modalities, including absorbance, fluorescence, luminescence, TRF and alpha technology.

Single vs Multi-step protocols
==============================

For multi-step protocols, the ``protocol_steps`` array will contain 1 item per step in a protocol.

For single-step protocols, it is recommended to still populate 1 item in the ``methods`` array for the protocol, and 1 item in the ``protocol_steps`` array for the step.
This ensures consistency in the structure of the IDS between singe and multi-step protocols, as well as ensuring the same SQL queries can be used for IDS of each type.

Endpoint vs Kinetic Steps
==============================

``protocol_steps`` contains a flat list of the steps that were performed by a method or protocol.
This includes both endpoint steps as well as kinetic cycles and their sub-protocols.
This step hierarchy is preserved by including a ``parent_step`` field, which contains the name of the parent step in the protocol, if this step belongs to a kinetic loop.

If a step is not a part of a kinetic sub-protocol, the ``parent_step`` field should not be defined, like in the first item in the ``protocol_steps`` array in the example below.

If the protocol contains a kinetic cycle, ``protocol_steps`` should contain:

- 1 item to act as the parent step for the kinetic cycle (the 2nd item in the example below).
- 1 item for each step in the kinetic sub-protocol, where the ``parent_step`` field is set to the name of the parent step (the 3rd and 4th items in the example below).

The ``kinetics`` object should also be defined for each of the parent and sub-protocol steps, containing the properties of the kinetic loop.

.. literalinclude:: ../../../__tests__/unit/snapshots/plate_reader_methods_endpoint_vs_kinetic_steps
    :language: json


Guidelines for extending these components
=========================================

Many plate readers will export metadata fields that are unique to the specific instrument.
Depending on the type of metadata, fields can be added to the component to capture this data in the following places:

- If a property applies to a whole protocol, e.g. a file path to the methods file, it belongs within ``methods``
- If a property applies to a particular measurement, e.g. an interval between well measurements, it belongs within ``measurement_settings``
- If a property belongs to a particular step in the protocol, but not related to a measurement, e.g. settings for a shake step, it belongs within ``protocol_steps``

Guidelines for linking results to items in these components
===========================================================

As previously mentioned, each of the ``methods``, ``protocol_steps``, and ``measurement_settings`` arrays contain a primary key ``pk``.

Depending on the type of result being harmonized, foreign keys to the items in these arrays can be used to link the results to the corresponding metadata:

- If a result refers to a particular measurement performed, the foreign key should be to the item in the ``measurement_settings`` array.
- If a result refers to a particular step in the protocol, such as an aggregation of measurements over multiple wavelengths, the foreign key should be to the item in the ``protocol_steps`` array.
- If a result refers to a whole protocol, such as a pass-fail quality control condition, the foreign key should be to the item in the ``methods`` array.

Methods Components
==================
"""

from enum import Enum

from ts_ids_core.annotations import Nullable, UUIDForeignKey, UUIDPrimaryKey
from ts_ids_core.schema import IdsElement, IdsField, RawValueUnit

# pylint: disable=too-many-ancestors

# Methods


class PlateReaderMethod(IdsElement):
    """A protocol followed during a plate reader experiment"""

    pk: UUIDPrimaryKey = IdsField(description="Primary key of a plate reader method")
    name: Nullable[str] = IdsField(description="The name of the method")
    id_: Nullable[str] = IdsField(alias="id", description="The ID of the method")


# Steps


class StepKinetics(IdsElement):
    """The kinetic metadata for the step"""

    number_of_cycles: Nullable[int] = IdsField(
        description="The number of cycles of the kinetic loop"
    )
    total_duration: RawValueUnit = IdsField(
        description="The total time of the kinetic loop"
    )
    interval: RawValueUnit = IdsField(
        description="The interval between cycles in the kinetic loop"
    )


class PlateReaderStep(IdsElement):
    """A step in a protocol"""

    pk: UUIDPrimaryKey = IdsField(description="Primary key of a step in the protocol")
    fk_method: UUIDForeignKey = IdsField(
        description="Foreign key to the method that the step belongs to",
        primary_key="/properties/methods/items/properties/pk",
    )
    parent_step: Nullable[str] = IdsField(
        description="Name of the parent step in the protocol, if this step belongs to a kinetic loop",
    )
    index: int = IdsField(description="The index of the step in the protocol")
    name: Nullable[str] = IdsField(description="The name of the step in the protocol")
    kinetics: StepKinetics = IdsField()


# Measurement Settings


class SingleChromatic(IdsElement):
    """Optical properties for a single chromatic e.g. filter or monochromator"""

    name: Nullable[str] = IdsField(
        description="The name of the filter or monochromator"
    )
    position: Nullable[str] = IdsField(
        description="Position of a filter in a container like a filter wheel"
    )
    bandwidth: RawValueUnit = IdsField(
        description="The range of frequencies around the target wavelength which are measured"
    )
    wavelength: RawValueUnit = IdsField(
        description="The target wavelength of the filter or monochromator"
    )


class Spectrum(IdsElement):
    """Spectrum or spectral scan properties

    Wavelength ranges are inclusive.
    """

    name: Nullable[str] = IdsField(description="The name of the spectrum")
    start: RawValueUnit = IdsField(description="The start of the spectrum")
    end: RawValueUnit = IdsField(description="The end of the spectrum")
    step: RawValueUnit = IdsField(description="The step of the spectrum")


class OpticalSetup(str, Enum):
    """The type of optical setup for a measurement"""

    MONOCHROMATOR = "monochromator"
    FILTER = "filter"
    SPECTRUM = "spectrometer"
    SPECTRAL_SCAN = "spectral scan"
    BROAD_SPECTRUM = "broad spectrum"


class Chromatics(Spectrum, SingleChromatic):
    """Properties of a chromatic setup, e.g. a filter or spectrum"""

    name: Nullable[str] = IdsField(description="The name of the optical setup used")
    type_: Nullable[str] = IdsField(  # Use OpticalSetup to populate if possible
        alias="type",
        description="The type of optical setup, e.g. filter or spectrum",
    )


class Gain(IdsElement):
    """The gain of a detector"""

    mode: Nullable[str] = IdsField(description="The gain mode used for the measurement")
    raw_value: Nullable[str] = IdsField(
        description="The raw, untransformed value from the primary data."
    )
    value: Nullable[float] = IdsField(
        description="The gain value transformed to a numerical value"
    )
    unit: Nullable[str] = IdsField(description="The unit of the gain value")


class LuminescenceMetadata(IdsElement):
    """Properties of a luminescence based measurement"""

    emission: Chromatics = IdsField(description="The emission optical setup")


class FluorescenceMetadata(LuminescenceMetadata):
    """Properties of a fluorescence based measurement"""

    excitation: Chromatics = IdsField(description="The excitation optical setup")
    number_of_flashes: Nullable[int] = IdsField(
        description="The number of flashes used for the measurement"
    )
    excitation_time: RawValueUnit = IdsField(
        description="The time for which the sample is illuminated by the excitation source"
    )


class PathLengthCorrection(IdsElement):
    """Properties for path length correction"""

    test: SingleChromatic = IdsField(
        description="The test wavelength for the path length correction"
    )
    reference: SingleChromatic = IdsField(
        description="The reference wavelength for the path length correction"
    )


class IntegrationTimes(IdsElement):
    """Properties for the integration times of a measurement"""

    integration_delay: RawValueUnit = IdsField(
        description="The delay before the integration of the detected signal begins"
    )
    integration_time: RawValueUnit = IdsField(
        description="The duration of the signal integration"
    )


class Channel(str, Enum):
    """The channel of a measurement"""

    PARALLEL = "parallel"
    PERPENDICULAR = "perpendicular"
    POLARIZATION = "polarization"


class Modality(str, Enum):
    """The modality of a measurement"""

    ABSORBANCE = "absorbance"
    FLUORESCENCE = "fluorescence"
    LUMINESCENCE = "luminescence"
    TRF = "time_resolved_fluorescence"
    ALPHA_TECHNOLOGY = "alpha_technology"


class EndpointKineticType(str, Enum):
    """The type of a measurement"""

    ENDPOINT = "endpoint"
    KINETIC = "kinetic"


class MeasurementSetting(IdsElement):
    """The settings related to a particular measurement by a step in the protocol"""

    class Absorbance(IdsElement):
        """Properties of an absorbance based measurement"""

        absorbance: Chromatics = IdsField(
            description="The absorbance filter or spectrum"
        )
        pathlength_correction: PathLengthCorrection = IdsField(
            description="The path length correction metadata for the measurement"
        )

    class Fluorescence(FluorescenceMetadata):
        """Properties of a fluorescence based measurement"""

        # Use the Channel Enum for standard values, for dual emission use the raw channel name
        channel: Nullable[str] = IdsField(
            description=(
                "The channel of the measurement when there can be multiple, e.g. for"
                "fluorescence polarization measurements the channels are parallel or perpendicular"
            )
        )

    class Luminescence(LuminescenceMetadata):
        """Properties of a luminescence based measurement"""

    class TRF(FluorescenceMetadata, IntegrationTimes):
        """Properties of a time-resolved fluorescence based measurement"""

    class Alpha(FluorescenceMetadata, IntegrationTimes):
        """Properties of an alpha technology based measurement"""

        alpha_type: Nullable[str] = IdsField(
            description="The type of alpha technology used for the measurement"
        )

    pk: UUIDPrimaryKey = IdsField(description="Primary key of a measurement setting")
    fk_protocol_step: UUIDForeignKey = IdsField(
        description="Foreign key to the step that this measurement setting belongs to",
        primary_key="/properties/protocol_steps/items/properties/pk",
    )
    fk_method: UUIDForeignKey = IdsField(
        description="Foreign key to the method that this measurement setting belongs to",
        primary_key="/properties/methods/items/properties/pk",
    )
    index: int = IdsField(
        description="The index of the measurement setting in the step"
    )

    # Use the Modality Enum for standard values
    modality: Nullable[str] = IdsField(description="The modality of the measurement")
    # Use the EndpointKineticType Enum for standard values
    type_: Nullable[str] = IdsField(
        description="The type of the measurement", alias="type"
    )

    measurement_duration: RawValueUnit = IdsField(
        description="The duration of the measurement"
    )
    number_of_readings: Nullable[int] = IdsField(
        description="The number of readings for a measurement"
    )

    gain: Gain = IdsField(description="The gain of the detector")
    dynamic_range: Nullable[str] = IdsField(
        description="The dynamic range of the detector"
    )
    optics: Nullable[str] = IdsField(
        description="The name or position of the optics used for the measurement"
    )


class PlateReaderMeasurementSetting(
    MeasurementSetting,
    MeasurementSetting.Absorbance,
    MeasurementSetting.Fluorescence,
    MeasurementSetting.Luminescence,
    MeasurementSetting.TRF,
    MeasurementSetting.Alpha,
):
    """The settings related to a particular measurement by a step in the protocol/method"""
