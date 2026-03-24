# Analysis with Jupyter Notebooks

This guide provides step-by-step instructions for creating and managing Jupyter notebook-based analyses in NOMAD using the `JupyterAnalysis` schema. It covers both the ELN interface and YAML-based approaches.

## Method 1: Using the ELN Interface

### Create a New Entry

- Navigate to your upload in NOMAD
- Click **Create Entry** and enter the name of your analysis (e.g., "XRD Phase Analysis")
- Select the **Built-in Schemas** option and select **Jupyter Analysis** from the dropdown
- Click **Create** to generate the entry

### Fill in Basic Information

| Field | Description |
|-------|-------------|
| **Name** | A descriptive name for your analysis |
| **Description** | Detailed description of the analysis purpose |
| **Lab ID** | Optional laboratory identifier |

### Select Input Data

You can search and connect multiple input entries to your analysis. To do this in the ELN:

- Find the `query_for_inputs` field
- Click the search icon to open the search interface
- Build a query to find your input data (e.g., filter by upload, entry type, etc.)
- Click OK to add the searched entries as inputs

The entries will be stored and appear in the `inputs` sub-section.

A new input can also be added manually by clicking the plus button in the `inputs` sub-section and filling in the reference path to the desired entry.


### Resetting Inputs

To clear and repopulate inputs from queries, click the **Reset Inputs** action button. All existing inputs will be removed and repopulated based on the search query in `query_for_inputs`.

### Generate the Notebook

A notebook can be uploaded manually and connected to the entry. For this, simply find the `notebook` quantity and upload a Jupyter notebook file.

You can also generate a notebook automatically by clicking the **Generate Notebook** action button. This will:

- Create a new `.ipynb` file in the same upload
- Pre-populate it with header cells and data loading code
- Link it with the `notebook` quantity

The name of the generated notebook will match your entry name.

!!! note
    If a notebook already exists with the same name, the generation will be skipped. Delete the existing notebook first if you want to regenerate it.

### Open and Run the Notebook

You can open the notebook in NOMAD's integrated JupyterHub (North).

- Click on right arrow button next to the `notebook` field
- From a list of NORTH tools, select the JupterHub by clicking on the "Launch" button under it

It will open in NOMAD's integrated JupyterHub (North) in a new tab with your notebook loaded. The directory structure in the JupyterHub will mirror your NOMAD upload structure, allowing you to easily access your data files and notebooks.

Now you can run the cells to load your data and perform your analysis.


## Method 2: Using YAML Files

`JupyterAnalysis` entries can also be created using YAML files. The support comes from NOMAD in general, where you can create entries by uploading YAML files with the appropriate structure.

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
the ELN interface.


## Learn More

- [Extend JupyterAnalysis Schema](extend_jupyter_analysis.md): Learn how to extend the `JupyterAnalysis` schema to add more fields, use specialized sub-section, and define the content for generated notebooks.
