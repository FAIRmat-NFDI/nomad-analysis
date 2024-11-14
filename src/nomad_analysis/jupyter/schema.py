#
# Copyright The NOMAD Authors.
#
# This file is part of NOMAD. See https://nomad-lab.eu for further info.
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

"""
Schema for analysis using Jupyter notebooks.
Allows the user to connect input sections through references. The entry archives from
the input sections are linked and imported into the generated Jupyter notebook.
The notebook can be used to interactively analyse the data from these entry archives.

Schema also allows the user to define the analysis type. Based on the analysis type,
pre-defined code cells are added to the notebook. For example, if the analysis type is
XRD, then the notebook will have pre-defined code cells for XRD analysis. By default,
the analysis type is set to Generic, which includes functions and statements to connect
with the entry archives.

Upcoming features:
- Link the output section of the analysis schema to a sub-section of the input.
- Write the analysis results back to the output section.
"""

import os
from typing import TYPE_CHECKING, Union

import nbformat as nbf
from nomad.datamodel.data import (
    ArchiveSection,
    EntryData,
    EntryDataCategory,
    Query,
)
from nomad.datamodel.metainfo.annotations import (
    BrowserAnnotation,
    ELNAnnotation,
    ELNComponentEnum,
    Filter,
    SectionProperties,
)
from nomad.datamodel.metainfo.basesections import (
    Analysis,
    AnalysisResult,
    SectionReference,
)
from nomad.metainfo import (
    Category,
    Quantity,
    SchemaPackage,
    Section,
    SubSection,
)

from nomad_analysis.utils import (
    create_unique_filename,
    get_function_source,
    list_to_string,
)

if TYPE_CHECKING:
    from nomad.datamodel.datamodel import (
        EntryArchive,
    )
    from structlog.stdlib import (
        BoundLogger,
    )

m_package = SchemaPackage(
    aliases=[
        'nomad_analysis.schema',
    ]
)


class ReferencedEntry(ArchiveSection):
    """
    Section for referenced entry.
    """

    m_proxy_value = Quantity(
        type=str,
        description='The m_proxy_value of the referenced entry.',
    )
    name = Quantity(
        type=str,
        description='The name of the referenced entry.',
    )
    lab_id = Quantity(
        type=str,
        description='The lab_id of the referenced entry.',
    )


class JupyterAnalysisCategory(EntryDataCategory):
    """
    Category for Jupyter notebook analysis.
    """

    m_def = Category(
        label='Jupyter Notebook Analysis',
        categories=[EntryDataCategory],
    )


