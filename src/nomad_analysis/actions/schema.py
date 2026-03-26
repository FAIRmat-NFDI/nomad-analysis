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
from typing import (
    TYPE_CHECKING,
)

from nomad.actions import manager
from nomad.datamodel import ArchiveSection
from nomad.datamodel.data import EntryDataCategory
from nomad.datamodel.metainfo.annotations import (
    ELNAnnotation,
    ELNComponentEnum,
    QuantityDisplayAnnotation,
)
from nomad.metainfo import (
    Category,
    Quantity,
    SchemaPackage,
    Section,
)

if TYPE_CHECKING:
    from nomad.datamodel import EntryArchive
    from structlog.stdlib import BoundLogger


m_package = SchemaPackage()


class ActionCategory(EntryDataCategory):
    """
    A category for schemas that can be used to run NOMAD Actions.

    `EntryData` sections with this category will be put under the same group,
    **"Run NOMAD Actions from ELN"**,
    in the Create from Schema > Built-in schema dropdown menu.

    Example usage:

    ```python
    class MyActionELN(Action, EntryData):
        m_def = Section(
            description='Section for running my custom action.',
            categories=[ActionCategory],
        )
        ...
    ```
    """

    m_def = Category(
        label='Run NOMAD Actions from ELN',
        categories=[EntryDataCategory],
    )


class StartAction(ArchiveSection):
    """Section to trigger an action instance."""

    action_instance_id = Quantity(
        type=str,
        description='Instance ID of the action.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
        a_display=QuantityDisplayAnnotation(editable=False, visible=True),
    )
    trigger_start_action = Quantity(
        type=bool,
        default=False,
        description='Starts the action defined under `start_action` method.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.ActionEditQuantity, label='Start Action'
        ),
    )

    def start_action(self, archive, logger) -> str:
        """
        To be implemented by subclasses. Based on the data available in the ELN,
        use this method to prepare the input for the given action and trigger it using
        `nomad.actions.manager.start_action`.

        The method should return the same instance ID of the triggered action as
        returned by the `nomad.actions.manager.start_action` method.

        Example implementation:

        ```python
        from nomad.actions import manager

        def start_action(self, archive, logger) -> str:
            # Prepare input for the action
            action_input = MyActionInput(
                user_id=archive.metadata.authors[0].user_id,
                upload_id=archive.metadata.upload_id,
                # other necessary input data for the action
            )

            # Start the action using the NOMAD action manager
            instance_id = manager.start_action(
                action_id='nomad_example.actions.myaction:my_action',
                data=action_input,
            )

            return instance_id
        ```

        When using an implemented `start_action` method, condition it on the
        `trigger_start_action` quantity to ensure that the action is triggered when the
        quantity is set to True. And set the trigger quantity to False the method
        is executed to avoid retriggering the action on the next normalization.

        Returns:
            str: The instance ID of the triggered action.
        """
        raise NotImplementedError('Subclasses should implement this method.')

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger'):
        """
        Normalizes the action entry. If `trigger_start_action` is set to True, it calls
        the `start_action` method to execute the action and sets
        `trigger_get_action_status` to True to retrieve the action status. If
        `trigger_get_action_status` is set to True, it calls the `_get_action_status`
        method to update the `action_status`.

        Args:
            archive (Archive): A NOMAD archive.
            logger (Logger): A structured logger.
        """
        if self.trigger_start_action:
            try:
                self.action_instance_id = self.start_action(archive, logger)
            except Exception:
                logger.warning('Failed to start the action.', exc_info=True)
            finally:
                self.trigger_start_action = False

        super().normalize(archive, logger)


class StopAction(ArchiveSection):
    """
    Section to stop a running action instance. Comes with a method `stop_action` that
    takes in action instance ID and schedules a cancellation of the action. It can used
    in the `normalize` method of child sections and set to be triggered using the
    `trigger_stop_action` quantity.

    Example usage:
    ```python
    class MyActionELN(..., StopAction):
        # Assuming quantity `action_instance_id` is already a property of the section.
        # Can be defined in the section or inherited from the parent section.

        def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger'):
            super().normalize(archive, logger)

            # Other normalization code...

            if self.trigger_stop_action:
                self.stop_action(self.action_instance_id, archive, logger)
    ```
    """

    trigger_stop_action = Quantity(
        type=bool,
        default=False,
        description='Schedule a cancellation of the action associated with the '
        'action instance ID.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.ActionEditQuantity, label='Stop Action'
        ),
    )

    def stop_action(
        self, action_instance_id: str, archive: 'EntryArchive', logger: 'BoundLogger'
    ):
        """
        Schedule a cancellation of the action associated with the action instance ID.
        """
        try:
            if not action_instance_id:
                raise ValueError('No action ID found.')
            manager.stop_action(action_instance_id, archive.metadata.authors[0].user_id)
            logger.info(
                f'Action with instance ID {action_instance_id} has been '
                'scheduled for stopping.'
            )
        except Exception:
            logger.warning('Failed to stop the action.', exc_info=True)
        finally:
            self.trigger_stop_action = False


