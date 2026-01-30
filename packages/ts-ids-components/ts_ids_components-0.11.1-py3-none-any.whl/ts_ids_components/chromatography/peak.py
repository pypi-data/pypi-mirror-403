"""
This module contains components to model a single peak for a liquid chromatography result.


"""

from enum import Enum
from typing import List

from ts_ids_core.annotations import (
    Nullable,
    NullableBoolean,
    NullableNumber,
    NullableString,
    Required,
)
from ts_ids_core.base.ids_element import IdsElement
from ts_ids_core.base.ids_field import IdsField
from ts_ids_core.schema import Parameter, RawValueUnit


class RawValueUnitMeter(RawValueUnit):
    unit: str = "Meter"


class ValuePair(IdsElement):
    raw_value: NullableString
    value: NullableNumber


class AreaPercent(RawValueUnit):
    """
    The area of a chromatographic peak expressed as a percent of the
    sum of the areas of all integrated peaks in the chromatogram
    """

    adjusted: RawValueUnit = IdsField(description="Percent adjusted area.")
    capillary_electrophoresis: RawValueUnit = IdsField(
        description="Capillary electrophoresis (CE) area for the peak as a percentage of the total CE areas."
    )


class Area(RawValueUnit):
    """Area values for a peak."""

    percent: AreaPercent
    corrected: RawValueUnit = IdsField(
        description="The area of a peak divided by its migration time."
    )
    capillary_electrophoresis: RawValueUnit = IdsField(
        description="Capillary electrophoresis (CE) area for the peak, which is defined as area / retention time."
    )


class Asymmetry(ValuePair):
    percent_height: NullableNumber = IdsField(
        description="Percent of peak height at which asymmetry was calculated."
    )
    is_squared: bool = IdsField(
        description="Boolean field denoting if the asymmetry value is squared."
    )


class BaselineValues(IdsElement):
    start: ValuePair = IdsField(description="Baseline value at peak start.")
    end: ValuePair = IdsField(description="Baseline value at peak end.")
    max: ValuePair = IdsField(description="Baseline value at peak maximum.")
    unit: ValuePair = IdsField(description="Unit of calculated baseline values.")
    model: NullableString = IdsField(
        description="Type of line/curve used to create the baseline. For example, 'Linear'."
    )
    parameters: List[NullableNumber] = IdsField(
        description="Parameters for the baseline curve."
    )
    slope: RawValueUnit = IdsField(
        description="Slope of baseline. Typically with unit x-axis unit / minute."
    )
    channel_name: NullableString = IdsField(
        description="Channel name used to establish baseline signal."
    )


class StartEndAttributes(IdsElement):
    height: RawValueUnit = IdsField(description="Height of peak at a given location.")
    signal: RawValueUnit = IdsField(
        description="Value of uncorrected peak signal at a given location in the peak."
    )


class PlateCounts(IdsElement):
    ep: ValuePair = IdsField(
        description="Plate count calculated using the European Pharmacopoeia plate count equation."
    )
    jp: ValuePair = IdsField(
        description="Plate count calculated using the Japanese Pharmacopoeia revision 15 or later where the plate count equation's coefficient is 5.54."
    )
    jp_14: ValuePair = IdsField(
        description="Plate count calculated using the Japanese Pharmacopoeia revision 14 or earlier where the plate count equation's coefficient is 5.55."
    )
    usp: ValuePair = IdsField(
        description="Plate count calculated using the United States Pharmacopeia plate count equation."
    )
    five_sigma: ValuePair = IdsField(
        description="Plate count calculated using the 5-sigma plate count equation."
    )
    four_sigma: ValuePair = IdsField(
        description="Plate count calculated using the 4-sigma plate count equation."
    )
    three_sigma: ValuePair = IdsField(
        description="Plate count calculated using the 3-sigma plate count equation."
    )
    two_sigma: ValuePair = IdsField(
        description="Plate count calculated using the 2-sigma plate count equation."
    )
    foley_dorsey: ValuePair = IdsField(
        description="Plate count calculated using the Foley-Dorsey method."
    )
    variance: ValuePair = IdsField(
        description="Plate count calculated using the Variance method."
    )
    unspecified: RawValueUnit = IdsField(
        description="Plate count calculated using an unspecified method."
    )
    per_meter: RawValueUnitMeter = IdsField(
        description="Plate count / column length in meters."
    )


