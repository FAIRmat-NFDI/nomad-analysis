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
    SectionProperties,
)
from nomad.datamodel.metainfo.basesections import Measurement, SectionReference
from nomad.datamodel.results import Material, SymmetryNew, System
from nomad.metainfo import (
    Quantity,
    SchemaPackage,
    Section,
    SubSection,
)
from nomad.normalizing.common import nomad_atoms_from_ase_atoms
from nomad.normalizing.topology import add_system, add_system_info

from nomad_analysis.jupyter.schema import JupyterAnalysis

if TYPE_CHECKING:
    from structlog.stdlib import (
        BoundLogger,
    )

m_package = SchemaPackage()


class SimulationSettings(ArchiveSection):
    """
    A schema for the settings for simulating XRD patterns.
    """

    structure_files = Quantity(
        type=str,
        shape=['*'],
        description='Path to structure file (CIF) containing crystal structure.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.FileEditQuantity,
        ),
        a_browser=BrowserAnnotation(adaptor='RawFileAdaptor'),
    )
    max_texture = Quantity(
        type=np.float64,
        description='Maximum texture value for the simualtions.',
        default=0.5,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
        ),
    )
    min_domain_size = Quantity(
        type=np.float64,
        description='Minimum domain size.',
        unit='nm',
        default=5.0,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
        ),
    )
    max_domain_size = Quantity(
        type=np.float64,
        description='Maximum domain size.',
        unit='nm',
        default=30.0,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
        ),
    )
    max_strain = Quantity(
        type=np.float64,
        description='Maximum strain value.',
        default=0.03,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
        ),
    )
    num_patterns = Quantity(
        type=int,
        description='Number of XRD patterns simulated per phase.',
        default=50,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
        ),
    )
    min_angle = Quantity(
        type=np.float64,
        description='Minimum angle value.',
        unit='deg',
        default=20.0,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
        ),
    )
    max_angle = Quantity(
        type=np.float64,
        description='Maximum angle value.',
        unit='deg',
        default=80.0,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
        ),
    )
    max_shift = Quantity(
        type=np.float64,
        description='Maximum shift value.',
        unit='deg',
        default=0.1,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
        ),
    )
    separate = Quantity(
        type=bool,
        description='Separate flag.',
        default=True,
        a_eln=ELNAnnotation(
            component='BoolEditQuantity',
        ),
    )
    impur_amt = Quantity(
        type=np.float64,
        description='Impurity amount.',
        default=0.0,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
        ),
    )
    skip_filter = Quantity(
        type=bool,
        description='Skip filter flag.',
        default=False,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.BoolEditQuantity,
        ),
    )
    include_elems = Quantity(
        type=bool,
        description='Include elements flag.',
        default=True,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.BoolEditQuantity,
        ),
    )


class TrainingSettings(ArchiveSection):
    """
    A schema for the settings for training the model.
    """

    num_epochs = Quantity(
        type=int,
        description='Number of training epochs.',
        default=50,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
        ),
    )
    batch_size = Quantity(
        type=int,
        description='Batch size for training.',
        default=32,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
        ),
    )
    learning_rate = Quantity(
        type=np.float64,
        description='Learning rate for training.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
        ),
    )
    seed = Quantity(
        type=int,
        description='Seed for random number generator.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
        ),
    )
    test_fraction = Quantity(
        type=np.float64,
        description='Fraction of data used for testing.',
        default=0.2,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
        ),
    )
    enable_wandb = Quantity(
        type=bool,
        description='Flag to enable "Weights and Biases" logging.',
        default=False,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.BoolEditQuantity,
        ),
    )
    wandb_project = Quantity(
        type=str,
        description='"Weights and Biases" project name.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.StringEditQuantity,
        ),
    )
    wandb_entity = Quantity(
        type=str,
        description='"Weights and Biases" entity name.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.StringEditQuantity,
        ),
    )


