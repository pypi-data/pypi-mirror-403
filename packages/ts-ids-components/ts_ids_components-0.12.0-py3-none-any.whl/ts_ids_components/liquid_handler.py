"""
This module contains components for liquid handler IDSs.

A liquid handler is an automated laboratory instrument designed for the precise
manipulation and distribution of liquid volumes. It operates using a set of programmed
instructions to aspirate (draw up) and dispense (release) liquid samples with high
accuracy. Liquid handlers are instrumental in various scientific disciplines, such as
genomics, drug discovery, and analytical chemistry, where handling precise quantities
of liquids is crucial.

Liquid handlers employ robotic arms equipped with specialized tools, such as pipettes
or probes, to perform various liquid-handling tasks. The system is typically programmed
with specific protocols that dictate the volumes to be aspirated or dispensed, as well
as the locations within well plates or other containers. The precision of liquid
handlers is attributed to their ability to control factors like pipette speed,
immersion depth, and dispensing rate. This level of precision is crucial in applications
such as high-throughput screening, where numerous samples need consistent and accurate
handling for reliable experimental outcomes. The automation provided by liquid handlers
significantly enhances efficiency in laboratories, minimizing human error and
facilitating complex liquid manipulations at a scale unattainable through manual
methods.

Two significant aspects of data usage patterns in liquid handlers include sample/liquid
transfers tracking and consumables usage tracking.

Sample tracking involves monitoring the movement and status of liquid samples throughout
the liquid handling process. It helps track each sample from its original well position
to the final destination well, along with all the intermediate wells it moves through
throughout the process. It enables researchers to trace the history and handling of each
sample, facilitates reproducibility and ensures the reliability of experimental results
and provides a record for quality control and audit purposes.

Consumables usage tracking involves monitoring the usage of the liquid handler's
physical components, including pipettes, tips, and other accessories. It provides a
detailed history of the types of pipettes and tips used, along with the frequency of
their usage and unload events, enables precise tracking of consumables, such as pipette
tips, facilitating inventory management, helps prevent contamination by tracking the
usage of disposable components and supports compliance with regulatory requirements by
maintaining thorough records of instrument performance and consumable usage.

Typically, a specific instrument IDS can have more fields than the ones present in
these models. For example, if the instrument pipetting step has additional attributes,
such as a pod name for example, this field can be added by inheriting from the
PipettingStep class:

.. code-block:: python

    class CustomPipettingStep(PipettingStep):
        pod_name: Nullable[str]
"""

from typing import List

from ts_ids_core.annotations import Nullable
from ts_ids_core.base.ids_element import IdsElement
from ts_ids_core.base.ids_field import IdsField
from ts_ids_core.schema import Holder, Location, RawValueUnit, Sample, Time


class LiquidHandlerHolder(Holder):
    """Liquid handler holder with associated deck position"""

    deck_position: Nullable[str] = IdsField(
        description="Position of the holder on a deck"
    )


class LiquidHandlerLocation(Location):
    """Liquid handler location in a liquid handler holder"""

    barcode: Nullable[str] = IdsField(
        description="Barcode associated with a tube location in a tube rack"
    )
    holder: LiquidHandlerHolder = IdsField(
        description="Information about the holder to which the location belongs to"
    )


class LiquidHandlerSample(Sample):
    """Properties of a liquid handler sample at a specific location"""

    location: LiquidHandlerLocation = IdsField(
        description="Liquid handler sample location properties"
    )


class Tip(IdsElement):
    """Properties of a tip used in a pipetting step"""

    id_: Nullable[str] = IdsField(alias="id", description="Identifier for the tip")
    type_: Nullable[str] = IdsField(
        alias="type", description="Type or model of the tip"
    )
    number: Nullable[int] = IdsField(description="Index of the current tip")


class PipettingStep(IdsElement):
    """Pipetting step component"""

    time: Time = IdsField(description="The time when the pipetting step occurs")
    operation_type: Nullable[str] = IdsField(
        description="Pipetting step operation type, such as 'Aspirate' or 'Dispense'"
    )
    tip: Tip = IdsField(
        description="Information about the tip used for the pipetting step"
    )
    device_name: Nullable[str] = IdsField(
        description="Device used for performing the pipetting step, such as a flexible "
        "channel arm or a multi-channel arm"
    )
    sample: LiquidHandlerSample = IdsField(
        description="Source or destination sample with its associated location for the"
        " pipetting step."
    )
    volume: RawValueUnit = IdsField(
        description="The liquid volume aspirated or dispensed during the pipetting step"
    )
    liquid_class: Nullable[str] = IdsField(
        description="The broad category or group of the liquid sample, such as solvent,"
        " buffer, or reagent."
    )
    liquid_type: Nullable[str] = IdsField(
        description="The specific instance or formulation of the liquid sample within "
        "its liquid class"
    )


class LiquidTransfer(IdsElement):
    """Liquid transfer component"""

    id_: Nullable[str] = IdsField(
        alias="id", description="Unique identifier for the liquid transfer operation"
    )
    source: LiquidHandlerSample = IdsField(
        description="The source sample with its associated location from where liquid"
        " is transferred"
    )
    destination: LiquidHandlerSample = IdsField(
        description="The destination sample with its associated location where liquid"
        " is transferred to"
    )
    volume: RawValueUnit = IdsField(
        description="The volume of liquid being transferred"
    )
    liquid_class: Nullable[str] = IdsField(
        description="The broad category or group of the liquid sample, such as solvent,"
        "buffer, or reagent."
    )
    liquid_type: Nullable[str] = IdsField(
        description="The specific instance or formulation of the liquid sample within "
        "its liquid class"
    )


class TipUnloadEvent(IdsElement):
    """Tip unload event"""

    time: Time = IdsField(
        description="Timestamp indicating when the tip unload event occurred"
    )
    tip_type: Nullable[str] = IdsField(description="Type or model of the unloaded tip")
    tip_count: Nullable[int] = IdsField(
        description="Number of tips unloaded during the event"
    )
    unload_box_barcode: Nullable[str] = IdsField(
        description="Barcode of the box or container to which tips are unloaded"
    )


class TipUsage(IdsElement):
    """Tip usage component"""

    tip_type: Nullable[str] = IdsField(
        description="Type or model of the tip for which usage statistics are recorded"
    )
    tip_unload_events: List[TipUnloadEvent] = IdsField(
        description="List of individual tip unload events"
    )
    total_tip_unload_events: Nullable[int] = IdsField(
        description="Total count of tip unload events for the specified tip type"
    )
    total_unloaded_tips: Nullable[int] = IdsField(
        description="Total count of tips unloaded for the specified tip type"
    )
