"""
This module contains the schema for chromatography IDSs.

Chromatography IDSs contain information about the chromatography system, modules, columns, methods, mobile phases, gradient steps, detector channels, peaks and datacubes.
====================

The chromatography common component is designed to store data about the following use cases:

A common data usage pattern in chromatography is analyzing measurement data or the chromatogram produced
by each detector channel as the sample is eluted through the column and separated or purified.
When a compound is detected at a concentration above the detection limit, a peak appears in the chromatogram.
Chromatogram peak data provides insights into compound identification, concentration, separation efficiency,
and sample purity.

Each element in the ``results`` array represents peak data for a single detector channel and can be linked
back to the raw chromatogram data stored in the ``datacubes`` array. The peak characteristics found in each
detector channel's ``results[*].peaks`` array are often analyzed alongside the methods, modules, and systems
used to elute the sample through the column.

The ``detector_channels`` array contains information about the settings in a detector channel for a
single injection/chromatography run. The ``mobile_phases`` and ``gradient_steps`` arrays contain information
about how the sample was separated. Additionally, the ``columns`` array, when analyzed alongside ``peaks``,
can help identify maintenance needs for specific instruments or instrument modules.

All of these entities are related via :external+ts-ids-core:py:data:`UUID primary key <ts_ids_core.annotations.UUIDPrimaryKey>`
field, named ``pk``, along with their respective foreign keys.

This level of granularity allows data from multiple chromatography systems and runs
to be stored in a consistent format, simplifying downstream data access and integration.

Below is an example of defining a schema that inherits from
:py:class:`ChromatographySchema` and populating it in Python.
In this example, the data is manually populated within the script, but in typical usage,
it would be parsed from a raw data file.

.. raw:: html

    <details>
      <summary>Click to expand</summary>
      <pre><code>

.. literalinclude:: ../../../__tests__/unit/test_liquid_chromatography.py
    :pyobject: test_complete_lc_chromatography_schema
    :language: python
    :dedent: 4
    :start-after: doc-start
    :end-before: doc-end

.. raw:: html

      </code></pre>
    </details>

The data can then be exported to JSON by calling ``instance.model_dump_json(indent=2)``
The resulting IDS JSON looks like this:

.. raw:: html

    <details>
      <summary>Click to expand</summary>
      <pre><code>

.. literalinclude:: ../../../__tests__/unit/snapshots/chromatography_lc_demo
    :language: json

.. raw:: html

      </code></pre>
    </details>
"""

from typing import List

from ts_ids_core.annotations import (
    Nullable,
    NullableNumber,
    NullableString,
    Required,
    UUIDForeignKey,
    UUIDPrimaryKey,
    fixed_length,
)
from ts_ids_core.base.ids_element import IdsElement
from ts_ids_core.schema import DataCube as _DataCube
from ts_ids_core.schema import DataCubeMetadata
from ts_ids_core.schema import Dimension as _Dimension
from ts_ids_core.schema import Measure as _Measure
from ts_ids_core.schema import TetraDataSchema
from typing_extensions import Annotated

from ts_ids_components.chromatography.method import (
    DetectorChannel,
    GradientStep,
    Method,
    MobilePhase,
    MobilePhaseGradientStep,
    ProcessingBase,
)
from ts_ids_components.chromatography.peak import Peak
from ts_ids_components.chromatography.system import Column, Module, System


class Result(IdsElement):
    name: NullableString
    peaks: List[Peak]


class Dimension(_Dimension):
    name: Required[NullableString]
    unit: Required[NullableString]


class Measure(_Measure):
    name: Required[NullableString]
    unit: Required[NullableString]
    value: Required[List[List[NullableNumber]]]


class DataCube(_DataCube):
    name: Required[NullableString]
    measures: Required[Annotated[List[Measure], fixed_length(1)]]
    dimensions: Required[Annotated[List[Dimension], fixed_length(2)]]


class ChromatographySchema(TetraDataSchema):
    """A schema for chromatography methods and peaks data"""

    systems: Required[List[System]]
    modules: List[Module]
    columns: List[Column]
    methods: Required[List[Method]]
    processing_methods: List[ProcessingBase]
    mobile_phases: List[MobilePhase]
    mobile_phase_gradient_steps: List[MobilePhaseGradientStep]
    gradient_steps: List[GradientStep]
    results: Required[List[Result]]
    detector_channels: List[DetectorChannel]
    datacubes: List[DataCube]