class ProcessingCodeCategory(str, Enum):
    baseline = "baseline"
    baseline_start = "baseline_start"
    baseline_end = "baseline_end"
    unspecified = "unspecified"


class ProcessingCode(IdsElement):
    """A code used to describe the processing of a peak."""

    code: Required[str] = IdsField(
        description="The code value defined by the software."
    )
    category: str = IdsField(
        description="A category to describe what specific component of a peak this code influences.",
        json_schema_extra={
            "example_values": [category.value for category in ProcessingCodeCategory]
        },
    )


class CalibrationCurve(IdsElement):
    """Information pertaining to the peak's calibration curve."""

    id: NullableString = IdsField(
        description="Calibration curve identifier associated with the peak."
    )
    mode: NullableString = IdsField(
        description="Determines which calibration standard injections are used as the basis for the calibration of each injection in a sequence."
    )
    entered_x_value: ValuePair = IdsField(
        description="Amount, concentration, or custom field, depending on the selection in the processing method."
    )
    type_: NullableString = IdsField(
        alias="type",
        description="Describes the mathematical model function (calibration function) that is used to calculate the calibration curve.",
    )
    weight: NullableString = IdsField(
        description="Weighting used when calculating the calibration curve. For example, 1/Amount."
    )
    retention: ValuePair = IdsField(description="Retention time of calibration curve.")
    detection_limit: ValuePair = IdsField(
        description="The minimum amount of an analyte that can be detected by a method with a specified level of certainty, given a particular set of calibration data."
    )
    r: ValuePair = IdsField(
        description="Correlation coefficient. The 'linear dependence' between two variables (for example, the peak area and the amount or concentration of an analyte)"
    )
    r_squared: ValuePair = IdsField(
        description="The coefficient of determination, which reflects the deviation of the measured data points from the calibration curve."
    )
    adjusted_r_squared: ValuePair = IdsField(
        description="The coefficient of determination corrected by the degree of freedom"
    )
    number_of_disabled_calibration_points: Nullable[int] = IdsField(
        description="The number of values that were not considered in the calibration."
    )
    x_unit: NullableString = IdsField(
        description="Unit of the x-axis of the calibration plot."
    )
    y_unit: NullableString = IdsField(
        description="Unit of the y-axis of the calibration plot."
    )
    injection_volume: ValuePair = IdsField(
        description="Injection volume use to generate the calibration curve."
    )
    rf: ValuePair = IdsField(
        description="Calculates the ascending slope of the calibration curve, specified as amount/area value."
    )
    variance: ValuePair = IdsField(
        description="The sum of the average deviation of all area values from the corresponding ideal area value in a calibration."
    )
    variance_coefficient: ValuePair = IdsField(
        description="A type of normalized variance value. The variance coefficient indicates how well the data points correspond to the theoretically assumed course of the curve."
    )
    standard_deviation: ValuePair = IdsField(
        description="Square root of calibration variance."
    )


class Height(RawValueUnit):
    percent: RawValueUnit = IdsField(
        description="Peak height as a percent of the sum of the heights of all integrated peaks in the chromatogram."
    )


class AmountPercent(IdsElement):
    total: RawValueUnit = IdsField(
        description="Peak amount as a percent of the sum of the amounts of all quantitated peaks in the chromatogram."
    )
    deviation: RawValueUnit = IdsField(
        description="The difference between the calculated and control sample amount or concentration values, expressed as a percentage of the control value."
    )


class Amount(RawValueUnit):
    """Quantity of a component in a chromatogram."""

    percent: AmountPercent
    from_extinction_coeff: bool = IdsField(
        description="True if amount value was calculated using the component's extinction coefficient."
    )
    deviation: ValuePair = IdsField(
        description="Difference between the nominal amount of the component and the actual value."
    )


class Response(RawValueUnit):
    """
    The peak area, peak height, or a ratio, depending on the Y Value flag and use of an internal standard.
    Together with amount and concentration, response is the value used to produce a point in the
    calibration curve and used during quantitation to obtain the amount of concentration of the
    unknown peak from the calibration curve.
    """

    relative: ValuePair = IdsField(
        description="A parameter that scales the response of a specified component to the response of a component named as a Curve reference."
    )
    factor: ValuePair = IdsField(
        description="Ratio off response to analyte concentration. This value is dependent on the response type chosen."
    )


