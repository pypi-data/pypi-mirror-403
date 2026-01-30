from enum import Enum
from typing import List

from ts_ids_core.annotations import Nullable, UUIDForeignKey, UUIDPrimaryKey
from ts_ids_core.base.ids_element import IdsElement
from ts_ids_core.base.ids_field import IdsField
from ts_ids_core.schema import RawValueUnit


class TimeWithRaw(IdsElement):
    value: Nullable[str]
    raw_value: Nullable[str]


class MethodEvent(IdsElement):
    """Parameters describing when an event took place and who performed it."""

    computer: Nullable[str] = IdsField(description="Identifier of the computer.")
    comment: Nullable[str] = IdsField(
        description="Comments provided by user associated with the event."
    )
    time: TimeWithRaw = IdsField(description="Time that the event took place.")
    user: Nullable[str] = IdsField(description="User associated with the event.")


class Wash(IdsElement):
    """
    Parameters describing a wash step, e.g. of a loop or needle/syringe used for
    injection.
    """

    repeat_count: Nullable[int] = IdsField(
        description="Number of times this step of the wash is repeated."
    )
    timing: Nullable[str] = IdsField(
        description=(
            "Timing of this wash step in relation to the injection, e.g. before the "
            "injection, after the injection, or both."
        )
    )
    solvent: Nullable[str] = IdsField(description="Solvent used for this wash step.")
    volume: RawValueUnit = IdsField(
        description="Volume of solvent used for this wash step."
    )


class Injection(IdsElement):
    """Parameters about the sample injection."""

    mode: Nullable[str] = IdsField(
        description="The injection mode, e.g. full loop or partial loop."
    )
    time: TimeWithRaw = IdsField(description="The time that the injection takes place.")
    volume: RawValueUnit = IdsField(description="Volume of sample to inject.")
    sample_temperature: RawValueUnit = IdsField(
        description="Temperature set point of the sample or sample tray."
    )


class SampleIntroduction(IdsElement):
    """
    The sample introduction includes the sample and its associated quantities (volume,
    concentration, etc.) as well as the preparation steps (e.g. dilution), and
    autosampler methods.
    """

    washes: List[Wash]
    dilution_factor: RawValueUnit = IdsField(
        description="The dilution factor of the sample introduction."
    )
    injection: Injection
    draw_speed: RawValueUnit = IdsField(
        description="The rate at which a sample is drawn."
    )
    dispense_speed: RawValueUnit = IdsField(
        description="The rate at which a sample is dispensed."
    )


class GasInlet(IdsElement):
    """
    Gas chromatography inlet method parameters.
    """

    fk_module: UUIDForeignKey = IdsField(
        primary_key="/properties/modules/items/properties/pk"
    )
    temperature: RawValueUnit = IdsField(description="Temperature of the inlet.")
    operating_mode: Nullable[str] = IdsField(
        description="Operating mode, e.g. split or splitless."
    )
    split_flow: RawValueUnit = IdsField(
        description="Flow rate for split mode injections."
    )
    split_flow_ratio: RawValueUnit = IdsField(
        description=(
            "Ratio of total flow of gas entering the inlet to column flow in split "
            "mode injections."
        )
    )
    purge_flow: RawValueUnit = IdsField(description="Rate of the purge flow.")
    vacuum_compensation: Nullable[bool] = IdsField(
        description=(
            "Whether vacuum correction is on at the start of the run, at 0 seconds "
            "retention time."
        )
    )


# --


class Heater(IdsElement):
    """
    Heater parameters.
    """

    location: Nullable[str] = IdsField(
        description=(
            "Description of the location of the heater in the column compartment, e.g. "
            "left or right."
        )
    )
    temperature: RawValueUnit = IdsField(
        description="Temperature set point of the heater."
    )


class Column(IdsElement):
    """
    Column identifiers for this method.
    """

    fk_column: UUIDForeignKey = IdsField(
        primary_key="/properties/columns/items/properties/pk"
    )
    name: Nullable[str] = IdsField(description="Name of the column.")


class Compartment(IdsElement):
    """
    Configuration of the column compartment.
    """

    fk_module: UUIDForeignKey = IdsField(
        primary_key="/properties/modules/items/properties/pk"
    )
    heaters: List[Heater] = IdsField(description="Heater parameters.")
    column: Column = IdsField(description="Column identifiers for this method.")


# --


class DetectionMethod(IdsElement):
    """Metadata about a detection method."""

    fk_module: UUIDForeignKey = IdsField(
        primary_key="/properties/modules/items/properties/pk"
    )
    name: Nullable[str] = IdsField(description="Name of the detector.")
    description: Nullable[str] = IdsField(
        description="Description of the detector channel."
    )
    data_collection_rate: RawValueUnit = IdsField(
        description="Frequency at which data is collected by the detector."
    )
    gain: RawValueUnit = IdsField(
        description="Parameters to adjust the sensitivity of the detector."
    )


