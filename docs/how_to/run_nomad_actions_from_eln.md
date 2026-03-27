# Run NOMAD Actions from the ELN

[NOMAD Actions][ext_href_1] allow to define executable workflows that can run on
specialized workers. This guide explains how to use the `Action` schema from
`nomad_analysis.actions.schema` to trigger, monitor, and stop NOMAD Actions
directly from the ELN interface.

If you would like to set up customizable analysis workflows that run in Jupyter
notebooks instead, check out the [Analysis with Jupyter Notebooks][int_href_1]
guide.

!!! tip "When to use Actions over Jupyter Notebooks?"
    - Running standarized analysis workflows that require fixed user input and generates a fixed output, without any custom code
    - Offloading heavy computations to dedicated workers
    - Integrate with external services and APIs as part of your analysis

## Overview

The `Action` base schema from `nomad_analysis.actions.schema` module is a
reusable schema for integrating Actions with NOMAD's ELN interface.
It provides a boilerplate NOMAD section equipped with buttons to:

- **Start Action**: Trigger a workflow from the ELN
- **Get Status**: Check the current status of a running action
- **Stop Action**: Cancel a running action

The schema is designed to be extended for different types of analysis workflows. By implementing the `start_action` method, you can define custom logic to prepare inputs and trigger any registered NOMAD Action.

!!! hint
    Read more about registration of Actions in the
    [Action Entry Point][ext_href_2] guide.

## Create a custom Action Schema

Extend the `Action` class and implement the `start_action` method:

```python
from nomad.actions import manager
from nomad.metainfo import Quantity, Section
from nomad_analysis.actions.schema import Action

# import your custom action input schema if needed
from .models import MyAnalysisActionInput


class MyAnalysisAction(Action):
    """Custom action for running analysis workflows."""

    # Add custom quantities for your action inputs
    input_parameter = Quantity(
        type=str,
        description='Input parameter for the analysis.',
        a_eln={'component': 'StringEditQuantity'},
    )

    def start_action(self, archive, logger) -> str:
        """
        Triggers the analysis action.

        Returns:
            str: The instance ID of the triggered action.
        """
        # Prepare input for the action
        action_input = MyActionInput(
            user_id=archive.metadata.authors[0].user_id,
            upload_id=archive.metadata.upload_id,
            parameter=self.input_parameter,
        )

        # Start the action using the NOMAD action manager
        instance_id = manager.start_action(
            action_id='nomad_example.actions.myaction:my_action',
            data=action_input,
        )

        return instance_id
```

## Use in an ELN Entry

The custom action section can be added as a sub-section to an ELN schema:

```python
from nomad.datamodel.data import EntryData
from nomad.metainfo import SubSection


class MyAnalysisELN(EntryData):
    """ELN entry with action trigger capability."""

    action = SubSection(section_def=MyAnalysisAction)
```

Or it can be defined as a standalone ELN entry:

```python
from nomad.datamodel.data import EntryData

class MyAnalysisELN(MyAnalysisAction, EntryData):
    """ELN entry for my specific analysis workflow."""
```

## Troubleshooting

If something isn't working as expected, there's a good chance you will find
useful information in the entry processing logs. You can access these logs from the ELN interface. Some common issues and tips:

- **Action Won't Start**: Check whether an action is already running. Only one action can run at a time per entry. Either stop the running action or wait for it to complete before starting a new one.
- **Status Not Updating**: The status does not auto-refresh. Try clicking "Get Action Status" to manually retrieve the latest status. If the status does not update, check the logs for errors.
- **Action Fails Immediately**: Check the logs for error messages. Common issues include incorrect action input preparation or problems with the action worker.


## Related Documentation

- [Define robust analysis pipelines with NOMAD Actions][ext_href_1]: Automate your analysis workflows with NOMAD Actions.
- [Analysis with Jupyter Notebooks][int_href_1]: Learn how to use the generated notebooks for your analysis workflow.

<!-- - [Schema Reference](../reference/schema_reference.md) -->


[int_href_1]: ./analysis_with_jupyter_notebooks.md#analysis-with-jupyter-notebooks

[ext_href_1]: https://nomad-lab.eu/prod/v1/docs/howto/plugins/types/actions.html
[ext_href_2]: https://nomad-lab.eu/prod/v1/docs/howto/plugins/types/actions.html#action-entry-point
