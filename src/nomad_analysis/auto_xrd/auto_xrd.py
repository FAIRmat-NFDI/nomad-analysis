from typing import (
    TYPE_CHECKING,
)

if TYPE_CHECKING:
    from nomad.datamodel.datamodel import (
        EntryArchive,
    )
    from structlog.stdlib import (
        BoundLogger,
    )

import numpy as np
from ase.io import read
from matid import SymmetryAnalyzer  # pylint: disable=import-error
from nomad.datamodel.data import Schema
from nomad.datamodel.metainfo.annotations import ELNAnnotation, ELNComponentEnum
from nomad.datamodel.results import Material, SymmetryNew, System
from nomad.metainfo import Quantity, SchemaPackage
from nomad.normalizing.common import nomad_atoms_from_ase_atoms
from nomad.normalizing.topology import add_system, add_system_info

m_package = SchemaPackage()


def my_normalization(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
    if self.cif_files is not None:
        # Read the CIF files and convert them into ase atoms
        ase_atoms_list = []
        for cif_file in self.cif_files:
            with archive.m_context.raw_file(cif_file) as file:
                try:
                    ase_atoms_list.append(read(file.name))
                except RuntimeError:
                    logger.warn(f'Cannot parse cif file: {cif_file}')

        # Let's save the composition and structure into archive.results.material
        if not archive.results.material:
            archive.results.material = Material()

        # populate elemets from a set aof all the elemsts in ase_atoms
        elements = set()
        for ase_atoms in ase_atoms_list:
            elements.update(ase_atoms.get_chemical_symbols())
        archive.results.material.elements = list(elements)

        # Create a System: this is a NOMAD specific data structure for storing structural  # noqa: E501
        # and chemical information that is suitable for both experiments and simulations.  # noqa: E501
        topology = {}
        for ase_atoms in ase_atoms_list:
            symmetry = SymmetryNew()
            symmetry_analyzer = SymmetryAnalyzer(ase_atoms, symmetry_tol=1)
            print(symmetry_analyzer.get_space_group_number())
            symmetry.bravais_lattice = symmetry_analyzer.get_bravais_lattice()
            symmetry.space_group_number = symmetry_analyzer.get_space_group_number()
            symmetry.space_group_symbol = (
                symmetry_analyzer.get_space_group_international_short()
            )
            symmetry.crystal_system = symmetry_analyzer.get_crystal_system()
            symmetry.point_group = symmetry_analyzer.get_point_group()
            system = System(
                atoms=nomad_atoms_from_ase_atoms(ase_atoms),
                label=f'{ase_atoms.get_chemical_formula()}-{symmetry.space_group_number}',
                description='Reference structure used to train the auto-XRD model.',
                structural_type='bulk',
                dimensionality='3D',
                symmetry=symmetry,
            )
            add_system_info(system, topology)
            add_system(system, topology)

        archive.results.material.topology = list(topology.values())


class AutoXRDModel(Schema):
    """
    A schema for hosting data from an
    [XRD-AutoAnalyzer](https://github.com/njszym/XRD-AutoAnalyzer) model.
    """

    xrd_model_file = Quantity(
        type=str,
        description='Path to the HDF5 file containing the XRD data.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.FileEditQuantity,
        ),
    )

    wandb_run_url_xrd = Quantity(
        type=str,
        description='URL to the W&B run containing the XRD model.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.URLEditQuantity,
        ),
    )

    pdf_model_file = Quantity(
        type=str,
        description='Path to the HDF5 file containing the XRD data.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.FileEditQuantity,
        ),
    )

    wandb_run_url_pdf = Quantity(
        type=str,
        description='URL to the W&B run containing the PDF model.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.URLEditQuantity,
        ),
    )

    cif_files = Quantity(
        type=str,
        shape=['*'],
        description='List of paths to CIF files containing crystal structures.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.FileEditQuantity,
        ),
    )

    max_texture = Quantity(
        type=np.float64,
        description='Maximum texture value for the simualtions.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
        ),
    )
    min_domain_size = Quantity(
        type=np.float64,
        description='Minimum domain size.',
        unit='nm',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
        ),
    )
    max_domain_size = Quantity(
        type=np.float64,
        description='Maximum domain size.',
        unit='nm',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
        ),
    )
    max_strain = Quantity(
        type=np.float64,
        description='Maximum strain value.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
        ),
    )
    num_patterns = Quantity(
        type=int,
        description='Number of XRD patterns simulated per phase.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
        ),
    )
    min_angle = Quantity(
        type=np.float64,
        description='Minimum angle value.',
        unit='deg',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
        ),
    )
    max_angle = Quantity(
        type=np.float64,
        description='Maximum angle value.',
        unit='deg',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
        ),
    )
    max_shift = Quantity(
        type=np.float64,
        description='Maximum shift value.',
        unit='deg',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
        ),
    )
    separate = Quantity(
        type=bool,
        description='Separate flag.',
        a_eln=ELNAnnotation(
            component='BoolEditQuantity',
        ),
    )
    impur_amt = Quantity(
        type=int,
        description='Impurity amount.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
        ),
    )
    skip_filter = Quantity(
        type=bool,
        description='Skip filter flag.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.BoolEditQuantity,
        ),
    )
    include_elems = Quantity(
        type=bool,
        description='Include elements flag.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.BoolEditQuantity,
        ),
    )
    inc_pdf = Quantity(
        type=bool,
        description='Include PDF flag.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.BoolEditQuantity,
        ),
    )
    num_epochs = Quantity(
        type=int,
        description='Number of training epochs.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
        ),
    )
    test_fraction = Quantity(
        type=np.float64,
        description='Fraction of data used for testing.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
        ),
    )

    def normalize(self, archive, logger):
        super().normalize(archive, logger)
        # use the normalization function defined above
        my_normalization(self, archive, logger)


m_package.__init_metainfo__()