class Electrode(IdsElement):
    """Electrical parameters of an electrode."""

    voltage: RawValueUnit = IdsField(description="Electrode voltage.")
    current: RawValueUnit = IdsField(description="Current through the electrode.")


class MassRange(IdsElement):
    """Range of mass/charge ratios for mass spectra."""

    minimum: RawValueUnit = IdsField(
        description="Minimum value in a range of mass/charge ratios."
    )
    maximum: RawValueUnit = IdsField(
        description="Maximum value in a range of mass/charge ratios."
    )


class SelectedIon(IdsElement):
    mass_charge_ratio: RawValueUnit = IdsField(
        description="The mass to charge ratio associated with a selected ion."
    )


class MassSpecSource(IdsElement):
    type_: Nullable[str] = IdsField(
        alias="type", description="Type of ionization source."
    )
    positive: Electrode = IdsField(
        description="Electrical parameters for the positive electrode."
    )
    negative: Electrode = IdsField(
        description="Electrical parameters for the negative electrode."
    )


class MassSpectrometerSettings(IdsElement):
    """
    Mass spectrometer settings for single spectra instruments, e.g. single
    quadrupole or TOF.
    """

    polarity: Nullable[str] = IdsField(description="Polarity of generated ions.")
    source: MassSpecSource = IdsField(
        description=(
            "Ionization source parameters, including source voltage and current."
        ),
    )
    mass_range: MassRange = IdsField(
        description="Lower and upper cutoffs for m/z values detected."
    )
    selected_ions: List[SelectedIon] = IdsField(
        description="List of specific selected ions for detection."
    )
    full_scan_duration: RawValueUnit = IdsField(
        description="Duration of time of the full mass scan."
    )


# ---


class WavelengthRange(IdsElement):
    minimum: RawValueUnit = IdsField(
        description="Minimum wavelength in the spectral range."
    )
    maximum: RawValueUnit = IdsField(
        description="Maximum wavelength in the spectral range."
    )
    step: RawValueUnit = IdsField(
        description="Spacing between wavelengths in the spectrum."
    )


class UvVisSettings(IdsElement):
    wavelength: RawValueUnit = IdsField(
        description="Wavelength at which absorbance is recorded."
    )
    bandwidth: RawValueUnit = IdsField(
        description=("Spectral bandwidth of the UV-vis channel."),
    )
    reference_used: Nullable[bool] = IdsField(
        description="Whether a reference wavelength is used."
    )
    reference_wavelength: RawValueUnit = IdsField(
        description=("Wavelength at which the reference absorbance is recorded."),
    )
    reference_bandwidth: RawValueUnit = IdsField(
        description=("Spectral bandwidth of the reference UV-vis channel."),
    )
    wavelength_range: WavelengthRange = IdsField(
        description="Wavelength range parameters for a spectral scan."
    )


# ---


class WavelengthSelection(IdsElement):
    """Parameters for wavelength selection."""

    wavelength: RawValueUnit = IdsField(description="Nominal wavelength of detection.")
    bandwidth: RawValueUnit = IdsField(description="Spectral bandwidth of detection.")
    filter_wheel: Nullable[str] = IdsField(
        description="Metadata related to a filter wheel."
    )


class FluorescenceScan(IdsElement):
    mode: str = IdsField(
        description="Mode of the fluorescence scan, e.g. an emission or excitation scan."
    )
    excitation_wavelength: WavelengthRange = IdsField(
        description="Wavelength range of an excitation spectral scan."
    )
    emission_wavelength: WavelengthRange = IdsField(
        description="Wavelength range of an emission spectral scan."
    )


class FluorescenceSettings(IdsElement):
    """Settings for fluorescence detection."""

    excitation: WavelengthSelection = IdsField(
        description="Wavelength and bandwidth of the excitation light."
    )
    emission: WavelengthSelection = IdsField(
        description="Wavelength and bandwidth of the emission detection."
    )
    scan: FluorescenceScan = IdsField(
        description=(
            "Spectral scan detection parameters for emission scan, excitation scan, or "
            "both."
        )
    )


# ---


class ChargedAerosolSettings(IdsElement):
    """Charged aerosol detection settings."""

    corona_needle_voltage: RawValueUnit = IdsField(
        description=(
            "Voltage applied between the needle and the chamber wall to ionize the "
            "charger gas stream. Also called the charger voltage."
        ),
    )
    corona_needle_current: RawValueUnit = IdsField(
        description=(
            "Current supplied to ionize the charger gas stream. Also called the "
            "charger current."
        ),
    )
    evaporator_temperature: RawValueUnit = IdsField(
        description="Temperature of the Charged Aerosol Detector evaporator."
    )


