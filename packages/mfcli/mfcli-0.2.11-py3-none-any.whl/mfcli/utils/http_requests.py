import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def get_retry_session(
        retries: int = 3,
        backoff_factor: float = 0.5,
        status_forcelist: tuple = (500, 502, 503, 504),
        allowed_methods: tuple = ("GET", "POST", "PUT", "DELETE", "PATCH")
) -> requests.Session:
    """Create a requests session with retry logic."""
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=allowed_methods,
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def http_request(
        method: str,
        url: str,
        retries: int = 3,
        timeout: int = 10,
        **kwargs
) -> requests.Response:
    """
    Perform an HTTP request with automatic retry logic.

    :param method: HTTP method (GET, POST, PUT, DELETE, etc.)
    :param url: URL to request
    :param retries: Number of retry attempts
    :param timeout: Timeout per request in seconds
    :param kwargs: Any requests.request() parameters (headers, data, json, etc.)
    :return: requests.Response object
    """
    session = get_retry_session(retries=retries)
    try:
        response = session.request(method.upper(), url, allow_redirects=True, timeout=timeout, **kwargs)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException:
        raise
    finally:
        session.close()
