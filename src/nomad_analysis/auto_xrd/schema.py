#
# Copyright The NOMAD Authors.
#
# This file is part of NOMAD.
# See https://nomad-lab.eu for further info.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import os
from typing import (
    TYPE_CHECKING,
)

import nbformat
import numpy as np
from ase.io import read
from matid import SymmetryAnalyzer
from nomad.datamodel import ArchiveSection
from nomad.datamodel.data import Schema
from nomad.datamodel.metainfo.annotations import (
    BrowserAnnotation,
    ELNAnnotation,
    ELNComponentEnum,
    Filter,
    SectionProperties,
)
from nomad.datamodel.results import Material, SymmetryNew, System
from nomad.metainfo import (
    Quantity,
    SchemaPackage,
    Section,
    SubSection,
)
from nomad.normalizing.common import nomad_atoms_from_ase_atoms
from nomad.normalizing.topology import add_system, add_system_info

from nomad_analysis.general.schema import AnalysisResult
from nomad_analysis.jupyter.schema import ELNJupyterAnalysis

if TYPE_CHECKING:
    from structlog.stdlib import (
        BoundLogger,
    )

m_package = SchemaPackage()


class SimulationSettings(ArchiveSection):
    """
    A schema for the settings for simulating XRD patterns.
    """

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


class TrainingSettings(ArchiveSection):
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


class AutoXRDModel(Schema):
    """
    A schema for hosting data from an
    [XRD-AutoAnalyzer](https://github.com/njszym/XRD-AutoAnalyzer) model.
    """

    models = Quantity(
        type=str,
        shape=['*'],
        description='Path to the trained model file.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.FileEditQuantity,
        ),
        a_browser=BrowserAnnotation(adaptor='RawFileAdaptor'),
    )
    wandb_run_urls = Quantity(
        type=str,
        shape=['*'],
        description='URL to the W&B run containing the PDF model.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.URLEditQuantity,
        ),
    )
    structure_files = Quantity(
        type=str,
        shape=['*'],
        description='Path to structure file (CIF) containing crystal structure.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.FileEditQuantity,
        ),
        a_browser=BrowserAnnotation(adaptor='RawFileAdaptor'),
    )
    inc_pdf = Quantity(
        type=bool,
        description='Include PDF flag.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.BoolEditQuantity,
        ),
    )
    simulation_settings = SubSection(
        section_def='SimulationSettings',
        description='Settings for simulating XRD patterns.',
    )
    training_settings = SubSection(
        section_def='TrainingSettings',
        description='Settings for training the model.',
    )

    def normalize(self, archive: 'ArchiveSection', logger: 'BoundLogger'):
        super().normalize(archive, logger)
        if self.structure_files is not None:
            # Read the CIF files and convert them into ase atoms
            ase_atoms_list = []
            for cif_file in self.structure_files:
                if not cif_file.endswith('.cif'):
                    logger.warn(
                        f'Cannot parse structure file: {cif_file}. '
                        'Should be a "*.cif" file.'
                    )
                    continue
                with archive.m_context.raw_file(cif_file) as file:
                    try:
                        ase_atoms_list.append(read(file.name))
                    except RuntimeError:
                        logger.warn(f'Cannot parse cif file: {cif_file}.')

            # Let's save the composition and structure into archive.results.material
            if not archive.results.material:
                archive.results.material = Material()

            # populate elemets from a set aof all the elemsts in ase_atoms
            elements = set()
            for ase_atoms in ase_atoms_list:
                elements.update(ase_atoms.get_chemical_symbols())
            archive.results.material.elements = list(elements)

            # Create a System: this is a NOMAD specific data structure for
            # storing structural and chemical information that is suitable for both
            # experiments and simulations.
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


class AutoXRDModelReference(SectionReference):
    reference = Quantity(
        type=SectionReference,
        description='A reference to an `AutoXRDModel` entry.',
        a_eln=ELNAnnotation(
            component='ReferenceEditQuantity',
        ),
    )


class IdentifiedPhase(AnalysisResult):
    """
    Section for the identified phase.
    """

    phase = Quantity(
        type=str,
        description='The identified phase in the XRD data.',
    )
    reference_cif = Quantity(
        type=str,
        description='The reference CIF file.',
        a_eln=ELNAnnotation(
            component='FileEditQuantity',
        ),
    )
    probability = Quantity(
        type=float,
        description='The probability that the phase is present.',
    )


