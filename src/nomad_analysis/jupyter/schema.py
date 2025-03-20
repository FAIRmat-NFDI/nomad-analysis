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
    SectionReference,
)
from nomad.metainfo import (
    Category,
    Quantity,
    SchemaPackage,
    Section,
)

from nomad_analysis.utils import (
    create_entry_with_api,
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


class ELNJupyterAnalysis(Analysis, EntryData):
    """
    Base section for ELN Jupyter notebook analysis.
    """

    m_def = Section(
        categories=[JupyterAnalysisCategory],
        label='Jupyter Notebook Analysis',
        a_eln=ELNAnnotation(
            properties=SectionProperties(
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
        default=False,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.BoolEditQuantity,
            default=False,
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

        Returns:
            list: The list of pre-defined code cells.
        """
        user = 'Unknown user'
        if archive.metadata.main_author:
            user = archive.metadata.main_author.name
        cells = []

        source = [
            '<div style="\n',
            '    background-color: #f7f7f7;\n',
            "    background-image: url('data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgd2lkdGg9IjcyIgogICBoZWlnaHQ9IjczIgogICB2aWV3Qm94PSIwIDAgNzIgNzMiCiAgIGZpbGw9Im5vbmUiCiAgIHZlcnNpb249IjEuMSIKICAgaWQ9InN2ZzEzMTkiCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgeG1sbnM6c3ZnPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CiAgPGRlZnMKICAgICBpZD0iZGVmczEzMjMiIC8+CiAgPHBhdGgKICAgICBkPSJNIC0wLjQ5OTk4NSwxNDUgQyAzOS41MzMsMTQ1IDcyLDExMi41MzIgNzIsNzIuNSA3MiwzMi40Njc4IDM5LjUzMywwIC0wLjQ5OTk4NSwwIC00MC41MzI5LDAgLTczLDMyLjQ2NzggLTczLDcyLjUgYyAwLDQwLjAzMiAzMi40NjcxLDcyLjUgNzIuNTAwMDE1LDcyLjUgeiIKICAgICBmaWxsPSIjMDA4YTY3IgogICAgIGZpbGwtb3BhY2l0eT0iMC4yNSIKICAgICBpZD0icGF0aDEzMTciIC8+Cjwvc3ZnPgo='), url('data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgd2lkdGg9IjIxNyIKICAgaGVpZ2h0PSIyMjMiCiAgIHZpZXdCb3g9IjAgMCAyMTcgMjIzIgogICBmaWxsPSJub25lIgogICB2ZXJzaW9uPSIxLjEiCiAgIGlkPSJzdmcxMTA3IgogICB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPgogIDxkZWZzCiAgICAgaWQ9ImRlZnMxMTExIiAvPgogIDxwYXRoCiAgICAgZD0ibSAyMi4wNDIsNDUuMDEwOSBjIDIxLjM2MjUsMjEuMjc1NyA1NS45NzYsMjEuMjc1NyA3Ny41MTkyLDAgQyAxMTkuNTU4LDI1LjA4IDE1MS41MDIsMjMuNzM1MiAxNzIuODY0LDQxLjM3OCBjIDEuMzQ1LDEuNTI1NCAyLjY5LDMuMjUxNiA0LjIzNiw0Ljc5NzEgMjEuMzYzLDIxLjI3NTYgMjEuMzYzLDU1Ljc5ODkgMCw3Ny4yNTQ5IC0yMS4zNjIsMjEuMjc2IC0yMS4zNjIsNTUuNzk4IDAsNzcuMjU1IDIxLjM2MywyMS40NTYgNTUuOTc2LDIxLjI3NSA3Ny41MiwwIDIxLjU0MywtMjEuMjc2IDIxLjM2MiwtNTUuNzk5IDAsLTc3LjI1NSAtMjEuMzYzLC0yMS4yNzYgLTIxLjM2MywtNTUuNzk4NiAwLC03Ny4yNTQ5IDEyLjY4OSwtMTIuNjQ1IDE3Ljg4OSwtMzAuMTA3MSAxNS4zOTksLTQ2LjU4NTc2IC0xLjU0NiwtMTEuNTAwOTQgLTYuNzI2LC0yMi44MjExNCAtMTUuNTgsLTMxLjYzMjU0IC0yMS4zNjMsLTIxLjI3NTYgLTU1Ljk3NiwtMjEuMjc1NiAtNzcuNTE5LDAgLTIxLjM2MywyMS4yNzU3IC01NS45NzYsMjEuMjc1NyAtNzcuNTE5NCwwIC0yMS4zNjI1LC0yMS4yNzU2IC01NS45NzYxLC0yMS4yNzU2IC03Ny41MTkyLDAgQyAwLjY3OTU2NSwtMTAuNzg3NiAwLjY3OTU5NiwyMy43MzUyIDIyLjA0Miw0NS4wMTA5IFoiCiAgICAgZmlsbD0iIzJhNGNkZiIKICAgICBzdHJva2U9IiMyYTRjZGYiCiAgICAgc3Ryb2tlLXdpZHRoPSIxMiIKICAgICBzdHJva2UtbWl0ZXJsaW1pdD0iMTAiCiAgICAgaWQ9InBhdGgxMTA1IiAvPgogIDxwYXRoCiAgICAgZD0ibSA1MS45OTUyMTIsMjIyLjczMDEzIGMgMjguMzU5MSwwIDUxLjM1ODM5OCwtMjIuOTk5OSA1MS4zNTgzOTgsLTUxLjM1ODQgMCwtMjguMzU4NiAtMjIuOTk5Mjk4LC01MS4zNTg1OSAtNTEuMzU4Mzk4LC01MS4zNTg1OSAtMjguMzU5MSwwIC01MS4zNTg2MDIsMjIuOTk5OTkgLTUxLjM1ODYwMiw1MS4zNTg1OSAwLDI4LjM1ODUgMjIuOTk5NTAyLDUxLjM1ODQgNTEuMzU4NjAyLDUxLjM1ODQgeiIKICAgICBmaWxsPSIjMTkyZTg2IgogICAgIGZpbGwtb3BhY2l0eT0iMC4zNSIKICAgICBpZD0icGF0aDE5MzciIC8+Cjwvc3ZnPgo=') ;\n",  # noqa: E501
            '    background-position: left bottom, right top;\n',
            '    background-repeat: no-repeat,  no-repeat;\n',
            '    background-size: auto 60px, auto 160px;\n',
            '    border-radius: 5px;\n',
            '    box-shadow: 0px 3px 1px -2px rgba(0, 0, 0, 0.2), 0px 2px 2px 0px rgba(0, 0, 0, 0.14), 0px 1px 5px 0px rgba(0,0,0,.12);">\n',  # noqa: E501
            '\n',
            '<h1 style="\n',
            '    color: #2a4cdf;\n',
            '    font-style: normal;\n',
            '    font-size: 2.25rem;\n',
            '    line-height: 1.4em;\n',
            '    font-weight: 600;\n',
            '    padding: 30px 200px 0px 30px;"\n',
            f'>{self.name}</h1>\n',
            '<p style="font-size: 1.25em; font-style: italic; padding: 5px 200px 30px 30px;"\n',  # noqa: E501
            f'>{user}</p>\n',
            '</div>\n',
            '\n',
            'This notebook has been generated by a NOMAD Analysis entry with the\n',
            'following definition path:\n',
            f'`{self.m_to_dict()["m_def"]}`',
        ]
        cells.append(
            nbf.v4.new_markdown_cell(
                source=source, metadata={'tags': ['nomad-analysis-predefined']}
            )
        )

        source = [
            '# Run the cell to get the analysis entry linked with this notebook\n',
            'from nomad_analysis.utils import get_analysis_entry\n',
            '\n',
            f'analysis = get_analysis_entry(entry_id="{archive.entry_id}")\n',
            'analysis\n',
        ]
        cells.append(
            nbf.v4.new_code_cell(
                source=source,
                metadata={
                    'tags': [
                        'nomad-analysis-predefined',
                        'nomad-analysis-get-analysis-entry',
                    ]
                },
            )
        )

        return cells

    def generate_jupyter_notebook(
        self, archive: 'EntryArchive', logger: 'BoundLogger'
    ) -> None:
        """
        Generates the notebook and saves it in `raw` folder. If the notebook already
        exists and `reset_notebook` is set to False, function returns without
        modifying the notebook. If `reset_notebook` is set to True, the notebook is
        overwritten with pre-defined cells while preserving the already existing
        user-defined cells.

        Args:
            archive (EntryArchive): The archive containing the section.
            logger (BoundLogger): A structlog logger.
        """

        if archive.m_context.raw_path_exists(self.notebook) and not self.reset_notebook:
            return

        new_notebook = nbf.v4.new_notebook()

        # add the pre-defined cells
        new_notebook.cells.extend(self.write_predefined_cells(archive, logger))

        if self.reset_notebook:
            # add the existing cells
            with archive.m_context.raw_file(self.notebook, 'r') as nb_file:
                old_notebook = nbf.read(nb_file, as_version=nbf.NO_CONVERT)

            for cell in old_notebook.cells:
                if (
                    cell.metadata
                    and cell.metadata.tags
                    and 'nomad-analysis-predefined' in cell.metadata.tags
                ):
                    continue
                new_notebook.cells.append(cell)
        else:
            # add some empty cells
            for _ in range(3):
                new_notebook.cells.append(nbf.v4.new_code_cell())

        new_notebook['metadata']['trusted'] = True

        with archive.m_context.raw_file(self.notebook, 'w') as nb_file:
            nbf.write(new_notebook, nb_file)
        archive.m_context.process_updated_raw_file(self.notebook, allow_modify=True)

    def save(self):
        """
        Uses the NOMAD API to update the entry with the current state.
        """
        create_entry_with_api(
            section=self,
            base_url=self.m_parent.m_context.installation_url,
            upload_id=self.m_parent.metadata.upload_id,
            file_name=self.m_parent.metadata.entry_name,
        )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger'):
        """
        Normalizes the ELN entry to generate a Jupyter notebook.
        """
        super().normalize(archive, logger)

        self.set_jupyter_notebook_name(archive, logger)
        self.normalize_input_references(
            self.process_query_for_inputs(archive, logger), logger
        )

        self.generate_jupyter_notebook(archive, logger)

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
                    'description',
                    'analysis_type',
                ],
            },
        ),
    )

    def write_predefined_cells(self, archive, logger):
        """
        Extends the pre-defined cells with XRD specific analysis functions.
        """

        cells = super().write_predefined_cells(archive, logger)

        comment = '# Analysis functions specific to XRD.\n\n'
        analysis_functions = get_function_source(category_name='XRD')
        source = comment + list_to_string(analysis_functions)
        cells.append(
            nbf.v4.new_code_cell(
                source=source,
                metadata={
                    'tags': [
                        'nomad-analysis-predefined',
                    ]
                },
            )
        )

        source = 'xrd_voila_analysis(analysis.data.inputs)\n'
        cells.append(
            nbf.v4.new_code_cell(
                source=source,
                metadata={
                    'tags': [
                        'nomad-analysis-predefined',
                    ]
                },
            )
        )

        return cells

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger'):
        """
        Sets the analysis type to `XRD` and normalizes the entry.
        """
        self.analysis_type = 'XRD'
        super().normalize(archive, logger)


ELNGenericJupyterAnalysis = ELNJupyterAnalysis

m_package.__init_metainfo__()
