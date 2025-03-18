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

import os.path

import pytest
from nomad.client import normalize_all, parse
from nomad.datamodel import all_metainfo_packages

test_data_dir = os.path.join(os.path.dirname(__file__), 'data')

all_metainfo_packages()


@pytest.mark.parametrize(
    'test_file',
    [
        os.path.join(test_data_dir, 'ELNGenericJupyterAnalysis.archive.yaml'),
        os.path.join(test_data_dir, 'ELNJupyterAnalysis.archive.yaml'),
    ],
)
def test_jupyter_analysis_generic_schema(
    test_file, capture_error_from_logger, clean_up
):
    entry_archive = parse(test_file)[0]
    normalize_all(entry_archive)

    assert entry_archive.data.analysis_type == 'Generic'


@pytest.mark.parametrize(
    'test_file',
    [os.path.join(test_data_dir, 'ELNXRDJupyterAnalysis.archive.yaml')],
)
def test_jupyter_analysis_xrd_schema(test_file, capture_error_from_logger, clean_up):
    entry_archive = parse(test_file)[0]
    normalize_all(entry_archive)

    assert entry_archive.data.analysis_type == 'XRD'
