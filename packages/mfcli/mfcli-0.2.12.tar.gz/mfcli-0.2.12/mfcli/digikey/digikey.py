import time

import requests
from requests import HTTPError

from mfcli.utils.config import get_config
from mfcli.utils.logger import get_logger

logger = get_logger(__name__)


class DigiKey:
    def __init__(self):
        self._config = get_config()
        self._url = "https://api.digikey.com"
        self._token: str | None = None
        self._get_access_token()
        self._session = requests.Session()
        headers = {
            "Authorization": f"Bearer {self._token}",
            "X-DIGIKEY-Client-Id": self._config.digikey_client_id,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        self._session.headers = headers

    @staticmethod
    def _format_datasheet_url(url: str | None) -> str | None:
        if url and url.startswith('//'):
            return f"https:{url}"
        return url

    def _api_call(self, method: str, url: str, data: dict | None = None) -> dict:
        max_retries = 5
        timeout = 5
        backoff_factor = 2

        for attempt in range(1, max_retries + 1):
            try:
                resp = self._session.request(method=method, url=url, json=data, timeout=timeout)

                if resp.status_code == 429:
                    if attempt == max_retries:
                        resp.raise_for_status()

                    retry_after = resp.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after is not None else backoff_factor * (2 ** (attempt - 1))
                    time.sleep(delay)
                    continue

                resp.raise_for_status()
                return resp.json()

            except requests.exceptions.Timeout:
                # Handle timeout — retry with exponential backoff
                if attempt == max_retries:
                    raise  # give up after last attempt
                delay = backoff_factor * (2 ** (attempt - 1))
                time.sleep(delay)
                continue

        raise RuntimeError("Exhausted retries without success.")

    def _get_access_token(self):
        logger.debug("Fetching Digi-Key access token")
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "client_id": self._config.digikey_client_id,
            "client_secret": self._config.digikey_client_secret,
            "grant_type": "client_credentials"
        }
        url = f"{self._url}/v1/oauth2/token"
        resp = requests.post(url, headers=headers, data=data)
        token_data = resp.json()
        self._token = token_data["access_token"]

    def _datasheet_from_part_number(self, part_number: str) -> str | None:
        url = f"{self._url}/products/v4/search/{part_number}/productdetails"
        resp = self._api_call('GET', url)
        if not resp.get("Product"):
            return None
        return resp["Product"].get("DatasheetUrl")

    def _keyword_search(self, part_number: str) -> str | None:
        payload = {
            "Keywords": part_number,
            "RecordCount": 1
        }
        url = f"{self._url}/products/v4/search/keyword"
        resp = self._api_call('POST', url, payload)
        if not resp.get("ExactMatches"):
            return None
        return resp["ExactMatches"][0].get("DatasheetUrl")

    def datasheet(self, part_number: str) -> str | None:
        datasheet_url = None
        try:
            datasheet_url = self._datasheet_from_part_number(part_number)
        except HTTPError as e:
            # Handle 404 with keyword search API, otherwise raise HTTP error
            if not e.response.status_code == 404:
                raise e
        if not datasheet_url:
            datasheet_url = self._keyword_search(part_number)
        return self._format_datasheet_url(datasheet_url)
