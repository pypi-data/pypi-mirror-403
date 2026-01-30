"""
This module contains the components for the clonal imager IDS.

Clonal Imaging
=============================================================
Clonal imaging is a technique used to assess the quality of cell cultures, select wells suitable for clonal expansion, and monitor
the growth and morphology of clones. The monoclonality field provides a direct assessment of whether a well is suitable for further
development, while the other measurements offer insights into cell growth patterns and potential issues like cell aggregation.

This information is used for selecting high-producing clones and ensuring the clonality of cell lines during biopharmaceutical
production.

Results components
==================

The :py:class:`ClonalImagerResult` component holds the results of a clonal imaging assay, including:

* Monoclonality: A value indicating whether the well is monoclonal (derived from a single cell).
* Number of aggregates: The number of cell aggregates detected in the well.
* Number of cells: The number of individual cells identified in the well.
* Number of cell-likes: The number of objects in the image that resemble cells but cannot be definitively identified as such.

* Confluence: The percentage of the well surface covered by adherent cells.

"""

from ts_ids_core.base.ids_field import IdsField
from ts_ids_core.schema import IdsElement, RawValueUnit


class ClonalImagerResult(IdsElement):
    """
    Result information for a clonal imager
    """

    monoclonality: RawValueUnit = IdsField(description="The monoclonality of the well.")

    # Measurements used to determine monoclonality
    number_of_aggregates: RawValueUnit = IdsField(
        description="The number of cell aggregates detected in each well."
    )
    number_of_cells: RawValueUnit = IdsField(
        description="The number of individual cells detected in each well."
    )
    number_of_cell_likes: RawValueUnit = IdsField(
        description="The number of objects detected in the image that resemble cells but are not definitively identified as such."
    )

    confluence: RawValueUnit = IdsField(
        description="The measure of confluence (the percentage of the surface covered by adherent cells) of the well."
    )
