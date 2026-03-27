# Analysis with Jupyter Notebooks

This guide provides step-by-step instructions for creating and managing Jupyter notebook-based analyses in NOMAD using the `JupyterAnalysis` schema. It covers both the ELN interface and YAML-based approaches.

## Why use Jupyter Analysis?

Jupyter notebooks are a powerful tool for interactive data analysis, combining
code, visualizations, and documentation in a single document. The
Jupyter Analysis schema leverages this capability to provide a structured
framework for performing semi-automated analysis workflows directly connected
to your research data.

With Jupyter Analysis entries, you can connect entries stored in
NOMAD as inputs, load them into your notebook environment, and perform custom
analysis using Python. The results can then be saved back to NOMAD, ensuring
that your analysis outputs are properly linked to the original data and remain
part of the reproducible research record. This approach also makes it easy to
share your complete analysis workflow—including code, data references, and
results—with collaborators.

## Method 1: Using the ELN Interface

### Create a new Jupyter Analysis Entry

- Navigate to your upload in NOMAD
- Click **Create Entry** and enter the name of your analysis (e.g., "XRD Phase Analysis")
- Select the **Built-in Schemas** option and select **Jupyter Analysis** from the dropdown menu
- Click **Create** to generate the entry

### Fill in Basic Information

| Field | Description |
|-------|-------------|
| **Name** | A descriptive name for your analysis |
| **Description** | Detailed description of the analysis purpose |
| **Lab ID** | Optional laboratory identifier |

### Select Input Data

Existing NOMAD entries can be added as input to your analysis as `Reference`s.
To do this, go to the `inputs` field and click on the plus button to add a new
sub-section. Inside the sub-section, fill in the `reference` quantity with path to the desired entry and save the analysis entry.

If you want to add several inputs, you can also use a **query-powered approach** to search and reference multiple entries at once. To do this:

- Go to the `query_for_inputs` field
- Click the search icon to open the search interface
- Build a query to find your input data (e.g., filter by upload, entry type, etc.)
- Click OK to add the searched entries as inputs

Each searched entry will be processed as one input and all of them will be added under the `inputs` field.

!!! hint
    If you have mistakenly added a lot of inputs based on a broad query, use the **Reset Inputs** action button to start afresh. Set the more specific query and click the button. All existing inputs will be removed and repopulated based on the new query.

### Generate the Notebook

A notebook can be uploaded manually and connected to the entry. For this, simply find the `notebook` quantity and upload a Jupyter notebook file.

You can also generate a notebook automatically by clicking the **Generate Notebook** action button. This will:

- Create a new `.ipynb` file in the same upload
- Pre-populate it with header cells and data loading code
- Link it with the `notebook` quantity

The name of the generated notebook will match your entry name. It contains a header with the analysis name and a pre-defined code cell that loads the analysis entry and its inputs:

```python
from nomad_analysis.utils import get_entry_data

analysis = get_entry_data(entry_id=<NOMAD_ANALYSIS_ENTRY_ID>)
```

Inputs can be accessed through the `analysis.inputs` attribute, which contains references to the input entries you defined in the ELN interface.

!!! warning
    Different notebooks cannot share the same name. If you encounter issues trying to generate a new notebook, check for name collisions first. Either modify or delete the existing notebook depending on your needs.

### Open and Run the Notebook

You can open the notebook in NOMAD's integrated JupyterHub (North).

- Click on right arrow button next to the `notebook` field
- From a list of NORTH tools, select the JupterHub by clicking on the "Launch" button under it

NOMAD's integrated JupyterHub (North) will automatically open in a new tab with your notebook loaded. The directory structure in the JupyterHub will mirror your NOMAD upload structure, allowing you to easily access your data files and notebooks.

Now you can run the cells to load your data and perform your analysis.

During the analysis, you can save the steps and results by writing them into
the `analysis.steps` and `analysis.outputs` fields respectively. To save the
entry back to NOMAD, simply call `analysis.save()` at the end of your notebook.
This will update the entry with your analysis results and ensure that
everything is properly linked and stored in NOMAD.


## Method 2: Using YAML Files

Jupyter Analysis entries can also be created using YAML files. The support
comes from NOMAD in general, where you can create entries by uploading YAML
files with the appropriate structure.

Create a file named `my_analysis.archive.yaml` and upload it to your NOMAD upload:

```yaml
data:
  m_def: nomad_analysis.jupyter.schema.JupyterAnalysis
  name: XRD Phase Analysis
  description: |
    Analysis of XRD patterns to identify crystalline phases
    in the synthesized samples.

  # Optional: Pre-define input references
  inputs:
    - reference: '../uploads/UPLOAD_ID/archive/ENTRY_ID_1#/data'
      name: Sample A - XRD Pattern
    - reference: '../uploads/UPLOAD_ID/archive/ENTRY_ID_2#/data'
      name: Sample B - XRD Pattern
```

After uploading, trigger notebook generation and other functionality through
the ELN interface (see above).


## Learn More

- [Extend JupyterAnalysis Schema](extend_jupyter_analysis.md): Learn how to
extend the `JupyterAnalysis` schema to add more fields, use specialized
sub-section, and define the content for generated notebooks.
- [Run NOMAD Actions from ELN](run_nomad_actions_from_eln.md): Trigger complex analysis workflows directly from your ELN entries using NOMAD Actions.