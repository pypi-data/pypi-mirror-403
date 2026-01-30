"""
This module contains IDS components designed for use in Crystallization in-silico solvent selection processes.

In-Silico Solvent Selection for Crystallization
=============================================================

Solvent selection is a part of crystallization optimization workflows where a mixture containing an Active Pharmaceutical Ingredient (API) is dissolved in solvent then further processed to separate the crystallized form from impurities.
Characterizing the solubility between API and many solvents, as well as common impurities with solvents, is critical to modeling these processes.
As there are many individual solvents and countless multi-solvent combinations available for testing, in-silico methods are commonly used.

Examples of in-silico computational models are COSMO-RS, r-UNIFAC and the Hansen equations.
Each of these require simple structural knowledge of the solute molecule of interest.
The r-UNIFAC and Hansen models also require some actual experimental solubility measures in order to fit specific interaction parameters within the models.

The data schemas herein should be adopted across solvent schema applications to ensure consistency in naming conventions.

Sample components
==================

Here a sample refers to the solute of interest.
This is typically the Active Pharmaceutical Ingredient (API) to be purified, but it could also refer to an impurity to be removed.
Two components are provided to support sample definitions:

:py:class:`SoluteMolecule` includes fundamental structural characteristics of a solute molecule.
These fields are immutable in the sense that it if they changed at all they would describe a different molecule.
Repeated experiments to describe them would be exactly the same.

:py:class:`SoluteProperties` describes experimental measures of a solute molecule.
While these also describe fundamental properties of a molecule the values are sensitive to experimental conditions or floating point precision.

If creating an IDS structure where all properties are provided as a source of truth then your Sample class could just inherit from both:

.. code-block:: python

    from ts_ids_components.solvent_selection import SoluteMolecule, SoluteProperties

    class Sample(SoluteMolecule, SoluteProperties):
        pass

Otherwise, if these measures are sensitive enough that different values should be evaluated on a separate run then :py:class:`SoluteProperties` fields might be better placed a Run object or other data structure.

Run components
==================

These components describe the setup of an experimental run to support a regression-UNIFAC or Hansen modelling process, which require pre-determined solvent solute solubility measures.
Other models, like COSMO-RS, do not require this.

Here a Run will consist of several solubility measurements.
:py:class:`PreMeasuredSolubility` can be used to describe solvent composition, temperature and solubility.

.. code-block:: python

    from ts_ids_components.solvent_selection import PreMeasuredSolubility

    class Run(PreMeasuredSolubility):
        pass

Two solvent mixture classes are included, :py:class:`TwoSolventMixture` or :py:class:`ThreeSolventMixture`.
If an application requires a more complex solvent description fields can be added as appropriate

Results components
=========================================

Similar to the Run :py:class:`PreMeasuredSolubility` class above the :py:class:`SolubilityPrediction` class describes a solvent temperature and solubility.
A separate class is defined for results here though so that the field names and descriptions can explicitly describe a result.


"""

from ts_ids_core.annotations import (
    NullableBoolean,
    NullableNumber,
    NullableString,
    Optional,
    UUIDPrimaryKey,
)
from ts_ids_core.base.ids_element import IdsElement
from ts_ids_core.base.ids_field import IdsField
from ts_ids_core.schema import RawValueUnit


class SoluteMolecule(IdsElement):
    """The name and structural characteristics of a solute. This may describe an Active Pharmaceutical Ingredient (API) or an impurity."""

    name: NullableString = IdsField(
        description="The name of an API or impurity molecule"
    )
    smiles: NullableString = IdsField(
        description="The 'smiles' chemical string representation of the molecule."
    )
    aromatic_rings_number: NullableNumber = IdsField(
        description="The number of aromatic rings in the molecule."
    )
    non_aromatic_rings_number: NullableNumber = IdsField(
        description="The number of non-aromatic rings in the molecule."
    )


class SoluteProperties(IdsElement):
    """The measured properties of a solute. These are floating point measures that may be sensitive to experimental conditions and precision."""

    melting_point: RawValueUnit = IdsField(
        description="The melting point temperature of the molecule"
    )
    enthalpy_of_fusion: RawValueUnit = IdsField(
        description="The enthalpy of fusion of the molecule"
    )
    solute_density: RawValueUnit = IdsField(description="The density of the solute")


class TwoSolventMixture(IdsElement):
    """Parameters to define the composition of a solvent mixture composed of up to 2 solvents"""

    solvent1: str = IdsField(description="Name of the 1st solvent in mixture.")
    solvent2: NullableString = IdsField(
        description="Name of the 2nd solvent in mixture."
    )
    volume_fraction1: NullableNumber = IdsField(
        description="Volume fraction of the 1st solvent."
    )


class ThreeSolventMixture(TwoSolventMixture):
    """Parameters to define the composition of a solvent mixture composed of up to 3 solvents"""

    solvent3: NullableString = IdsField(
        description="Name of the 3rd solvent in mixture."
    )
    volume_fraction2: NullableNumber = IdsField(
        description="Volume fraction of the 2nd solvent."
    )


class PreMeasuredSolubility(IdsElement):
    """A single solubility measurement"""

    solvent_composition: ThreeSolventMixture = IdsField(
        description="Composition of the solvent mixture used for the solubility measure."
    )
    temperature: RawValueUnit = IdsField(
        description="Temperature at which solubility is measured."
    )
    premeasured_solubility: RawValueUnit = IdsField(
        description="Measured solubility with unit."
    )


class PredictedSolubility(IdsElement):
    """A single solubility prediction"""

    solvent_composition: ThreeSolventMixture = IdsField(
        description="Composition of the solvent mixture used for the solubility prediction."
    )

    temperature: RawValueUnit = IdsField(
        description="Temperature at which solubility is predicted."
    )
    predicted_solubility: RawValueUnit = IdsField(
        description="Predicted solubility in the solvent mixture."
    )
