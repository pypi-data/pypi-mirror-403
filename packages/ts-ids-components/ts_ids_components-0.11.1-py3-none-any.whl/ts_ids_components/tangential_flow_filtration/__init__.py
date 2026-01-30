"""
This module contains components for the Tangential Flow Filtration results data model.

Tangential Flow Filtration (TFF) is a filtration technique where the fluid flows tangentially
across the surface of a filter membrane rather than directly into it.

Data from a tangential flow filtration device comes typically in time series formats since a filtration
takes time to execute. This include multiple datapoints for each run.

Because of the multiple data points, a parquet file is used to store the data. The parquet file is referenced
via file name and file ID in the `TangentialFlowFiltrationResults` class component.

The `Result` class component also holds high level time series data measurements from a tangential flow filtration
device as well as the associated foreign keys.

This data model encapsulates high-level time series data measurements from a tangential flow
filtration device. It includes:
    - A reference to the parquet file containing the detailed time series data. file_name and file_id
    - Basic time data (minimum and maximum timestamps) via the `MinMaxTime` class.
    - A comprehensive results component (`TangentialFlowFiltrationResults`) that links experimental run
    information to its corresponding parquet file through various foreign key relationships (run, method, system, user, and sample).

The IDS serves as the central document, providing a primary key for each experimental run,
which is used to associate additional data (such as recipe, system, user, alarms, etc.) via
foreign key relationships. This design ensures that the results component accurately references
and locates the corresponding parquet file containing all detailed time series data.

The resulting IDS JSON will look like this after calling `instance.model_dump_json(indent=2)`:

.. literalinclude:: ../../../__tests__/unit/snapshots/tangential_flow_instance.json
    :language: json
"""

from ts_ids_core.annotations import NullableString, UUIDForeignKey
from ts_ids_core.base.ids_element import IdsElement
from ts_ids_core.base.ids_field import IdsField


class MinMaxTime(IdsElement):
    """
    Time data from a tangential flow filtration device.
    """

    min_timestamp: NullableString = IdsField(
        description="Minimum time data from the raw file. Equivalent to a start timestamp"
    )
    max_timestamp: NullableString = IdsField(
        description="Maximum time data from the raw file. Equivalent to an end timestamp"
    )


class StartEndTime(IdsElement):
    """
    Start and end time data from a tangential flow filtration device.
    Preferred method to use for time-series data.
    """

    start_timestamp: NullableString = IdsField(
        description="Start time data from the raw file. Equivalent to a minimum timestamp."
    )
    end_timestamp: NullableString = IdsField(
        description="End time data from the raw file. Equivalent to a maximum timestamp."
    )


class RawTime(StartEndTime, MinMaxTime):
    """
    Raw time data that includes both start/end and min/max timestamps.
    """


class Time(StartEndTime, MinMaxTime):
    """
    Time data from a tangential flow filtration device.
    Inherits both start/end timestamps and min/max timestamps.
    """

    raw: RawTime = IdsField(description="Raw time data from the raw file.")


class TangentialFlowFiltrationResults(IdsElement):
    """
    Time Series data measurements from tangential flow filtration device
    and all associated data.
    """

    file_name: str = IdsField(
        description="The name of the parquet file containing the data."
    )
    file_id: str = IdsField(
        description="The file ID of the parquet file containing the data."
    )
    fk_run: UUIDForeignKey = IdsField(
        primary_key="/properties/runs/items/properties/pk",
        description="Foreign key relating the parquet file back to the experiment run.",
    )
    fk_method: UUIDForeignKey = IdsField(
        primary_key="/properties/methods/items/properties/pk",
        description="Foreign key relating the parquet file back to the method.",
    )
    fk_sample: UUIDForeignKey = IdsField(
        primary_key="/properties/samples/items/properties/pk",
        description="Foreign key relating the parquet file back to the sample.",
    )
    time: Time
