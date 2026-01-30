"""
This module contains components for quantitative PCR (qPCR) and digital PCR (dPCR) IDSs.

Polymerase Chain Reaction (PCR) and quantitative DNA analysis
=============================================================

Polymerase chain reaction (PCR) takes advantage of
a thermally activated DNA chemistry to repeatedly replicate (or amplify) target DNA sequences for quantitative analysis.
Specificity is achieved by designing primers tailored to a target sequence, combined with a fluorescent mechanism that
produces a signal on a successful reaction thus indicating the presence of the target sequence.

In conventional "real-time" or quantitative PCR (qPCR), targets in a sample are amplified in batch producing a fluorescent
signal proportional to the target amplicons (amplified DNA). The signal is measured in "real-time" at the end of each
amplification cycle and, briefly stated, fit to an exponential model to estimate the initial abundance.
Typically, an experiment is designed to provide a "relative quantification" measure of target abundance, compared to that
of a stable reference gene or reference sample using the delta-cycle-threshold (ΔCt) and delta-delta-cycle-threshold (ΔΔCt)
methods respectively.
Alternatively an "absolute quantification" experiment can be performed by comparing the target signal to a
"standard curve" generated from samples with known concentrations of the target DNA.
Correct quantification here is sensitive to target-specific amplification efficiencies and the quality of the
standard library.

Digital PCR (dPCR), including digital droplet PCR (ddPCR), is a more recent technology able to isolate and amplify
individual DNA molecules in a high-throughput fashion and then count all reactions in a sample for a positive or negative signal indicating presence of a target sequence.
Directly counting discrete reactions in a sample enables a more straight-forward derivation of target abundance.

For both techniques the methods describing PCR chemistry with target and reporter specifications are very similar, though
how results are calculated and reported are unique.

The IDS components presented here were designed to capture methods and results from PCR experiments and should be used to
transform data from disparate instrument vendors/models into a consistent format.
Notably absent is a structure representing the PCR thermocycling parameters, these are often not included in data
exports.
Please contact TetraScience to discuss a use-case requiring an update to this standard.

Methods components
==================

The :py:class:`PcrMethodsTarget` component is built to hold relevant experimental setup information around a molecular target.
In both qPCR and dPCR experiments this typically includes information on the target type (e.g. a Reference or
Unknown) and the reporter & quencher chemistry used to develop a reaction signal. Optionally, a
reference target name and/or reference copy number may be required for some experimental setups (e.g Copy Number Variation
or Relative Quantification).

Quantitative PCR (qPCR) results components
=========================================

The :py:class:`QPcrResultsTarget` component holds results pertaining to a single target within a qPCR experiment.
This includes the cycle_threshold (Ct) and control normalized delta_cycle_threshold (ΔCt) which are typically calculated for
each target. Optional standard_curve parameters can also be set depending on the experiment design.

For relative quantification experiments the delta_delta_cycle_threshold (ΔΔCt) and relative_quantity values are determined.
For an absolute quantification experiment the absolute_quantity can be set as well as a standard_curve for the
reference sample targets.

Digital PCR (dPCR) results components
=====================================

The :py:class:`DPcrResultsTarget` component holds results for an individual target within a dPCR sample.
This includes the fluorescent intensity threshold, from which each reaction is determined to be positive or negative,
the count of all reactions in a sample, the derived concentration of the target and when appropriate the copy number variation.

Building a custom IDS data schema
=================================

Here is an example of defining a dPCR schema from these components and populating it in Python.
This shows data being manually populated in the script itself, but in typical usage,
this data would be parsed from a raw data file.
Note the addition of foreign key fields to the ResultsTarget object linking to the appropriate Sample and MethodsTarget.

.. literalinclude:: ../../../__tests__/unit/test_qpcr.py
    :pyobject: test_complete_dpcr_schema
    :language: python
    :dedent: 4
    :start-after: doc-start
    :end-before: doc-end

Then, the data could be dumped to JSON by calling ``instance.model_dump_json(indent=2)``
The resulting IDS JSON looks like this:

.. literalinclude:: ../../../__tests__/unit/snapshots/qpcr_schema_demo.json
    :language: json

"""

