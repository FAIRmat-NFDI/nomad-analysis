# Entry points

The NOMAD Analysis plugin provides the following [entry points](https://nomad-lab.eu/prod/v1/docs/reference/glossary.html#plugin-entry-point) that can
be included in your [Oasis](https://nomad-lab.eu/prod/v1/docs/reference/glossary.html#deployment-nomad-oasis):

- `nomad_analysis.general:schema_entry_point`: Provides low-level schemas that can be extended for defining analysis workflows.

- `nomad_analysis.jupyter:schema_entry_point`: Provides schemas for managing Jupyter notebook-based analyses.

- `nomad_analysis.actions:schema_entry_point`: Provides schemas for defining and managing NOMAD Actions from the ELN interface.


You can configure which entry points to include in your Oasis deployment by
updating the `nomad.yaml` of your distribution, as described in the [Configure
the Plugin](../how_to/install_and_add_to_your_oasis.md#configure-the-plugin-optional) section of the installation guide.
By default, all entry points from the plugin are included.