class RelativeRetentionTime(RawValueUnit):
    """Difference between the retention time of a component and the retention time of its RT Reference peak"""

    value: Required[Nullable[float]] = IdsField(
        description="Relative retention time value calculated using an unspecified pharmacop(o)eia standard."
    )
    usp: RawValueUnit = IdsField(
        description="Relative retention time calculated using the USP standard."
    )
    ep: RawValueUnit = IdsField(
        description="Relative retention time calculated using the EP standard."
    )
    jp: RawValueUnit = IdsField(
        description="Relative retention time calculated using the JP standard."
    )


class RetentionTime(RawValueUnit):
    """
    The time that elapses between the injection of a sample and the appearance of
    the peak maximum (apex) of a component in the sample.
    """

    relative: RelativeRetentionTime
    ratio: ValuePair = IdsField(
        description="The retention time of a component divided by the retention time of its reference peak (RT Reference)."
    )
    centroid: RawValueUnit = IdsField(
        description="The centroid time of the peak (i.e. the peak's center of mass)."
    )
    corrected: RawValueUnit = IdsField(
        description="Corrected retention time based off a standard peak's deviation from its expected retention time."
    )


class Retention(IdsElement):
    time: RetentionTime
    signal: RawValueUnit = IdsField(
        description="Uncorrected peak signal value at retention time."
    )
    deviation: RawValueUnit = IdsField(
        description="The deviation of the actual retention time from the expected retention time."
    )
    index: ValuePair = IdsField(
        description="Interpolated retention index calculated based on designated marker peaks, if specified."
    )
    window_width: RawValueUnit = IdsField(
        description="The tolerance interval in which the peak is expected"
    )
    selectivity: ValuePair = IdsField(
        description="A USP standard that is a ratio of two peak's capacity factors. Where the peak represented in the numerator must have a retention time greater than the retention time of the peak representated in the denominator (i.e. selectivity cannot be less than 1)."
    )


class USPResolution(IdsElement):
    """Resolution values calculated following United States Pharmacopeia standards."""

    tangent: RawValueUnit = IdsField(
        description="Resolution calculated using USP tangent method."
    )
    half_height: RawValueUnit = IdsField(
        description="Resolution calculated using USP half-height method."
    )
    five_sigma: RawValueUnit = IdsField(
        description="Resolution calculated using USP 5-sigma method."
    )
    half_width: RawValueUnit = IdsField(
        description="Resolution calculated using USP half-width method."
    )
    statistical: RawValueUnit = IdsField(
        description="Resolution calculated using USP statistical method."
    )


class Resolution(RawValueUnit):
    """The extent to which a chromatographic column separates components from each other"""

    value: NullableNumber = IdsField(
        description="Resolution calculated using an unspecified resolution formula."
    )
    usp: USPResolution = IdsField(
        description="Resolution calculated using the USP standard."
    )
    ep_jp: RawValueUnit = IdsField(
        description="Resolution calculated using the EP/JP pharmacopeia standard. This standard is the same for EP and JP."
    )


class SignalToNoise(ValuePair):
    usp: ValuePair = IdsField(
        description="Signal-to-noise calculated using the USP standard"
    )


class Pharmacopeia(str, Enum):
    """Enumeration of Pharmacop(o)eia standard names."""

    usp = "United States Pharmacopeia"
    ep = "European Pharmacopoeia"
    jp = "Japanese Pharmacopoeia"


class WidthType(str, Enum):
    left = "Left"
    right = "Right"
    full = "Full"


class WidthSpan(str, Enum):
    tangent = "Tangent"
    signal = "Signal"


class WidthLocation(str, Enum):
    percent = "Percent Height"
    baseline = "Baseline"