from ts_ids_core.annotations import NullableString, Optional, UUIDPrimaryKey
from ts_ids_core.base.ids_element import IdsElement
from ts_ids_core.base.ids_field import IdsField
from ts_ids_core.schema import RawValueUnit


class PcrMethodsTarget(IdsElement):
    """
    Method information for a PCR Target
    """

    pk: UUIDPrimaryKey = IdsField(description="Primary key of a methods target")
    name: NullableString = IdsField(
        description="Name of the target. Can be descriptive or an index, e.g. '1', 'GAPDH'"
    )
    type: NullableString = IdsField(
        description="Type description of target in experimental context, e.g. 'Reference', 'Unknown'"
    )
    reporter_name: NullableString = IdsField(
        description="Name of the reporter or dye used in the reaction, e.g. 'FAM', 'HEX'"
    )
    quencher_name: NullableString = IdsField(
        description="Name of any quencher used in the reaction, e.g. 'NFQ-MGB', 'QSY'"
    )
    reference_target_name: NullableString = IdsField(
        description="Name of any reference target if applicable, may reference another MethodsTarget.name. Could contain a house-keeping gene or CNV normalization target."
    )
    reference_copies: RawValueUnit = IdsField(
        description="Known copy number of the reference target in a CNV calculation if applicable"
    )


class ReactionMeasure(IdsElement):
    """
    Result count data for a droplet measurement
    """

    count: Optional[int] = IdsField(description="Count of characteristic reaction")
    mean_amplitude: RawValueUnit = IdsField(
        description="Mean amplitude of the reactions"
    )


class DPcrResultsTarget(IdsElement):
    """dPCR Result Target values from raw data"""

    threshold: RawValueUnit = IdsField(
        description="Fluorescent intensity threshold for positive/negative determination"
    )
    concentration: RawValueUnit = IdsField(
        description="Concentration of the target in the sample"
    )
    accepted_reactions: ReactionMeasure = IdsField(
        description="Count of accepted reactions"
    )
    positive_reactions: ReactionMeasure = IdsField(
        description="Count of positive reactions"
    )
    negative_reactions: ReactionMeasure = IdsField(
        description="Count of negative reactions"
    )
    copy_number_variation: RawValueUnit = IdsField(
        description="Copy number variation of the target if applicable"
    )


class RawValueUnitStatistics(RawValueUnit):
    """Value Unit Mean Standard Deviation information."""

    mean: RawValueUnit = IdsField(description="Mean value of the data")
    standard_deviation: RawValueUnit = IdsField(
        description="Standard deviation of the data"
    )


class QPcrStandardCurve(IdsElement):
    """Standard Curve information."""

    y_intercept: RawValueUnit = IdsField(
        description="Y-intercept of the standard curve"
    )
    slope: RawValueUnit = IdsField(description="Slope of the standard curve")
    efficiency: RawValueUnit = IdsField(
        description="Amplification efficiency from the standard curve"
    )
    r_squared: RawValueUnit = IdsField(
        description="R-squared value of the standard curve"
    )


class QPcrResultsTarget(IdsElement):
    """qPCR Result Target values from raw data"""

    cycle_threshold: RawValueUnitStatistics = IdsField(
        description="Cycle threshold (Ct) value for the target"
    )
    delta_cycle_threshold: RawValueUnitStatistics = IdsField(
        description="Control normalized delta cycle threshold (ΔCt) value"
    )
    delta_delta_cycle_threshold: RawValueUnitStatistics = IdsField(
        description="Delta delta cycle threshold (ΔΔCt) value to derive relative quantification"
    )
    standard_curve: QPcrStandardCurve = IdsField(
        description="Standard curve parameters created for this target if applicable"
    )
    relative_quantity: RawValueUnitStatistics = IdsField(
        description="Relative quantity value for relative quantification if applicable "
    )
    absolute_quantity: RawValueUnitStatistics = IdsField(
        description="Absolute quantity value for absolute quantification from a known standard curve value if applicable"
    )
