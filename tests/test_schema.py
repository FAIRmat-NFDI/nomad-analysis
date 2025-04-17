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

import nbformat as nbf
import pytest
from nomad.client import normalize_all, parse
from nomad.datamodel import all_metainfo_packages

test_data_dir = os.path.join(os.path.dirname(__file__), 'data')
log_levels = ['error', 'critical']

all_metainfo_packages()


@pytest.mark.parametrize(
    ('test_file', 'caplog'),
    [(os.path.join(test_data_dir, 'test_jupyter_analysis.archive.yaml'), log_levels)],
)
def test_jupyter_analysis_schema(test_file, caplog, clean_up):
    """
    Test the Jupyter analysis schema.
    """
    entry_archive = parse(test_file)[0]
    normalize_all(entry_archive)

    assert entry_archive.data.method == 'Generic'

    # open the notebook and test the pre-defined cells blocks
    with entry_archive.m_context.raw_file(entry_archive.data.notebook, 'r') as nb_file:
        notebook = nbf.read(nb_file, as_version=nbf.NO_CONVERT)
    total_cells = 3
    assert len(notebook.cells) == total_cells
    assert notebook.cells[1].source == (
        'from nomad_analysis.utils import get_entry_data\n\n'
        'analysis = get_entry_data(entry_id="None")\n'
    )


@pytest.mark.parametrize(
    ('test_file', 'caplog'),
    [
        (
            os.path.join(
                test_data_dir, 'test_extended_xrd_jupyter_analysis.archive.yaml'
            ),
            log_levels,
        )
    ],
)
def test_jupyter_analysis_xrd_schema(test_file, caplog, clean_up):
    """
    Test the Jupyter analysis schema for XRD.
    """
    entry_archive = parse(test_file)[0]
    normalize_all(entry_archive)

    assert entry_archive.data.method == 'XRD'

    # open the notebook and test the extended pre-defined cells blocks
    with entry_archive.m_context.raw_file(entry_archive.data.notebook, 'r') as nb_file:
        notebook = nbf.read(nb_file, as_version=nbf.NO_CONVERT)
    total_cells = 5
    assert len(notebook.cells) == total_cells
    assert notebook.cells[3].source == 'xrd_voila_analysis(analysis.data.inputs)\n'


@pytest.mark.parametrize(
    ('test_file', 'caplog'),
    [
        (
            os.path.join(test_data_dir, 'test_aliased_jupyter_analysis.archive.yaml'),
            log_levels,
        )
    ],
)
def test_aliasing(test_file, caplog):
    """
    Test the Jupyter analysis schema for aliasing.
    """
    entry_archive = parse(test_file)[0]
    normalize_all(entry_archive)
    assert entry_archive.data.method == 'Generic'