class Width(RawValueUnit):
    """A width measurement of a peak."""

    percent_height: NullableNumber = IdsField(
        description="Percent height of peak at which width value was calculated."
    )
    span: str = IdsField(
        description="The span of the width. 'Tangent' if the width is measured from peak tangent lines. 'Signal' if the width is measured from the peak's signal values.",
        json_schema_extra={"example_values": [span.value for span in WidthSpan]},
    )
    location: str = IdsField(
        description="The width location along the peak's y-axis. 'Percent Height' if the width is measured at a percent height of the peak. 'Baseline' if the width is measured at the baseline of the peak.",
        json_schema_extra={
            "example_values": [location.value for location in WidthLocation]
        },
    )
    pharmacopeia: str = IdsField(
        description="Designates which standard the width value conforms to. This flags the width with which standard's formulas may use this width value.",
        json_schema_extra={"example_values": [pharma.value for pharma in Pharmacopeia]},
    )
    type_: str = IdsField(
        alias="type",
        description="Describes width distance relative to retention time. Where 'left' marks the width as the distance between peak start and retention time, 'right' as the distance between retention time and peak end, and 'full' when the width crosses the retention time and spans the entire peak.",
        json_schema_extra={"example_values": [type.value for type in WidthType]},
    )


class Channel(IdsElement):
    group: NullableString = IdsField(
        description="Name of group that monitor signal belongs to; for example, Chrom.1."
    )
    name: NullableString = IdsField(
        description="Name of signal being detected by a specific monitor associated with a given peak; for example, UV 1_280"
    )


class Conductivity(IdsElement):
    average: RawValueUnit = IdsField(
        description="Average electrical conduction associated with a given peak."
    )
    end: RawValueUnit = IdsField(
        description="Conductivity of eluent at time of peak end."
    )
    max: RawValueUnit = IdsField(
        description="Conductivity of eluent at time of max peak height."
    )
    start: RawValueUnit = IdsField(
        description="Conductivity of eluent at time of peak start."
    )


class Concentration(RawValueUnit):
    """Concentration of sample."""

    from_extinction_coeff: bool = IdsField(
        description="True if concentration was calculated using the component's extinction coefficient."
    )


class FractionTube(IdsElement):
    """Fraction tubes used during peak elution."""

    end: RawValueUnit = IdsField(
        description="Tube label or position collecting eluent at time of peak end."
    )
    start: RawValueUnit = IdsField(
        description="Tube label or position collecting eluent at time of peak start."
    )
    max: RawValueUnit = IdsField(
        description="Tube label or position collecting eluent at time of max peak height."
    )


class StandardDeviation(RawValueUnit):
    """Standard deviation for a Gaussian-shaped peak."""

    relative: ValuePair = IdsField(
        description="The standard deviation as a percentage of the mean of the measured values. A normalized standard deviation that can be used to measure relative error in the calibration."
    )


class Statistic(IdsElement):
    standard_deviation: StandardDeviation
    moment_0: NullableNumber = IdsField(
        description="The zeroth moment; the uncorrected area (area under peak not including baseline correction)."
    )
    moment_1: NullableNumber = IdsField(
        description="The first central moment (peak mean). This value differs from the retention time when the third moment is nonzero."
    )
    moment_2: NullableNumber = IdsField(
        description="The second central moment, which corresponds to variance."
    )
    moment_3: NullableNumber = IdsField(
        description="The Third cumulant/central moment."
    )
    moment_4: NullableNumber = IdsField(description="The fourth central moment.")
    unspecified_moment: ValuePair = IdsField(
        description="This value can be any of the 0th-4th statistical moments. This will be populated when the primary data does not specify which moment value is captured."
    )
    skewness: ValuePair = IdsField(
        description="The third moment divided by the standard deviation cubed."
    )
    kurtosis: ValuePair = IdsField(
        description="The peak's fourth moment divided by the peak's standard deviation raised to the 4th power. Often referred to as the 'tailedness' of the peak."
    )
    excess_kurtosis: ValuePair = IdsField(
        description="Excess kurtosis = kurtosis - 3. It describes the peak's kurtosis relative to a normal distribution whose kurtosis is always 3."
    )
    symmetry: NullableNumber = IdsField(
        description="A pseudomoment measure of symmetry determined by tangents to the peak at points of inflection in the curve."
    )


