import os
from io import StringIO

import pandas as pd
import requests


class CachubClient:
    def __init__(self, base_url=None, token=None):
        self.base_url = base_url
        self.token = token

    @staticmethod
    def from_env_properties():
        return CachubClient(os.environ["CACHUB_URL"], os.environ["CACHUB_TOKEN"])

    def fetch(self, provider, **kwds):
        """Fetch data from given provider

        Args:
            provider (str): name of provider to use
            **kwds: arguments for provider

        Returns:
            (dict, pd.DataFrame): header, data
        """
        response = requests.post(f"{self.base_url}/api/{provider}", json=kwds,
                                 headers={'Authorization': f"Bearer {self.token}"})

        if response.status_code != 200:
            raise UserWarning(f"Invalid request code '{response.status_code}'")

        resp = response.json()
        df = pd.read_csv(StringIO(resp["data"]), sep=";")

        return resp["header"], df
