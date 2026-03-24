# Overview

This section provides an overview of the schemas defined in the NOMAD Analysis plugin:

- [**General Analysis Schema**](general.md): A collection of low-level schemas with minimal fields that can be used as building blocks for defining more complex schemas. They are intended to be extended and customized for specific analysis use cases.
- [**Jupyter Analysis Schema**](jupyter.md): A collection of schemas designed for analyses that involve Jupyter notebooks. It includes fields for notebook content, input references, and metadata to facilitate the integration of Jupyter notebooks with NOMAD's ELN interface.
- [**Action Schema**](actions.md): This schema serves as a base for defining NOMAD Actions that can be triggered from the ELN. It provides a boilerplate structure for integrating with the ELN interface, allowing users to start, monitor, and stop actions directly from their ELN entries.

!!! info "Metainfo Browser"
    The **NOMAD Metainfo Browser** allows users to explore all available schemas, including their sections, values, and references, in a detailed and interactive manner. It can be accessed through the *Analyze* tab in any NOMAD instance. To explore the schemas specific to the NOMAD Analysis plugin, you can visit the [Metainfo Browser on the Example Oasis](https://nomad-lab.eu/prod/v1/oasis/gui/analyze/metainfo/nomad_analysis) and review all the details of the plugin's structures and components.