# --


class EluentIon(IdsElement):
    name: Nullable[str] = IdsField(
        description="Name of the ion being eluted by the suppressor."
    )
    concentration: RawValueUnit = IdsField(description="Eluent ion concentration.")


class Suppressor(IdsElement):
    name: Nullable[str] = IdsField(description="Name of the ion suppressor.")
    type_: Nullable[str] = IdsField(alias="type", description="Ion suppressor type.")
    eluent_ions: List[EluentIon] = IdsField(
        description="Ions being eluted by the suppressor."
    )
    current: RawValueUnit = IdsField(description="Current in the suppressor.")
    flow_rate: RawValueUnit = IdsField(description="Flow rate through the suppressor.")


class ConductivitySettings(IdsElement):
    """Conductivity detector settings."""

    suppressor: Suppressor = IdsField(description="Ion exchange suppressor parameters.")


class FlowControlQuantity(RawValueUnit):
    control: Nullable[bool] = IdsField(description="Whether the flow is on.")


class FlameIonizationSettings(IdsElement):
    """Flame ionization detector parameters."""

    detector_temperature: RawValueUnit = IdsField(
        description="Flame ionization detector temperature."
    )
    air_flow: FlowControlQuantity = IdsField(
        description="Flow of air into the flame ionization detector."
    )
    makeup_gas_flow: FlowControlQuantity = IdsField(
        description="Flow of makeup gas into the flame ionization detector."
    )
    hydrogen_gas_flow: FlowControlQuantity = IdsField(
        description="Flow of hydrogen into the flame ionization detector."
    )


class AnalogDigitalConverterSettings(IdsElement):
    """Analog to digital converter settings."""

    input_multiplier: Nullable[float] = IdsField(
        description="Multiplier for the input voltage."
    )
    input_offset: Nullable[float] = IdsField(
        description="Offset for the input voltage."
    )


class DetectorType(str, Enum):
    UV_VIS = "UV-vis"
    MASS_SPECTROMETER = "Mass spectrometer"
    FLUORESCENCE = "Fluorescence"
    CHARGED_AEROSOL = "Charged Aerosol"
    CONDUCTIVITY = "Conductivity"
    FLAME_IONIZATION = "Flame ionization"
    ANALOG_DIGITAL_CONVERTERS = "Analog digital converters"
    OTHER = "Other"


class DetectorChannel(DetectionMethod):
    """Detection method parameters."""

    fk_method: UUIDForeignKey = IdsField(
        primary_key="/properties/methods/items/properties/pk"
    )
    detector_type: str = IdsField(
        description="The type of detector. Possible values are: UV-vis, Mass spectrometer, Fluorescence, Charged Aerosol, conductivity, Flame ionization, Analog digital converters, and other.",
        json_schema_extra={
            "example_values": [detector_type.value for detector_type in DetectorType]
        },
    )
    uv_vis: UvVisSettings
    mass_spectrometer: MassSpectrometerSettings
    fluorescence: FluorescenceSettings
    charged_aerosol: ChargedAerosolSettings
    conductivity: ConductivitySettings
    flame_ionization: FlameIonizationSettings
    analog_digital_converters: AnalogDigitalConverterSettings


# --


class Solvent(IdsElement):
    """
    Solvent metadata in liquid chromatography or ion exchange chromatography
    """

    name: Nullable[str] = IdsField(description="Name of the solvent.")
    description: Nullable[str] = IdsField(description="Description of the solvent.")
    used: Nullable[bool] = IdsField(
        description="Whether or not this solvent is used in this method."
    )


class MobilePhase(IdsElement):
    """
    Mobile phase metadata in liquid chromatography or ion exchange chromatography
    """

    pk: UUIDPrimaryKey = IdsField(
        description="Primary key for mobile phases in the chromatography system."
    )
    fk_method: UUIDForeignKey = IdsField(
        primary_key="/properties/methods/items/properties/pk"
    )
    solvent_a: Solvent
    solvent_b: Solvent
    solvent_c: Solvent
    solvent_d: Solvent
    id_: Nullable[str] = IdsField(alias="id", description="ID of the mobile phase.")
    name: Nullable[str] = IdsField(description="Name assigned to the mobile phase.")
    used: Nullable[bool] = IdsField(
        description="Whether or not this mobile phase is used in this method."
    )


class StartEndAttribute(IdsElement):
    start: RawValueUnit = IdsField(description="Start value.")
    end: RawValueUnit = IdsField(description="End value.")


