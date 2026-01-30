"""
This module contains components for spectrophotometry IDSs.

Spectrophotometry for life science
=============================================================

Spectrophotometers measure how much visible or UV light a sample absorbs.
Since different molecules absorb light at specific wavelengths, their absorption spectra can be used to calculate solute concentrations using Beer-Lambert’s Law.

In life sciences, spectrophotometry is commonly used to quantify DNA, RNA, proteins and potential contaminants.
To assess DNA or RNA purity, absorption is measured at 230 nm, 260 nm and 280 nm.
Both RNA and DNA absorb at 260 and 280 nm (to characteristic extents) while common contaminants, such as phenol or guanidine, absorb at 230 nm.
The 260/280 and 260/230 absorbance ratios are quick assessments of sample purity, for example:

* A 260/280 ratio of 1.8 is considered "pure" for DNA and 2.0 for RNA.
* A 260/230 ratio above 2.0 is considered free of contaminant.

Results components
==================

The :py:class:`SpectrophotometerResult` component holds results for a single DNA or RNA spectrophotometer assay, including:

* Absorbance at 260 nm and 280 nm
* Absorbance ratios at 260/280 and 260/230
* Calculated concentration of the target molecule

Instruments often calculate concentration of a target simply through the proportionality of absorbance and concentration described by Beer-Lambert’s Law and ignoring the absorption contributions of other molecules.
Advanced models detect contaminants more precisely and provide a corrected concentration.
In this case we recommend adding a field called `corrected_concentration` to hold this value
"""

from ts_ids_core.base.ids_element import IdsElement
from ts_ids_core.base.ids_field import IdsField
from ts_ids_core.schema import RawValueUnit


class SpectrophotometerResult(IdsElement):
    """
    Common spectrophotometer result fields for molecular biology
    """

    absorbance_ratio_260_230: RawValueUnit = IdsField(
        alias="260_230_absorbance_ratio", description="Absorbance ratio at 260/230 nm"
    )
    absorbance_ratio_260_280: RawValueUnit = IdsField(
        alias="260_280_absorbance_ratio", description="Absorbance ratio at 260/280 nm"
    )
    absorbance_260: RawValueUnit = IdsField(
        alias="260_absorbance", description="Absorbance at 260 nm"
    )
    absorbance_280: RawValueUnit = IdsField(
        alias="280_absorbance", description="Absorbance at 280 nm"
    )
    concentration: RawValueUnit = IdsField(
        description="Concentration of the target molecule in the sample. Typically calculated according to Beer-Lambert's Law."
    )