class AutoXRDModel(Schema):
    """
    Section for describing an auto XRD model.
    """

    m_def = Section(
        description="""
        Based on the structure files (CIF files) added, XRD patterns are simulated
        for different phase compositions and structures. The simulated XRD patterns are
        then used to train a machine learning model to predict the phase composition
        and structure from the XRD data.""",
    )
    working_directory = Quantity(
        type=str,
        description='Path to the directory containing the simulated data and trained '
        'models.',
        default='nomad_auto_xrd',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.StringEditQuantity,
        ),
    )
    reference_files = Quantity(
        type=str,
        shape=['*'],
        description='Path to the filtered reference structure files (.cif) used to '
        'train the model.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.FileEditQuantity,
        ),
        a_browser=BrowserAnnotation(adaptor='RawFileAdaptor'),
    )
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
        description='URL to the "Weights and Biases" run containing the trained model.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.URLEditQuantity,
        ),
    )
    includes_pdf = Quantity(
        type=bool,
        description='Flag to indicate if an additional model was trained using the '
        'virtual pairwise distribution functions or PDFs computed through a Fourier '
        'transform of the simulated XRD patterns.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.BoolEditQuantity,
        ),
    )
    simulation_settings = SubSection(
        section_def=SimulationSettings,
        description='Settings for simulating XRD patterns.',
    )
    training_settings = SubSection(
        section_def=TrainingSettings,
        description='Settings for training the model.',
    )

    def normalize(self, archive: 'ArchiveSection', logger: 'BoundLogger'):
        super().normalize(archive, logger)
        if self.reference_files is not None:
            # Read the reference CIF files and convert them into ase atoms
            ase_atoms_list = []
            for cif_file in self.reference_files:
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
    """
    A reference to an `AutoXRDModel` entry.
    """

    reference = Quantity(
        type=AutoXRDModel,
        description='A reference to an `AutoXRDModel` entry.',
        a_eln=ELNAnnotation(
            component='ReferenceEditQuantity',
        ),
    )


class AutoXRDMeasurementReference(SectionReference):
    """
    A reference to an `Measurement` entry.
    """

    reference = Quantity(
        type=Measurement,
        description='A reference to an `Measurement` entry.',
        a_eln=ELNAnnotation(
            component='ReferenceEditQuantity',
        ),
    )


class IdentifiedPhase(ArchiveSection):
    """
    Section for the identified phase.
    """

    phase = Quantity(
        type=str,
        description='The identified phase in the XRD data.',
    )
    reference_structure = Quantity(
        type=System,
        description='The reference structure of the identified phase in the training '
        'data.',
        a_eln=ELNAnnotation(
            component='ReferenceEditQuantity',
        ),
    )
    probability = Quantity(
        type=float,
        description='The probability that the phase is present.',
    )


class AutoXRDTraining(JupyterAnalysis):
    """
    Schema for training an auto XRD model. Generates a Jupyter notebook containing
    helper code to train and index the model NOMAD.
    """

    m_def = Section(
        a_eln=ELNAnnotation(
            properties=SectionProperties(
                order=[
                    'name',
                    'datetime',
                    'lab_id',
                    'location',
                    'description',
                    'method',
                    'query_for_inputs',
                    'notebook',
                    'action_trigger',
                ],
            ),
        ),
    )
    description = Quantity(
        description='A description of the auto XRD model training.',
        a_eln=ELNAnnotation(
            component='RichTextEditQuantity',
            props=dict(height=500),
        ),
    )
    outputs = SubSection(
        section_def=AutoXRDModelReference,
        repeats=True,
        description='An `AutoXRDModel` trained to predict phases in a given composition'
        'space.',
    )

    def write_predefined_cells(self, archive, logger):
        """
        Extends the `write_predefined_cells` method to add additional cells specific to
        the Auto XRD Training.
        """
        cells = super().write_predefined_cells(archive, logger)

        source = [
            '## Training Auto XRD Model\n',
            '\n',
            'For training the Auto XRD model, we need to simulate XRD patterns for\n',
            'different composition and phases covering an expected composition\n',
            'space. Once the training data is setup, we train a CNN model capable of\n',
            'phase identification from real XRD patterns.\n',
            '\n',
            'The workflow is managed by `nomad_auto_xrd.training` module which uses\n',
            'the [XRD-AutoAnalyzer](https://github.com/njszym/XRD-AutoAnalyzer)\n',
            'package under the hood. `nomad_auto_xrd.training.train` takes\n',
            '`AutoXRDModel` NOMAD section as input. The section can be used to\n',
            'specify the settings for simulating XRD patterns and training the\n',
            'model.\n',
        ]
        cells.append(
            nbformat.v4.new_markdown_cell(
                source=source,
                metadata={'tags': ['nomad-analysis-predefined']},
            )
        )

        source = [
            'from nomad_analysis.auto_xrd.schema import (\n',
            '    SimulationSettings,\n',
            '    TrainingSettings,\n',
            '    AutoXRDModel,\n',
            ')\n',
            '\n',
            '# either specify or use the default settings\n',
            'training_settings = TrainingSettings(\n',
            '    num_epochs=2,\n',
            '    batch_size=32,\n',
            '    learning_rate=0.001,\n',
            '    seed=43,\n',
            ')\n',
            'simulation_settings = SimulationSettings()\n',
            'model = AutoXRDModel(\n',
            "    working_directory='.',\n",
            '    training_settings=training_settings,\n',
            '    simulation_settings=simulation_settings,\n',
            '    includes_pdf=True,\n',
            ')\n',
        ]
        cells.append(
            nbformat.v4.new_code_cell(
                source=source,
                metadata={'tags': ['nomad-analysis-predefined']},
            ),
        )

        source = [
            '## Training the Model\n',
            '\n',
            'Next, we add the path to the structure files (CIF files) containing\n',
            'the crystal structures to be used for setting up training data.\n',
            'Then, we train the model using the `train` function.\n',
        ]
        cells.append(
            nbformat.v4.new_markdown_cell(
                source=source,
                metadata={'tags': ['nomad-analysis-predefined']},
            ),
        )

        source = [
            'from nomad_auto_xrd.training import train\n',
            '\n',
            'structure_files =\n',
            'model.simulation_settings.structure_files = structure_files\n',
            '\n',
            'train(model)',
        ]
        cells.append(
            nbformat.v4.new_code_cell(
                source=source,
                metadata={'tags': ['nomad-analysis-predefined']},
            ),
        )

        source = [
            '## Saving the Model\n',
            '\n',
            'After training successfully, we can find that `model.models` is\n',
            'populated with the path to the trained model file. Additionally, \n',
            '`model.reference_structures` holds a list of section references to \n',
            'possible structures that can be predicted by the model. \n',
            '\n',
            'Let us now make an entry for this model in NOMAD, after which you can\n',
            'use the model entry to run Auto XRD analysis.\n',
            'We will also save a reference to model entry from the analysis entry.\n',
        ]
        cells.append(
            nbformat.v4.new_markdown_cell(
                source=source,
                metadata={'tags': ['nomad-analysis-predefined']},
            ),
        )

        source = [
            'from nomad_analysis.utils import create_entry_with_api\n',
            '\n',
            "analysis.m_setdefault('outputs/0')\n",
            '\n',
            'analysis.outputs[0].reference = create_entry_with_api(\n',
            '    model,\n',
            '    base_url=analysis.m_context.installation_url,\n',
            '    upload_id=analysis.m_context.upload_id,\n',
            "    file_name=f'{analysis.name}_auto_xrd_model.archive.json',\n",
            ')\n',
        ]
        cells.append(
            nbformat.v4.new_code_cell(
                source=source,
                metadata={'tags': ['nomad-analysis-predefined']},
            ),
        )

        return cells

    def normalize(self, archive, logger):
        """
        Normalizes the `AutoXRDAnalysis` entry.

        Args:
            archive (Archive): A NOMAD archive.
            logger (Logger): A structured logger.
        """
        self.method = 'Auto XRD Model Training'
        if self.description is None or self.description == '':
            self.description = """
            <p>
            This ELN comes with a Jupyter notebook that can be used to train an ML model
            for automatic phase identification from XRD data. The trained model can be
            indexed with `AutoXRDModel` entry which saves related metadata. </p> <p>

            From the <strong><em>notebook</em></strong> quantity, open the the
            Jupyter notebook and follow the steps mentioned in there to perform the
            training.</p>
            """
        super().normalize(archive, logger)


