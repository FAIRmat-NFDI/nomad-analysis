#
# Copyright The NOMAD Authors.
#
# This file is part of NOMAD.
# See https://nomad-lab.eu for further info.
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

"""
Utility functions for the analysis plugin.
"""

import importlib
import inspect
import json
from typing import TYPE_CHECKING, Any

import requests
from nomad.client import ArchiveQuery
from nomad.client.api import Auth
from nomad.config import config
from nomad.datamodel import EntryArchive, EntryData

if TYPE_CHECKING:
    from nomad.datamodel.data import MSection


def category(category_name: str = None) -> callable:
    """
    A decorator which adds category attribute to a function.

    Args:
        category (str): Category of the function.
    """

    def decorator(func):
        if category_name is not None:
            func.category = category_name
        return func

    return decorator


def get_function_source(
    func: callable = None, category_name: str = None, module: object = None
) -> list:
    """
    Gets the source code of function (or functions) based on name or category.
    It looks up for the function in the specified module.

    Args:
        func (callable): Singular function whose source code is to be returned.
        category (str): Category of the functions.
        module (str): Module which will be searched.
            Default is `nomad_analysis.analysis_source`.

    Returns:
        list: List of source code of the functions.
    """
    func_sources = []
    if category_name is None and func is not None:
        func_sources.append(inspect.getsource(func))
    if category_name is not None and func is None:
        if module is None:
            module = importlib.import_module('nomad_analysis.analysis_source')
        for _, obj in inspect.getmembers(module):
            if (
                inspect.isfunction(obj)
                and hasattr(obj, 'category')
                and obj.category == category_name
            ):
                func_source = ''
                source_lines = inspect.getsourcelines(obj)[0]
                for source_line in source_lines:
                    # ignoring category decorator
                    if source_line.startswith('@category'):
                        continue
                    func_source += source_line
                func_sources.append(func_source)
    return func_sources


def list_to_string(list_instance: list) -> str:
    """
    Converts a list to a string.

    Args:
        list_instance (list): List to be converted.

    Returns:
        str: String representation of the list.
    """
    string = ''
    for item in list_instance:
        string += item + '\n'
    return string


def get_entry_data(
    entry_id: str,
    url: str = config.client.url,
    username: str = config.client.user,
    password: str = config.client.password,
) -> EntryData:
    """
    Gets the data section of an entry archive using the NOMAD API.

    Args:
        entry_id (str): Entry ID of the analysis ELN.
        url (str): URL of the NOMAD server.

    Returns:
        EntryArchive: Entry archive of the analysis entry.
    """

    entry_list = []
    try:
        a_query = ArchiveQuery(
            query={
                'entry_id:any': [entry_id],
            },
            required='*',
            url=url,
            username=username,
            password=password,
        )
        entry_list.extend(a_query.download(1))
    except Exception as e:
        print(f'Encountered error: {e}')

    if not entry_list:
        print(
            f'Entry not found for entry_id: "{entry_id}", url: "{url}", and user: '
            f'"{username}".'
        )
        return None

    return entry_list[0].data


def get_reference(upload_id: str, entry_id: str, archive_path: str = 'data') -> str:
    """
    Returns the proxy value for referencing a section of an entry.

    Args:
        upload_id (str): Upload ID of the upload in which the entry resides.
        entry_id (str): Entry ID of the entry.
        archive_path (str): Path in the entry where the section is located.
            Defaults to 'data'.

    Returns:
        str: Proxy value of the form
            '../uploads/{upload_id}/archive/{entry_id}#/{archive_path}'
    """
    return f'../uploads/{upload_id}/archive/{entry_id}#/{archive_path}'


def create_entry_with_api(
    section: 'MSection',
    base_url: str,
    upload_id: str,
    file_name: str,
    path: str = '',
    **params,
) -> str:
    """
    Uses the NOMAD API endpoint `/uploads/{upload_id}/raw/{path}` to create an entry
    for the given NOMAD section. If an entry already exists with the same name, it
    will be overwritten. Returns the proxy value for referencing the entry.

    Args:
        section (MSection): The entry data sections to be used for entry creation.
        base_url (str): Base URL of the NOMAD installation.
        upload_id (str): Upload ID of the upload in which the entry needs to be created.
        file_name (str): Name of the file to be created in the entry.
        path (str, Optional): Path in the NOMAD upload where the entry will be created.
        params (dict): Additional parameters for the request.

    Returns:
        str: proxy value of the form '../uploads/{upload_id}/archive/{entry_id}#/data'
    """
    endpoint = base_url + f'/uploads/{upload_id}/raw/{path}'

    params['file_name'] = file_name
    if 'wait_for_processing' not in params:
        params['wait_for_processing'] = True
    if 'overwrite_if_exists' not in params:
        params['overwrite_if_exists'] = True

    if not isinstance(section, EntryArchive):
        json_dict = {
            'data': section.m_to_dict(with_root_def=True),
        }
    else:
        json_dict = section.m_to_dict()

    response = put_nomad_request(url=endpoint, json_dict=json_dict, params=params)

    reference = get_reference(
        upload_id=response['processing']['entry']['upload_id'],
        entry_id=response['processing']['entry']['entry_id'],
    )

    return reference


def put_nomad_request(
    url: str,
    data: Any = None,
    json_dict: dict = None,
    params: dict = None,
    timeout: int = None,
) -> json:
    """
    Sends a put request to the NOMAD API.

    Args:
        url (str): Endpoint of the API.
        data (Any, optional): Dictionary, list of tuples, bytes, or file-like object to
            send in the body of the `Request`.
        json_dict (dict, optional): A JSON serializable Python object to send in the
            body of the `Request`.
        params (dict, optional): Parameters for the request.
        timeout (int, optional): Timeout for the request in seconds.

    Returns:
        json: Response from the API in JSON serializable Python object.
    """

    headers = {**Auth().headers()}

    print(f'Sending post request @ {url}')

    response = requests.put(
        url,
        headers=headers,
        json=json_dict,
        params=params,
        data=data,
        timeout=timeout,
    )

    if not response.ok:
        raise ValueError(f'Unexpected response {response.json()}')

    return response.json()
