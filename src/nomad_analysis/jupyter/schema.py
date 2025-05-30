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
import os
from typing import TYPE_CHECKING, Union

import nbformat as nbf
from nomad.datamodel.context import ServerContext
from nomad.datamodel.data import (
    EntryData,
    EntryDataCategory,
    Query,
)
from nomad.datamodel.metainfo.annotations import (
    BrowserAnnotation,
    ELNAnnotation,
    ELNComponentEnum,
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
from pydantic import BaseModel, Field

from nomad_analysis.utils import (
    create_entry_with_api,
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


class ReferencedEntry(BaseModel):
    """
    A data model for referenced entry.
    """

    m_proxy_value: str = Field(description='The proxy value of the referenced entry.')
    name: str | None = Field(
        default=None, description='The name of the referenced entry.'
    )
    lab_id: str | None = Field(
        default=None, description='The lab_id of the referenced entry.'
    )


class JupyterAnalysisCategory(EntryDataCategory):
    """
    Category for analysis schemas using Jupyter notebooks.
    """

    m_def = Category(
        label='Analysis using Jupyter notebooks',
        categories=[EntryDataCategory],
    )


class JupyterAnalysis(Analysis, EntryData):
    """
    Base section for analysis that connects a Jupyter notebook to the entry. The
    notebook allows the user to run custom code for analysis.

    The section allows the user to:
    - Build queries to search and connect the input entries for the analysis.
    - Generate and connect a Jupyter notebook with pre-defined cell blocks.
    - Optionally, upload a Jupyter notebook from your local system and connect
      to the entry.

    The pre-defined cells act as a starting point and can be used to supply template
    code for the analysis. In order to extend the pre-defined cells in the notebook,
    extend this class and simply override the `write_predefined_cells` method to add
    your own pre-defined code cells. Make sure to add the `nomad-analysis-predefined`
    tag to the metadata of the code cells. This ensures cells are recognized as pre-
    defined cells by other methods. For example:

    ```
    class MyJupyterAnalysis(JupyterAnalysis):
        def write_predefined_cells(self, archive, logger):
            cells = super().write_predefined_cells(archive, logger)

            # add your own pre-defined cells
            source = [
                'import pprint\n',
                'pprint("Hello World!")\n',
            ]
            cells.append(
                nbf.v4.new_code_cell(
                    source=source, metadata={'tags': ['nomad-analysis-predefined']}
                )
            )
            # add more cells as needed
            # ...


            return cells
    ```
    """

    m_def = Section(
        categories=[JupyterAnalysisCategory],
        description="""
        Section for analysis using Jupyter notebooks.
        """,
        label='Jupyter Analysis',
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
                    'trigger_generate_notebook',
                    'trigger_reset_inputs',
                ],
            ),
        ),
    )
    method = Quantity(
        type=str,
        default='Generic',
    )
    trigger_generate_notebook = Quantity(
        type=bool,
        description="""
        Generates a Jupyter notebook and connects it with `notebook` quantity. If the
        notebook already exists, the cells containing `nomad-analysis-predefined` tag
        will be reset. All other cells will be preserved.
        """,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.ActionEditQuantity,
            label='Generate Notebook',
        ),
    )
    trigger_reset_inputs = Quantity(
        type=bool,
        description="""
        Removes the existing references in `inputs` sub-section and creates new
        references based on the `query_for_inputs` quantity.
        """,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.ActionEditQuantity,
            label='Reset Inputs',
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
        shape=['*'],
        description="""
        Search queries for connecting input entries to be used in the analysis.
        These queries are used to populates the `inputs` sub-section.
        """,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.QueryEditQuantity,
            props=dict(
                storeInArchive=True,
            ),
        ),
    )

    def resolve_entry_data(
        self,
        entry_id: str,
        upload_id: str,
        archive: 'EntryArchive',
        logger: 'BoundLogger',
    ) -> Union['EntryData', None]:
        """
        Tries to resolves the entry data for the given `entry_id` and `upload_id`.

        Args:
            entry_id (str): The entry_id of .
            upload_id (str): The upload_id of the referenced section.
            archive (EntryArchive): The archive containing the section.
            logger (BoundLogger): A structlog logger.

        Returns:
            Union[EntryData, None]: The resolved entry data or None.
        """
        from nomad.app.v1.models.models import User
        from nomad.app.v1.routers.uploads import get_upload_with_read_access
        from nomad.datamodel.context import ServerContext

        try:
            reference = SectionReference(
                reference=f'../uploads/{upload_id}/archive/{entry_id}#/data'
            )
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
            logger.warning(
                f'Could not resolve the entry with upload_id "{upload_id}" and '
                f'entry_id "{entry_id}".\n Encountered {e}.'
            )

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
            list[ReferencedEntry]: The list of `ReferencedEntry` containing metadata of
                the queried entries.
        """
        ref_list = []
        entries = []

        # extend the entries with the data from query_for_inputs
        if self.query_for_inputs:
            for query in self.query_for_inputs:
                if query.get('data') is not None:
                    entries.extend(query['data'])

        for entry in entries:
            resolved_entry = self.resolve_entry_data(
                entry['entry_id'],
                entry['upload_id'],
                archive,
                logger,
            )
            if resolved_entry is None:
                continue
            ref = ReferencedEntry(
                m_proxy_value=resolved_entry.m_proxy_value,
                name=resolved_entry.get('name'),
                lab_id=resolved_entry.get('lab_id'),
            )
            ref_list.append(ref)

        return ref_list

    def normalize_input_references(
        self,
        archive: 'EntryArchive',
        logger: 'BoundLogger',
    ):
        """
        Combines the existing input references with references based on the
        `query_for_inputs` quantity. Filters out duplicates based on m_proxy_value and
        lab_id. Sets the name of the input references. Returns without normalizing if
        the context is not a server context.
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

        if not isinstance(archive.m_context, ServerContext):
            return

        ref_list = []
        ref_list.extend(self.process_query_for_inputs(archive, logger))

        # add the existing input references
        for input_ref in self.inputs:
            if input_ref.reference is None:
                continue
            ref = ReferencedEntry(
                m_proxy_value=input_ref.reference.m_proxy_value,
                name=input_ref.reference.get('name'),
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
            if ref.lab_id and ref.lab_id in ref_hash_map.values():
                continue
            ref_hash_map[ref.m_proxy_value] = ref.lab_id
            filtered_ref_list.append(ref)

        # reset the inputs references
        self.inputs = []
        for ref in filtered_ref_list:
            self.inputs.append(SectionReference(reference=ref.m_proxy_value))
            if ref.name:
                self.inputs[-1].name = ref.name
            elif ref.lab_id:
                self.inputs[-1].lab_id = ref.lab_id

    def write_predefined_cells(
        self, archive: 'EntryArchive', logger: 'BoundLogger'
    ) -> list:
        """
        Writes the pre-defined Jupyter notebook cells.

        Args:
            archive (EntryArchive): The archive containing the section.
            logger (BoundLogger): A structlog logger.

        Returns:
            list: The list of pre-defined code cells.
        """
        user = 'Unknown user'
        if archive.metadata.main_author:
            user = archive.metadata.main_author.name
        notebook_heading = self.name
        if not notebook_heading:
            notebook_heading = archive.metadata.mainfile.split('.')[0].replace('_', ' ')

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
            f'>{notebook_heading}</h1>\n',
            '<p style="font-size: 1.25em; font-style: italic; padding: 5px 200px 30px 30px;"\n',  # noqa: E501
            f'>{user}</p>\n',
            '</div>\n',
            '\n',
            'This notebook has been generated by a NOMAD Analysis entry with the\n',
            f'definition path: `{self.m_def.qualified_name()}`.\n',
            '\n',
            'Running the following code cell loads the entry in the local Jupyter\n',
            'environment allowing you to update it based on your analysis. Once the\n',
            'entry has been modified, use `analysis.save()` method to pass on the\n',
            'changes back into NOMAD.\n',
        ]
        cells.append(
            nbf.v4.new_markdown_cell(
                source=source, metadata={'tags': ['nomad-analysis-predefined']}
            )
        )

        source = [
            'from nomad_analysis.utils import get_entry_data\n',
            '\n',
            f'analysis = get_entry_data(entry_id="{archive.entry_id}")\n',
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

    def generate_notebook(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        """
        Generates the notebook and saves it in the upload folder. If a notebook already
        exists, the cells containing `nomad-analysis-predefined` tag will be reset. All
        other cells and their outputs will be preserved.

        Args:
            archive (EntryArchive): The archive containing the section.
            logger (BoundLogger): A structlog logger.
        """
        file_name = (
            os.path.basename(archive.metadata.mainfile).rsplit('.archive.', 1)[0]
            + '.ipynb'
        )

        new_notebook = nbf.v4.new_notebook()

        # add the pre-defined cells
        new_notebook.cells.extend(self.write_predefined_cells(archive, logger))

        if archive.m_context.raw_path_exists(file_name):
            # add the existing cells
            with archive.m_context.raw_file(file_name, 'r') as nb_file:
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
            # add an empty cell
            new_notebook.cells.append(nbf.v4.new_code_cell())

        new_notebook['metadata']['trusted'] = True

        with archive.m_context.raw_file(file_name, 'w') as nb_file:
            nbf.write(new_notebook, nb_file)
        archive.m_context.process_updated_raw_file(file_name, allow_modify=True)

        self.notebook = file_name

    def save(self):
        """
        Uses the NOMAD API to update the entry with the current state. This method
        can be used to update the entry on the server from the client side.
        """
        create_entry_with_api(
            section=self,
            base_url=self.m_context.installation_url,
            upload_id=self.m_context.upload_id,
            file_name=self.m_parent.metadata.mainfile,
        )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger'):
        """
        Handles the behavior of action triggers and normalizes the input
        references.
        """
        if self.trigger_generate_notebook:
            self.generate_notebook(archive, logger)
            self.trigger_generate_notebook = False
        if self.trigger_reset_inputs:
            self.inputs = []
            self.trigger_reset_inputs = False
        self.normalize_input_references(archive, logger)

        # running super().normalize() at this point ensures the workflow section uses
        # filtered self.inputs
        super().normalize(archive, logger)


class XRDJupyterAnalysis(JupyterAnalysis, EntryData):
    """
    Extends `JupyterAnalysis` section to generate XRD specific Jupyter notebooks.
    """

    m_def = Section(
        label='XRD Jupyter Analysis',
        description="""
        Section for XRD analysis using Jupyter notebooks.
        """,
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
                    'trigger_generate_notebook',
                    'trigger_reset_inputs',
                ],
            ),
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
        Sets the method to `XRD` and normalizes the entry.
        """
        self.method = 'XRD'
        super().normalize(archive, logger)


# aliases
ELNGenericJupyterAnalysis = ELNJupyterAnalysis = JupyterAnalysis
ELNXRDJupyterAnalysis = XRDJupyterAnalysis

m_package.__init_metainfo__()