class AutoXRDTraining(ELNJupyterAnalysis):
    def normalize(self, archive, logger):
        super().normalize(archive, logger)
        for output in self.outputs:
            if isinstance(output, AutoXRDModelReference):
                # trigger a reprocessing of the AutoXRDModel
                output.reference.normalize(archive, logger)


class AutoXRDAnalysisInput(SectionReference):
    """
    Base class for all `AutoXRDAnalysis` inputs.
    """


class AutoXRDAnalysis(ELNJupyterAnalysis):
    """
    Schema for running an auto XRD analysis using an pre-trained ML model.
    """

    m_def = Section(
        a_eln=ELNAnnotation(
            properties=SectionProperties(
                visible=Filter(
                    exclude=['input_entry_class', 'query_for_inputs'],
                ),
                order=[
                    'name',
                    'datetime',
                    'lab_id',
                    'location',
                    'notebook',
                    'reset_notebook',
                    'description',
                    'analysis_type',
                ],
            ),
        ),
    )
    description = Quantity(
        type=str,
        description='A description of the auto XRD analysis.',
        a_eln=ELNAnnotation(
            component='RichTextEditQuantity',
            props=dict(height=500),
        ),
    )
    analysis_type = Quantity(
        type=str,
        default='Auto XRD',
        description=(
            'Based on the analysis type, code cells will be added to the Jupyter '
            'notebook. Code cells from **Generic** are always included.'
            """
            | Analysis Type       | Description                                     |
            |---------------------|-------------------------------------------------|
            | **Generic**         | Basic setup including connection \
                                    with entry data.                                |
            | **XRD**             | Adds XRD related analysis functions.            |
            | **Auto XRD**        | (Default) Analysis XRD patterns using machine \
                                    learning.                                       |
            """
        ),
    )
    inputs = SubSection(
        section_def=SectionReference,
        description='The input section for the auto XRD analysis.',
        repeats=True,
    )
    outputs = SubSection(
        section_def=IdentifiedPhase,
        description='The phases identified by the auto XRD analysis.',
        repeats=True,
    )

    def write_jupyter_notebook(self, archive, logger):
        """
        Writes the Jupyter notebook for the `AutoXRDAnalysis` entry.
        Uses the notebook template from the `nomad_auto_xrd/jupyter_notebooks`.
        Overwrites the `analysis_entry_id` in the notebook with the current entry id.
        """

        module_path = os.path.abspath(__file__)
        package_path = os.path.dirname(os.path.dirname(module_path))
        notebook_path = os.path.join(
            package_path, 'jupyter_notebooks', 'auto-xrd-analysis.ipynb'
        )
        with open(notebook_path, encoding='utf-8') as f:
            nb = nbformat.read(f, as_version=4)
        for cell in nb.cells:
            if cell.cell_type == 'code':
                if 'analysis_entry_id' in cell.metadata.get('tags', []):
                    cell.source = f'analysis_entry_id = "{archive.entry_id}"'
                    break

        nb['metadata']['trusted'] = True

        with archive.m_context.raw_file(self.notebook, 'w') as nb_file:
            nbformat.write(nb, nb_file)
        archive.m_context.process_updated_raw_file(self.notebook, allow_modify=True)

    def normalize(self, archive, logger):
        """
        Normalizes the `AutoXRDAnalysis` entry.

        Args:
            archive (Archive): A NOMAD archive.
            logger (Logger): A structured logger.
        """
        super().normalize(archive, logger)
        if self.description is None or self.description == '':
            self.description = """
            <p>
            This ELN comes with a Jupyter notebook that can be used to run an auto
            XRD analysis using a pre-trained ML model. To get started, do the
            following:</p> <p>

            1. In the <strong><em>inputs</em></strong> sub-section, use the
            <strong><em>AutoXRDModelReference</em></strong> section to reference an
            <strong><em>AutoXRDModel</em></strong> entry containing the pre-trained
            model.</p> <p>

            2. In the <strong><em>inputs</em></strong> sub-section, use the
            <strong><em>XRDMeasurement</em></strong> section to reference an
            <strong><em>ELNXRayDiffraction</em></strong> containing the XRD data
            you want to analyse.</p> <p>

            3. From the <strong><em>notebook</em></strong> quantity, open the the
            Jupyter notebook and follow the steps mentioned in there to perform the
            analysis.</p>
            """


m_package.__init_metainfo__()