class PeakValleyRatio(IdsElement):
    """Peak value ratio(s) for a peak."""

    start: ValuePair = IdsField(
        description="Ratio of peak height to valley height at start of peak."
    )
    end: ValuePair = IdsField(
        description="Ratio of peak height to valley height at end of peak."
    )
    max: ValuePair = IdsField(
        description="Peak valley ratio using the smallest valley adjacent to the peak."
    )


class PeakGroup(IdsElement):
    """Aggregate information pertaining to a group of peaks."""

    name: NullableString = IdsField(description="Name of the peak group.")
    amount: ValuePair = IdsField(description="Sum peak amounts within a group.")
    area: RawValueUnit = IdsField(description="Sum peak areas within a group.")
    height: RawValueUnit = IdsField(description="Sum peak heights within a group.")


class Tolerance(IdsElement):
    high: ValuePair = IdsField(description="High value for tolerance level.")
    low: ValuePair = IdsField(description="Low value for tolerance level.")


class LevelTolerance(IdsElement):
    amount: Tolerance = IdsField(description="Amount tolerance for a given level.")
    response: Tolerance = IdsField(description="Response tolerance for a given level.")


class Level(IdsElement):
    value: NullableString = IdsField(
        description="Level designation used for a standard during sample loading."
    )
    check: NullableString = IdsField(
        description="Pass/fail result of a calibration level for a check standard/QC sample injection"
    )
    tolerance: LevelTolerance


class Peak(IdsElement):
    amount: Amount
    analyte: str
    area: Area = IdsField(
        description="The peak signal integrated over time between peak start and peak end points."
    )
    assigned: NullableBoolean = IdsField(
        description="True if the peak has been manually assigned by the user; false otherwise."
    )
    asymmetry: List[Asymmetry] = IdsField(
        description="All asymmetry values calculated for a given peak."
    )
    baseline: BaselineValues
    calibration_curve: CalibrationCurve
    capacity_factor: ValuePair = IdsField(
        description="Capacity factor aka k prime (k'), a measurement of the retention time of a sample molecule relative to the column void volume (VØ)"
    )
    channel: Channel
    component_type: NullableString
    concentration: Concentration
    conductivity: Conductivity
    control_value: ValuePair
    custom_fields: List[Parameter]
    description: NullableString = IdsField(
        description="User denoted annotation of peak."
    )
    end: StartEndAttributes = IdsField(
        description="Calculated values specific to the end of the peak."
    )
    extinction_coefficient: NullableNumber = IdsField(
        description="Component's extinction coefficient."
    )
    f_at_5: ValuePair = IdsField(
        description="Peak width from start point at 5% of peak height to retention time. 'f' denoting this width's use in the USP tailing factor equation."
    )
    fraction_tube: FractionTube
    group: PeakGroup
    height: Height = IdsField(
        description="Height of the peak as measured from the peak's apex to baseline."
    )
    impurity_type: NullableString
    integration_type: NullableString
    kav: NullableNumber = IdsField(
        description="The ratio between the elution volume of a given molecule and the total available volume of the column"
    )
    label: NullableString = IdsField(description="Label given to peak.")
    level: Level
    manipulated: NullableBoolean = IdsField(
        description="true if the peak has been manipulated by the user; false otherwise"
    )
    name: NullableString = IdsField(description="A name given to the peak.")
    number: NullableNumber = IdsField(
        description="Number assigned to the peak in the chromatogram."
    )
    offset: ValuePair
    plate_count: PlateCounts
    points_across_peak: ValuePair = IdsField(
        description="Width of peak expressed as the number of data points on x-axis"
    )
    processing_codes: List[ProcessingCode]
    peak_valley_ratio: PeakValleyRatio
    resolution: Resolution
    response: Response
    retention: Retention
    signal_to_noise: SignalToNoise
    start: StartEndAttributes = IdsField(
        description="Calculated values specific to the start of the peak."
    )
    statistic: Statistic
    symmetry_factor: ValuePair = IdsField(
        description="The maximum permissible asymmetry of the peak. EP and JP standard that is equivalent to USP Tailing Factor."
    )
    type: NullableString = IdsField(description="String descriptor of type of peak.")
    usp_tailing_factor: ValuePair = IdsField(
        description="The maximum permissible asymmetry of the peak. USP Tailing Factor that is equivalent to EP and JP symmetry factor."
    )
    widths: List[Width]