class MobilePhaseGradientStep(IdsElement):
    """
    Parameters of a mobile phase gradient step.
    Composition is given in terms of mobile phases labelled A, B, C and D.
    For example, A and B may be used with a binary pump, and all four may be used with a
    quaternary pump.
    """

    fk_mobile_phase: UUIDForeignKey = IdsField(
        primary_key="/properties/mobile_phases/items/properties/pk"
    )
    percent_a: RawValueUnit = IdsField(description="Percent of A used.")
    percent_b: RawValueUnit = IdsField(description="Percent of B used.")
    percent_c: RawValueUnit = IdsField(description="Percent of C used.")
    percent_d: RawValueUnit = IdsField(description="Percent of D used.")
    percent_a_start: RawValueUnit = IdsField(
        description="Percent of A at start of gradient step."
    )
    percent_b_start: RawValueUnit = IdsField(
        description="Percent of B at start of gradient step."
    )
    percent_c_start: RawValueUnit = IdsField(
        description="Percent of C at start of gradient step."
    )
    percent_d_start: RawValueUnit = IdsField(
        description="Percent of D at start of gradient step."
    )
    percent_a_end: RawValueUnit = IdsField(
        description="Percent of A at end of gradient step."
    )
    percent_b_end: RawValueUnit = IdsField(
        description="Percent of B at end of gradient step."
    )
    percent_c_end: RawValueUnit = IdsField(
        description="Percent of C at end of gradient step."
    )
    percent_d_end: RawValueUnit = IdsField(
        description="Percent of D at end of gradient step."
    )
    flow: RawValueUnit = IdsField(description="Flow rate for this gradient step.")
    curve: Nullable[str] = IdsField(
        description="A curve identifier for the curve defining this gradient step."
    )
    duration: RawValueUnit = IdsField(
        description="Duration of time of this gradient step."
    )
    retention_time: RawValueUnit = IdsField(
        description="The retention time at which this gradient step starts."
    )


class ProcessingBase(IdsElement):
    """Basic parameters describing a processing method."""

    fk_method: UUIDForeignKey = IdsField(
        primary_key="/properties/methods/items/properties/pk"
    )
    name: Nullable[str] = IdsField(description="Name of the processing method.")
    algorithm: Nullable[str] = IdsField(
        description="Identifier or name of the processing algorithm."
    )
    creation: MethodEvent = IdsField(
        description="Information about the creation of this processing method."
    )
    last_update: MethodEvent = IdsField(
        description="Information about the last update of this processing method."
    )


class GradientStepType(str, Enum):
    TEMPERATURE = "Temperature"
    FLOW = "Flow"
    PRESSURE = "Pressure"


class GradientStep(IdsElement):
    """
    Parameters describing a gradient control step such as temperature, flow or pressure
    gradients.
    """

    fk_method: UUIDForeignKey = IdsField(
        primary_key="/properties/methods/items/properties/pk"
    )
    gradient_type: str = IdsField(
        description="The type of gradient step. Possible values are: Temperature, Flow, and Pressure.",
        json_schema_extra={
            "example_values": [
                gradient_type.value for gradient_type in GradientStepType
            ]
        },
    )
    retention_time: RawValueUnit = IdsField(
        description="The retention time at which this gradient step starts."
    )
    rate: RawValueUnit = IdsField(description="Rate of the gradient step.")
    start_value: RawValueUnit = IdsField(description="Start value of the parameter.")
    target_value: RawValueUnit = IdsField(description="Target value of the parameter.")
    hold_duration: RawValueUnit = IdsField(
        description=(
            "Duration of time that this parameter is held for after reaching the "
            "target."
        )
    )


class Method(IdsElement):
    pk: UUIDPrimaryKey = IdsField(description="Primary key for the method.")
    name: Nullable[str] = IdsField(description="Name of the method.")
    creation: MethodEvent = IdsField(
        description="Information about the creation of this acquisition method."
    )
    last_update: MethodEvent = IdsField(
        description="Information about the last update of this acquisition method."
    )
    sample_introduction: SampleIntroduction
    run_duration: RawValueUnit = IdsField(
        description="Duration of time the method will run for."
    )
    gc_inlet: GasInlet
    carrier_gas: Nullable[str] = IdsField(
        description="The carrier gas used in GC runs."
    )
    compartment: Compartment = IdsField(
        description=(
            "Metadata and settings relating to the first (and possibly only) active "
            "column compartment."
        )
    )
    second_compartment: Compartment = IdsField(
        description=(
            "Second active column compartment, for example used in 2D liquid "
            "chromatography."
        )
    )
