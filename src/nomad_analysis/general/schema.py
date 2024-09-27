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

from nomad.datamodel.metainfo.basesections import (
    ActivityStep,
    Entity,
)
from nomad.metainfo import (
    SchemaPackage,
    SubSection,
)

m_package = SchemaPackage()


class AnalysisResult(Entity):
    """
    An abstract class representing the results of an analysis. The data model is
    intended to be extended for specific analysis methods.
    """


class AnalysisStep(ActivityStep):
    """
    An abstract class representing the step of an analysis. It contains the results of
    the analysis step. The data model is intended to be extended for specific analysis
    methods.
    """

    results = SubSection(
        section_def=AnalysisResult,
        repeats=True,
    )


m_package.__init_metainfo__()