class JupyterAnalysisResult(AnalysisResult):
    """
    Section for collecting Jupyter notebook analysis results.
    It is a non-editable section that is populated once the processing is.

    TODO: One can also create a custom schema for results and
    define it as a sub-section here.
    """

    m_def = Section(
        label='Jupyter Notebook Analysis Results',
    )
    connection_status = Quantity(
        type=str,
        default='Not connected',
        description='Status of connection with Jupyter notebook',
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger'):
        """
        The normalize function for `JupyterAnalysisResult` section.

        Args:
            archive (EntryArchive): The archive containing the section.
            logger (BoundLogger): A structlog logger.
        """
        super().normalize(archive, logger)


class JupyterAnalysis(Analysis):
    """
    Generic class for Jupyter notebook analysis.
    """

    m_def = Section()
    inputs = SubSection(
        section_def=SectionReference,
        description='The input sections for the analysis',
    )
    outputs = SubSection(
        section_def=SectionReference,
        description='The result section for the analysis',
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger'):
        """
        The normalize function for `JupyterAnalysis` section.

        Args:
            archive (EntryArchive): The archive containing the section.
            logger (BoundLogger): A structlog logger.
        """
        super().normalize(archive, logger)


class ELNJupyterAnalysis(JupyterAnalysis, EntryData):
    """
    Base section for ELN Jupyter notebook analysis.
    """

    m_def = Section(
        categories=[JupyterAnalysisCategory],
        label='Jupyter Notebook Analysis',
        a_eln=ELNAnnotation(
            properties=SectionProperties(
                visible=Filter(
                    exclude=['input_entry_class'],
                ),
                order=[
                    'name',
                    'datetime',
                    'lab_id',
                    'location',
                    'notebook',
                    'reset_notebook',
                    'query_for_inputs',
                    'description',
                    'analysis_type',
                ],
            ),
        ),
    )
    analysis_type = Quantity(
        type=str,
        default='Generic',
        description=(
            'Based on the analysis type, code cells will be added to the Jupyter '
            'notebook. Code cells from **Generic** are always included.'
            """
            | Analysis Type       | Description                                     |
            |---------------------|-------------------------------------------------|
            | **Generic**         | (Default) Basic setup including connection \
                                    with entry data.                                |
            | **XRD**             | Adds XRD related analysis functions.            |
            """
        ),
    )
    reset_notebook = Quantity(
        type=bool,
        description=(
            '**Caution** This will reset the pre-defined cells of the notebook. '
            'All customization to these cells will be lost.\n'
            'In case the notebook is not available as a raw file'
            ', it will be generated.\n'
            'Resetting or generating a notebook will be based on the analysis type.'
        ),
        default=True,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.BoolEditQuantity,
        ),
    )
    notebook = Quantity(
        type=str,
        description='Generated Jupyter notebook file.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.FileEditQuantity,
        ),
        a_browser=BrowserAnnotation(adaptor='RawFileAdaptor'),
    )
    query_for_inputs = Quantity(
        type=Query,
        description='Query to get the input entries for the analysis.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.QueryEditQuantity,
            props=dict(
                storeInArchive=True,
            ),
        ),
    )

    # deprecated in favor of `query_for_inputs`; non-functional
    input_entry_class = Quantity(
        type=str,
        description="""
        Reference all the available entries of this EntryClass as inputs.
        (Deprecated in favor of `query_for_inputs`)
        """,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.StringEditQuantity,
        ),
    )

    def set_jupyter_notebook_name(
        self, archive: 'EntryArchive', logger: 'BoundLogger'
    ) -> None:
        """
        Sets the name of notebook in accordance to self.name.

        Args:
            archive (EntryArchive): The archive containing the section.
            logger (BoundLogger): A structlog logger.
        """
        if self.name:
            file_name = (
                self.name.replace(' ', '_')
                + '_'
                + self.analysis_type.lower()
                + '_notebook.ipynb'
            )
        else:
            file_name = create_unique_filename(
                archive=archive, prefix='untitled', suffix='ipynb'
            )

        if self.notebook is None:
            self.notebook = file_name
            return

        if self.notebook != file_name:
            raw_path = archive.m_context.raw_path()
            os.rename(
                os.path.join(raw_path, self.notebook),
                os.path.join(raw_path, file_name),
            )
            archive.m_context.process_updated_raw_file(file_name, allow_modify=True)
            self.notebook = file_name

    def get_resolved_section(
        self,
        m_proxy_value: str,
        upload_id: str,
        archive: 'EntryArchive',
        logger: 'BoundLogger',
    ) -> Union['ArchiveSection', None]:
        """
        Get the resolved reference of the input entry class.

        Args:
            m_proxy_value (str): The m_proxy_value of the reference.
            upload_id (str): The upload_id of the reference.
            archive (EntryArchive): The archive containing the section.
            logger (BoundLogger): A structlog logger.

        Returns:
            Union[ArchiveSection, None]: The resolved archive or None.
        """
        from nomad.app.v1.models.models import User
        from nomad.app.v1.routers.uploads import get_upload_with_read_access
        from nomad.datamodel.context import ServerContext

        try:
            reference = SectionReference(reference=m_proxy_value)
            context = ServerContext(
                get_upload_with_read_access(
                    upload_id,
                    User(
                        is_admin=True,
                        user_id=archive.metadata.main_author.user_id,
                    ),
                )
            )
            reference.reference.m_proxy_context = context
            return reference.reference

        except Exception as e:
            logger.warning(f'Could not resolve the reference {m_proxy_value}.\n{e}')

        return None

    def process_query_for_inputs(
        self, archive: 'EntryArchive', logger: 'BoundLogger'
    ) -> list[ReferencedEntry]:
        """
        Get the input entries based on the `query_for_inputs`.

        Args:
            archive (EntryArchive): The archive containing the section.
            logger (BoundLogger): A structlog logger.

        Returns:
            list[ReferencedEntry]: The list of input entries.
        """
        ref_list = []
        entries = []

        # extend the entries with the data from query_for_inputs
        if self.query_for_inputs is not None:
            entries.extend(self.query_for_inputs['data'])

        for entry in entries:
            entry_id = entry['entry_id']
            upload_id = entry['upload_id']
            resolved_section = self.get_resolved_section(
                f'../uploads/{upload_id}/archive/{entry_id}#/data',
                entry['upload_id'],
                archive,
                logger,
            )
            if resolved_section is None:
                continue
            ref = ReferencedEntry(
                m_proxy_value=f'../uploads/{upload_id}/archive/{entry_id}#/data',
                name=resolved_section.get('name'),
                lab_id=resolved_section.get('lab_id'),
            )
            if resolved_section.get('lab_id') is not None:
                ref.name = resolved_section.get('lab_id')
            ref_list.append(ref)

        return ref_list

    def normalize_input_references(
        self,
        ref_list: list[ReferencedEntry] = None,
        logger: 'BoundLogger' = None,
    ):
        """
        Combines the existing input references with provided list of references.
        Filters out duplicates based on m_proxy_value and lab_id.
        Sets the name of the input references.
        """

        def normalize_m_proxy_value(m_proxy_value):
            """
            Normalize the m_proxy_value (in-place) by adding forward slash in the
            beginning of section path. For e.g., '../uploads/1234/archive/5678#data'
            will be modified to '../uploads/1234/archive/5678#/data'.

            Args:
                m_proxy_value (str): The m_proxy_value to be normalized.
            """
            try:
                entry_path, section_path = m_proxy_value.split('#')
                if not section_path.startswith('/'):
                    return f'{entry_path}#/{section_path}'
            except Exception as e:
                logger.warning(
                    f'Error in normalizing the m_proxy_value "{m_proxy_value}".\n{e}'
                )
            return m_proxy_value

        def set_name_for_inputs():
            """
            Set the name of the input references based on the lab_id or name of the
            referenced section. If lab_id, it is preferred over the name. If both are
            not available, the reference name remains the default: None.
            """
            for input_ref in self.inputs:
                if input_ref.name is not None:
                    continue
                if input_ref.reference.name is None:
                    continue
                if input_ref.reference.get('lab_id') is not None:
                    input_ref.name = input_ref.reference.lab_id
                elif input_ref.reference.get('name') is not None:
                    input_ref.name = input_ref.reference.name

        if ref_list is None:
            ref_list = []

        # add the existing input references
        for input_ref in self.inputs:
            if input_ref.reference is None:
                continue
            ref = ReferencedEntry(
                m_proxy_value=input_ref.reference.m_proxy_value,
                name=input_ref.name,
                lab_id=input_ref.reference.get('lab_id'),
            )
            ref_list.append(ref)

        # normalize m_proxy_value
        for ref in ref_list:
            ref.m_proxy_value = normalize_m_proxy_value(ref.m_proxy_value)

        # filter based on m_proxy_value, and lab_id (if available)
        ref_hash_map = {}
        filtered_ref_list = []
        for ref in ref_list:
            if ref.m_proxy_value in ref_hash_map:
                continue
            if ref.lab_id is not None and ref.lab_id in ref_hash_map.values():
                continue
            ref_hash_map[ref.m_proxy_value] = ref.lab_id
            filtered_ref_list.append(ref)

        self.inputs = []
        for ref in filtered_ref_list:
            self.inputs.append(
                SectionReference(reference=ref.m_proxy_value, name=ref.name)
            )

        set_name_for_inputs()

    def write_predefined_cells(
        self, archive: 'EntryArchive', logger: 'BoundLogger'
    ) -> list:
        """
        Writes the pre-defined Jupyter notebook cells based on the analysis type.

        Args:
            archive (EntryArchive): The archive containing the section.
            logger (BoundLogger): A structlog logger.
        """
        entry_ids = []
        if self.inputs is not None:
            for entry in self.inputs:
                entry_ids.append(entry.reference.m_parent.entry_id)
        if len(entry_ids) == 0:
            logger.warning('No EntryArchive linked.')

        cells = []

        code = (
            '# Pre-defined block\n'
            '\n'
            '# This notebook has been generated by "Jupyter Notebook Analysis" '
            'schema.\n'
            '# It gets the data from the entries referenced in the `inputs` '
            'sub-section.\n'
            '# It also gets the analysis function based on the analysis type '
            '(e.g., XRD).'
        )
        cells.append(nbf.v4.new_code_cell(source=code))

        generic_analysis_functions = get_function_source(category_name='Generic')
        generic_analysis_functions = list_to_string(generic_analysis_functions)

        code = (
            '# Pre-defined block\n'
            '\n'
            f'analysis_entry_id = "{archive.entry_id}"\n'
            '\n'
            f'{generic_analysis_functions}'
            'analysis = get_analysis_entry(analysis_entry_id)\n'
            'analysis\n'
        )
        cells.append(nbf.v4.new_code_cell(source=code))

        if self.analysis_type is not None and self.analysis_type != 'Generic':
            comment = (
                '# Pre-defined block\n'
                '\n'
                f'# Analysis functions specific to "{self.analysis_type}".\n'
                '\n'
            )
            analysis_functions = get_function_source(category_name=self.analysis_type)
            code = list_to_string(analysis_functions)
            cells.append(nbf.v4.new_code_cell(source=comment + code))

        if self.analysis_type == 'XRD':
            code = '# Pre-defined block\n' '\n' 'xrd_voila_analysis(input_data)\n'
            cells.append(nbf.v4.new_code_cell(source=code))

        return cells

    def generate_jupyter_notebook(
        self, archive: 'EntryArchive', logger: 'BoundLogger'
    ) -> None:
        """
        Generates the notebook `ELNJupyterAnalysis.ipynb` and saves it in `raw` folder.

        Args:
            archive (EntryArchive): The archive containing the section.
            logger (BoundLogger): A structlog logger.
        """
        nb = nbf.v4.new_notebook()

        cells = self.write_predefined_cells(archive, logger)

        cells.append(nbf.v4.new_code_cell())
        cells.append(nbf.v4.new_code_cell())
        cells.append(nbf.v4.new_code_cell())

        for cell in cells:
            nb.cells.append(cell)

        nb['metadata']['trusted'] = True

        with archive.m_context.raw_file(self.notebook, 'w') as nb_file:
            nbf.write(nb, nb_file)
        archive.m_context.process_updated_raw_file(self.notebook, allow_modify=True)

    def overwrite_jupyter_notebook(
        self, archive: 'EntryArchive', logger: 'BoundLogger'
    ) -> None:
        """
        Overwrites the Jupyter notebook to reset predefined cells while preserving the
        other user-defined cells.

        Args:
            archive (EntryArchive): The archive containing the section.
            logger (BoundLogger): A structlog logger.
        """
        cells = self.write_predefined_cells(archive, logger)

        with archive.m_context.raw_file(self.notebook, 'r') as nb_file:
            nb = nbf.read(nb_file, as_version=nbf.NO_CONVERT)

        for cell in nb.cells:
            if cell.source.startswith('# Pre-defined block'):
                continue
            cells.append(cell)

        nb.cells = cells

        nb['metadata']['trusted'] = True

        with archive.m_context.raw_file(self.notebook, 'w') as nb_file:
            nbf.write(nb, nb_file)
        archive.m_context.process_updated_raw_file(self.notebook, allow_modify=True)

    def write_jupyter_notebook(
        self, archive: 'EntryArchive', logger: 'BoundLogger'
    ) -> None:
        """
        Writes the Jupyter notebook based on the analysis type.

        Args:
            archive (EntryArchive): The archive containing the section.
            logger (BoundLogger): A structlog logger.
        """
        if not self.notebook or not archive.m_context.raw_path_exists(self.notebook):
            self.generate_jupyter_notebook(archive, logger)
        else:
            self.overwrite_jupyter_notebook(archive, logger)

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger'):
        """
        Normalizes the ELN entry to generate a Jupyter notebook.
        """
        super().normalize(archive, logger)

        self.set_jupyter_notebook_name(archive, logger)
        self.normalize_input_references(
            self.process_query_for_inputs(archive, logger), logger
        )

        if self.reset_notebook:
            self.write_jupyter_notebook(archive, logger)
            self.reset_notebook = False

        super().normalize(archive, logger)


class ELNXRDJupyterAnalysis(ELNJupyterAnalysis, EntryData):
    """
    Entry section for Jupyter notebook analysis with `XRD` analysis type.
    """

    m_def = Section(
        label='XRD Jupyter Notebook Analysis',
        a_eln=ELNAnnotation(
            properties={
                'order': [
                    'name',
                    'datetime',
                    'lab_id',
                    'location',
                    'notebook',
                    'reset_notebook',
                    'query_for_inputs',
                    'input_entry_class',
                    'description',
                    'analysis_type',
                ],
            },
        ),
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger'):
        self.analysis_type = 'XRD'
        super().normalize(archive, logger)


ELNGenericJupyterAnalysis = ELNJupyterAnalysis

m_package.__init_metainfo__()
