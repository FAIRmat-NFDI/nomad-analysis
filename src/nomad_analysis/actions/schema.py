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
from nomad.datamodel.metainfo.annotations import (
    ELNAnnotation,
    ELNComponentEnum,
)
from nomad.metainfo import (
    Quantity,
    SchemaPackage,
    Section,
)

if TYPE_CHECKING:
    from nomad.datamodel import EntryArchive
    from structlog.stdlib import BoundLogger


m_package = SchemaPackage()


class Action(ArchiveSection):
    """
    Base class for actions that can be triggered from the ELN interface. Includes two
    action buttons: one for triggering the action and another for retrieving the
    status of the action using the action ID. Subclasses should implement the
    `start_action` method to define the specific action to be performed.
    """

    m_def = Section(description='Section for running NOMAD Actions.')
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
        Retrieves the status of the action using the action ID.
        """
        try:
            if not self.action_instance_id:
                raise ValueError('No action ID found.')
            status = manager.get_action_status(
                self.action_instance_id, archive.metadata.authors[0].user_id
            )
            self.action_status = status.name
        except Exception:
            logger.error('Failed to get action status.', exc_info=True)
        finally:
            self.trigger_get_action_status = False

    def stop_action(self, archive: 'EntryArchive', logger: 'BoundLogger'):
        """
        Stops the action using the action ID.
        """
        try:
            if not self.action_instance_id:
                raise ValueError('No action ID found.')
            manager.stop_action(
                self.action_instance_id, archive.metadata.authors[0].user_id
            )
        except Exception:
            logger.error('Failed to stop the action.', exc_info=True)
        finally:
            self.trigger_stop_action = False

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
