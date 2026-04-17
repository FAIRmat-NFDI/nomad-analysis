# Extend JupyterAnalysis Schema

This guide shows how to create custom analysis schemas by extending the base
`JupyterAnalysis` schema.

!!! note "Prerequisites"
    It assumes that you already have a NOMAD plugin that adds customizations to your NOMAD installation. More details on creating a plugin can be found in the [Plugin Development](https://nomad-lab.eu/prod/v1/docs/howto/plugins/plugins.html) guide (look at schema packages there).

## Why Extend JupyterAnalysis?

Extending `JupyterAnalysis` allows you to:

- Define quantities and sub-sections specific to your analysis domain
- Customize pre-defined notebook cells
- Customize the validation and normalization logic of the analysis schema

### Add custom quantities and sub-sections

```python
import nbformat as nbf
from nomad.datamodel.data import EntryData
from nomad.datamodel.metainfo.basesections import AnalysisStep
from nomad.datamodel.metainfo.plot import PlotSection
from nomad.metainfo import Quantity, Section

from nomad_analysis.jupyter.schema import JupyterAnalysis


class MyCustomAnalysisStep(AnalysisStep, PlotSection):
    """
    For illustrative purposes, this section includes a plotting section on top
    of the base AnalysisStep. In a real-world problem, this would have to be
    filled further.
    """


class MyCustomAnalysis(JupyterAnalysis, EntryData):
    """
    Custom analysis schema for my specific use case.
    """

    m_def = Section(
        label='My Custom Analysis',
        description='Analysis schema for my domain-specific workflow.',
    )

    # Add custom quantities
    custom_parameter = Quantity(
        type=float,
        description='A custom parameter for my analysis',
        a_eln=ELNAnnotation(
            component='NumberEditQuantity',
        ),
    )

    # Add custom steps
    steps = SubSection(section_def=MyCustomAnalysisStep, repeats=True)
```

### Customize pre-defined notebook cells

When a notebook is generated from a Jupyter Analysis entry, it contains data loading code as part of the header. To add more pre-defined cells, implement the `write_predefined_cells` method, which defines the code cells added to generated notebooks:

```python
class MyCustomAnalysis(JupyterAnalysis, EntryData):
    # ... m_def and quantities ...

    def write_predefined_cells(self, archive, logger):
        """
        Add custom pre-defined cells to the generated notebook.
        """
        cells = []

        # Add analysis function cell
        analysis_source = [
            'def process_data(data):\n',
            '    # Your processing logic here\n',
        ]
        cells.append(
            nbf.v4.new_code_cell(
                source=analysis_source,
                metadata={'tags': ['nomad-analysis-predefined']},
            )
        )

        # Add a markdown cell with instructions
        instructions = [
            '## Analysis Instructions\n',
            '\n',
            '1. Run the cells above to load data\n',
            '2. Use `process_data()` to transform your inputs\n',
            '3. Add steps to `analysis.steps`\n',
            '4. Run `analysis.save()` to persist results\n',
        ]
        cells.append(
            nbf.v4.new_markdown_cell(
                source=instructions,
                metadata={'tags': ['nomad-analysis-predefined']},
            )
        )

        return cells
```

!!! tip "Newlines in Code Cells"
    When defining the source code for pre-defined cells, make sure to include newline characters (`\n`) at the end of each line to ensure proper formatting in the generated notebook.

!!! tip "Cell Metadata Tags"
    Always include `'nomad-analysis-predefined'` in cell metadata tags. This allows the schema to identify and manage these cells differently.

### Customize normalization logic

Everytime an analysis entry is created or updated, the `normalize()` method is called to validate and normalize the data. You can override this method to add custom validation rules or set default values:

```python
def normalize(self, archive, logger):
    """
    Custom normalization logic.
    """
    # Set default method
    self.method = 'My Custom Method'

    # Custom validation
    if self.custom_parameter and self.custom_parameter < 0:
        logger.warning('custom_parameter should be positive')

    # Call parent normalize
    super().normalize(archive, logger)
```

!!! tip "Error Handling"
    Even though NOMAD processing does not crash on exceptions in `normalize()`, it's good practice to handle potential errors gracefully. Use `try/except` blocks around code that might raise exceptions and utilize the `logger` to log warnings or errors.

## Learn More

- [Analysis with Jupyter Notebooks](./analysis_with_jupyter_notebooks.md#analysis-with-jupyter-notebooks): Learn how to use the generated notebooks for your analysis workflow.
- [Run NOMAD Actions from ELN](./run_nomad_actions_from_eln.md): Trigger complex analysis workflows directly from your ELN entries using NOMAD Actions.