class ActionStatus(ArchiveSection):
    """
    Section to save and fetch the status of an action instance. Comes with a method
    `get_action_status` that takes in action instance ID and gets the status. It can
    used in the `normalize` method of child sections and set to be triggered using
    the `trigger_get_action_status` quantity.

    Example usage:

    ```python
    class MySection(..., ActionStatus):
        # Assuming quantity `action_instance_id` is already a property of the section.
        # Can be defined in the section or inherited from the parent section.

        def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger'):
            super().normalize(archive, logger)

            # Other normalization code...

            if self.trigger_get_action_status:
                self.get_action_status(self.action_instance_id, archive, logger)
    ```
    """

    action_status = Quantity(
        type=str,
        description='Status of the action instance.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
        a_display=QuantityDisplayAnnotation(editable=False, visible=True),
    )
    trigger_get_action_status = Quantity(
        type=bool,
        default=False,
        description='Retrieves the status of the action using action ID.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.ActionEditQuantity, label='Get Action Status'
        ),
    )

    def get_action_status(
        self, action_instance_id: str, archive: 'EntryArchive', logger: 'BoundLogger'
    ):
        """
        Retrieves the status of the action using the `action_instance_id`.
        """
        status = None
        try:
            if not action_instance_id:
                raise ValueError('No action instance ID found.')
            status = manager.get_action_status(
                action_instance_id, archive.metadata.authors[0].user_id
            )
        except Exception:
            logger.warning('Failed to get action status.', exc_info=True)
        finally:
            if status is not None:
                self.action_status = status.name
            self.trigger_get_action_status = False



class Action(ArchiveSection):
    """
    Base class for triggering actions from the ELN interface.
    Subclasses should implement the `start_action` method.
    """

    m_def = Section(description='Section for handling NOMAD Actions.')
    action_instance_id = Quantity(
        type=str,
        description='The instance ID of the last triggered action.',
    )
    action_status = Quantity(
        type=str,
        description='The status of the action derived using the action instance ID.',
    )
    trigger_start_action = Quantity(
        type=bool,
        description='Starts the action defined under `start_action` method.',
        default=False,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.ActionEditQuantity,
            label='Run Action',
        ),
    )
    trigger_get_action_status = Quantity(
        type=bool,
        description='Retrieves the status of the action using the action instance ID.',
        default=False,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.ActionEditQuantity,
            label='Get Action Status',
        ),
    )
    trigger_stop_action = Quantity(
        type=bool,
        description='Stops the action using the action instance ID.',
        default=False,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.ActionEditQuantity,
            label='Stop Action',
        ),
    )

    def start_action(self, archive, logger) -> str:
        """
        To be implemented by subclasses. Based on the data available in the ELN,
        use this method to prepare the input for the given action and trigger it using
        `nomad.actions.manager.start_action`. The method should return the same instance
        ID of the triggered action as returned by the
        `nomad.actions.manager.start_action` method.

        Returns:
            str: The instance ID of the triggered action.
        """
        raise NotImplementedError('Subclasses should implement this method.')

    def get_action_status(self, archive: 'EntryArchive', logger: 'BoundLogger'):
        """
        Retrieves the status of the action using the action instance ID.
        """
        try:
            if self.action_status == 'COMPLETED':
                return
            if not self.action_instance_id:
                raise ValueError('Action instance ID not provided.')
            status = manager.get_action_status(
                self.action_instance_id, archive.metadata.authors[0].user_id
            )
            self.action_status = status.name
        except Exception:
            logger.error(
                'Failed to get status for action instance ID '
                f'"{self.action_instance_id}".',
                exc_info=True,
            )
        finally:
            self.trigger_get_action_status = False

    def stop_action(self, archive: 'EntryArchive', logger: 'BoundLogger'):
        """
        Stops the action using the action instance ID.
        """
        try:
            if not self.action_instance_id:
                raise ValueError('Action instance ID not provided.')
            manager.stop_action(
                self.action_instance_id, archive.metadata.authors[0].user_id
            )
        except Exception:
            logger.error(
                'Failed to stop the action with instance ID '
                f'"{self.action_instance_id}".',
                exc_info=True,
            )
        finally:
            self.trigger_stop_action = False

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger'):
        """
        Handles the behavior of the trigger buttons:

        - If `trigger_start_action` is set to True, it calls the `start_action`
        method to execute the action and sets `trigger_get_action_status` to True to
        retrieve the action status.

        - If `trigger_stop_action` is set to True, it calls the `stop_action` method
        to stop the action and sets `trigger_get_action_status` to True to update
        the action status.

        - If `trigger_get_action_status` is set to True, it calls the
        `get_action_status` method to update the `action_status`.

        The `action_status` field can have the following values:

        | Status       | Description                              |
        |--------------|------------------------------------------|
        | `RUNNING`    | Action is currently executing            |
        | `COMPLETED`  | Action finished successfully             |
        | `FAILED`     | Action encountered an error              |
        | `CANCELLED`  | Action was stopped by user               |
        | `TERMINATED` | Action was terminated by system or admin |

        The `start_action` method should be implemented by subclasses.
        It should prepare the input for the specific action and trigger it using the
        `nomad.actions.manager.start_action` method. The `start_action` method should
        return the same instance ID of the triggered as returned by the
        `nomad.actions.manager.start_action` method.
        """
        if self.action_status == 'RUNNING':
            # work with the latest status if last known status is RUNNING
            self.get_action_status(archive, logger)

        if self.trigger_stop_action:
            if self.action_status != 'RUNNING':
                self.trigger_stop_action = False
                logger.error(
                    'The action is not running. Cannot stop an action that '
                    'is not running.'
                )
            else:
                self.stop_action(archive, logger)
                self.trigger_get_action_status = True

        if self.trigger_start_action:
            if self.action_status == 'RUNNING':
                self.trigger_start_action = False
                logger.error(
                    'The action is already running. Please wait for it to '
                    'complete before running the action again.'
                )
            else:
                try:
                    self.action_instance_id = self.start_action(archive, logger)
                    self.trigger_get_action_status = True
                except Exception:
                    logger.error('Failed to start the action.', exc_info=True)
                finally:
                    self.trigger_start_action = False

        if self.trigger_get_action_status:
            self.get_action_status(archive, logger)

        super().normalize(archive, logger)


m_package.__init_metainfo__()