class AutoXRDAnalysis(JupyterAnalysis):
    """
    Schema for running an auto XRD analysis using an pre-trained ML model.
    """

    m_def = Section(
        a_eln=ELNAnnotation(
            properties=SectionProperties(
                order=[
                    'name',
                    'datetime',
                    'lab_id',
                    'location',
                    'description',
                    'method',
                    'query_for_inputs',
                    'notebook',
                    'action_trigger',
                    'inputs',
                    'identified_phases',
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
    identified_phases = SubSection(
        section_def='IdentifiedPhase',
        repeats=True,
        description='The identified phases in the XRD data.',
    )

    def write_predefined_cells(self, archive, logger):
        cells = super().write_predefined_cells(archive, logger)

        # TODO add the code to run the analysis in notebook

        return cells

    def normalize(self, archive, logger):
        """
        Normalizes the `AutoXRDAnalysis` entry.

        Args:
            archive (Archive): A NOMAD archive.
            logger (Logger): A structured logger.
        """
        self.method = 'Auto XRD Analysis'
        if self.description is None or self.description == '':
            self.description = """
            <p>
            This ELN comes with a Jupyter notebook that can be used to run an auto
            XRD analysis using a pre-trained ML model. To get started, do the
            following:</p> <p>

            1. In the <strong><em>inputs</em></strong> sub-section, use the
            <strong><em>AutoXRDModelReference</em></strong> section to reference an
            <strong><em>AutoXRDModel</em></strong> entry containing the pre-trained
            model. Select a model trained on a composition space that includes the
            composition of the given sample.
            </p> <p>

            2. In the <strong><em>inputs</em></strong> sub-section, use the
            <strong><em>AutoXRDMeasurementReference</em></strong> section to reference
            an <strong><em>ELNXRayDiffraction</em></strong> entry containing the XRD
            data for which phases are to be identified.</p> <p>

            3. From the <strong><em>notebook</em></strong> quantity, open the the
            Jupyter notebook and follow the steps mentioned in there to perform the
            analysis.</p>
            """
        super().normalize(archive, logger)


m_package.__init_metainfo__()
