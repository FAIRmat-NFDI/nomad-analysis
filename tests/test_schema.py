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

test_archives_dir = os.path.join(os.path.dirname(__file__), 'data')
test_archives_path = []
for path in os.listdir(test_archives_dir):
    if path.endswith('.archive.yaml'):
        test_archives_path.append(os.path.join(os.path.dirname(__file__), 'data', path))


@pytest.mark.parametrize('test_file', test_archives_path)
def test_schema(test_file, capture_error_from_logger, clean_up):
    entry_archive = parse(test_file)[0]
    normalize_all(entry_archive)

    assert entry_archive.data.analysis_type == 'Generic'
    # TODO: Add tests for generated jupyter notebook
