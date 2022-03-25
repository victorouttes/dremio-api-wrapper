import logging
import sys
import time
from urllib.parse import quote

import requests

from dremio.exceptions import DremioException

logging.basicConfig(stream=sys.stdout, level=logging.INFO)


class DremioWrapper:
    def __init__(self, host: str, username: str, password: str):
        # dremio
        self._host = host
        self._username = username
        self._password = password

        # api
        self._url_login = f'{self._host}/apiv2/login'
        self._url_sql = f'{self._host}/api/v3/sql'
        self._url_jobstatus = f'{self._host}/api/v3/job/'
        self._url_manage = f'{self._host}/api/v3/catalog'
        self._url_view = f'{self._host}/api/v3/catalog/by-path/'
        self._url_documentation = f'{self._host}/api/v3/catalog/@@@@@/collaboration/wiki'
        self._url_reflection = f'{self._host}/api/v3/reflection'
        self._url_refresh_pds = f'{self._host}/api/v3/catalog/@@@@@'

    def get_token(self) -> str:
        """
        Get the API token
        :return: token
        """
        data = {
            'userName': self._username,
            'password': self._password
        }
        response = requests.post(
            url=self._url_login,
            json=data
        )
        token = None
        if response.status_code == requests.codes.ok:
            token = response.json().get('token', None)
        if token:
            return token
        else:
            raise DremioException(response.text)

    def create_element(self, element_type: str, element_name_or_path: str) -> str:
        """
        Create a Dremio element.
        :param element_type: may be 'folder' or 'space'.
        :param element_name_or_path: desired path into Dremio.
        :return: Dremio ID of the element.
        """
        assert element_type in ['folder', 'space']
        token = self.get_token()
        header = {
            'Authorization': f'_dremio{token}',
            'Content-Type': 'application/json',
            'cache-control': 'no-cache'
        }
        if element_type == 'space':
            data = {
                'entityType': element_type,
                'name': element_name_or_path,
            }
        elif element_type == 'folder':
            data = {
                'entityType': element_type,
                'path': element_name_or_path.split('/'),
            }
        result = None
        response = requests.post(
            url=self._url_manage,
            headers=header,
            json=data
        )
        if response.status_code == requests.codes.ok:
            result = response.json().get('id', None)
        elif response.status_code == requests.codes.conflict:
            result = 'already exists'
        if result:
            return result
        else:
            raise DremioException(response.text)

    def delete_element(self, element_id: str) -> str:
        """
        Remove a Dremio element.
        :param element_id: Dremio ID of element.
        :return: confirmation.
        """
        token = self.get_token()
        header = {
            'Authorization': f'_dremio{token}',
            'Content-Type': 'application/json',
            'cache-control': 'no-cache'
        }
        result = None
        response = requests.delete(
            url=f'{self._url_manage}/{element_id}',
            headers=header,
        )
        if response.status_code == requests.codes.no_content:
            result = 'removed'
        if result:
            return result
        else:
            raise DremioException(response.text)

    def get_run_status(self, id: str) -> str:
        """
        Get the status of a Dremio operation.
        :param id: Job ID.
        :return: 'COMPLETED', 'CANCELED' or 'FAILED'
        """
        token = self.get_token()
        header = {
            'Authorization': f'_dremio{token}',
            'Content-Type': 'application/json',
            'cache-control': 'no-cache'
        }
        result = None
        max_tries = 300
        while result not in ['COMPLETED', 'CANCELED', 'FAILED'] and max_tries > 0:
            max_tries -= 1
            response = requests.get(
                url=self._url_jobstatus + id,
                headers=header
            )
            if response.status_code == requests.codes.ok:
                result = response.json().get('jobState', None)
            if result not in ['COMPLETED', 'CANCELED', 'FAILED']:
                time.sleep(1)
        if result:
            return result
        else:
            raise DremioException(response.text)

    def run_sql(self, command: str) -> str:
        """
        Run a query into Dremio.
        :param command: sql query.
        :return: 'COMPLETED', 'CANCELED' or 'FAILED'
        """
        token = self.get_token()
        payload = {
            'sql': command
        }
        header = {
            'Authorization': f'_dremio{token}',
            'Content-Type': 'application/json',
            'cache-control': 'no-cache'
        }
        response = requests.post(
            url=self._url_sql,
            json=payload,
            headers=header
        )
        result = None
        if response.status_code == requests.codes.ok:
            job = response.json().get('id', None)
            result = self.get_run_status(id=job)
        if result:
            return result
        else:
            raise DremioException(response.text)

    def get_element_id(self, path: str) -> str:
        """
        Get Dremio element ID.
        :param path: path of element (like source/folder1/folder2/my_file.csv or source/folder1/folder2)
        :return: Dremio element ID
        """
        path = path.replace('.', '/').replace(r'"', '')
        token = self.get_token()
        header = {
            'Authorization': f'_dremio{token}',
            'Content-Type': 'application/json',
            'cache-control': 'no-cache'
        }
        result = None
        max_tries = 10
        while not result and max_tries > 0:
            max_tries -= 1
            response = requests.get(
                url=self._url_view + path,
                headers=header
            )
            if response.status_code == requests.codes.ok:
                result = response.json().get('id', None)
            if not result:
                time.sleep(.5)
        if result:
            return result
        else:
            raise DremioException(response.text)

    def create_documentation(self, element_id: str, text: str) -> str:
        """
        Create documentation for VDS.
        :param element_id: Dremio ID for VDS.
        :param text: markdown text to be documented.
        :return: confirmation.
        """
        logging.info(f'Creating or replacing documentation for {element_id}...')

        token = self.get_token()
        header = {
            'Authorization': f'_dremio{token}',
            'Content-Type': 'application/json',
            'cache-control': 'no-cache'
        }

        # recovering version number
        response = requests.get(
            url=self._url_documentation.replace('@@@@@', element_id),
            headers=header,
        )
        version = None
        if response.status_code == requests.codes.ok:
            version = response.json().get('version', None)
        data = {
            'text': text
        }
        if version is not None:
            data['version'] = version

        result = None
        response = requests.post(
            url=self._url_documentation.replace('@@@@@', element_id),
            headers=header,
            json=data
        )
        if response.status_code == requests.codes.ok:
            logging.info(f'Documentation done!')
            return 'ok'
        else:
            logging.error(f'Documentation creation error: {response.text}')
            raise DremioException(response.text)

    def create_or_replace_vds(self, vds_path: str, query: str, docs: str = None):
        """
        Create (or replace) a VDS.
        :param vds_path: desired path for VDS.
        :param query: sql query to mount VDS.
        :param docs: markdown text for documentation.
        """
        logging.info(f'Creating or replacing VDS {vds_path}...')

        qheader = f'CREATE OR REPLACE VDS {vds_path} AS'
        result = self.run_sql(
            command=f'{qheader} {query}',
        )
        if 'FAILED' in result:
            logging.error(f'Creation failed! Error in query {query}')
            raise DremioException(result)
        if docs:
            eid = self.get_element_id(path=vds_path)
            self.create_documentation(element_id=eid, text=docs)
        logging.info('VDS done!')

    def refresh_parquet_pds(self, pds_path: str) -> str:
        """
        Refresh a parquet PDS.
        :param pds_path: path of PDS.
        :return: confirmation.
        """
        pds_path = pds_path.replace('.', '/').replace(r'"', '')
        logging.info('Checking already existing PDS...')
        element_id_antigo = self.get_element_id(path=pds_path)
        if pds_path not in element_id_antigo:
            logging.info('Removing old PDS...')
            try:
                self.delete_element(element_id_antigo)
                logging.info('Old PDS removed!')
            except DremioException:
                logging.info('PDS not found...')
            element_id = self.get_element_id(path=pds_path)
        else:
            logging.info('PDS not found...')
            element_id = element_id_antigo

        logging.info('Creating new PDS...')
        token = self.get_token()
        payload = {
            'entityType': 'dataset',
            'id': element_id,
            'path': pds_path.split('/'),
            'type': 'PHYSICAL_DATASET',
            'format': {
                'type': 'Parquet'
            }
        }
        header = {
            'Authorization': f'_dremio{token}',
            'Content-Type': 'application/json',
            'cache-control': 'no-cache'
        }
        element_id_quoted = quote(element_id, safe='')
        response = requests.post(
            url=self._url_refresh_pds.replace('@@@@@', element_id_quoted),
            json=payload,
            headers=header
        )
        result = None
        if response.status_code == requests.codes.ok:
            result = response.json().get('id', None)
        else:
            raise DremioException(response.text)
        logging.info('Done!')
        return result
