"""Common functions for the SDK."""

import re
import urllib.parse
from enum import Enum

import httpx

_USER_AGENT_REGEX = re.compile(
    r"^[A-Za-z0-9]+(?:/[0-9A-Za-z]+(?:\.[0-9A-Za-z]+)*(-[a-z]+)?)? [A-Za-z-0-9]+$"
)
_USER_AGENT_DOC_URL = "https://developer.cisco.com/meraki/api-v1/user-agents-overview/"


class BaseURL(str, Enum):
    """Base URL for the Meraki dashboard API."""

    # Default base URL for the Meraki dashboard API.
    DEFAULT = "https://api.meraki.com/api/v1"
    # Canada base URL for the Meraki dashboard API.
    CANADA = "https://api.meraki.ca/api/v1"
    # China base URL for the Meraki dashboard API.
    CHINA = "https://api.meraki.cn/api/v1"
    # India base URL for the Meraki dashboard API.
    INDIA = "https://api.meraki.in/api/v1"
    # United States FedRAMP URL for the Meraki dashboard API.
    US_FEDRAMP = "https://api.gov-meraki.com/api/v1"


def format_user_agent_caller(caller: str | None = None) -> str:
    """Generate the caller portion of the User-Agent header.

    Args:
        caller: The caller identifier following the user agent format.

    Returns:
        The formatted caller string for the User-Agent header.

    Raises:
        ValueError: If caller doesn't match the expected format.

    """
    if caller is None:
        return "Caller/(unidentified)"
    if _USER_AGENT_REGEX.match(caller):
        return f"Caller/({caller})"
    raise ValueError(
        f"Invalid MERAKI_PYTHON_SDK_CALLER format: {caller!r}. See: {_USER_AGENT_DOC_URL}"
    )


def handle_3xx(response: httpx.Response) -> tuple[str, str]:
    """Handle 3xx redirects.

    Args:
        base_url: The base URL to use for the request.
        response: The response from the request.

    Returns:
        A tuple containing the absolute URL and the new base URL.

    Raises:
        ValueError: If the redirect URL doesn't match expected Meraki API patterns.

    """
    abs_url = response.headers["Location"]

    for base in BaseURL:
        parsed = urllib.parse.urlparse(base.value)
        # Pattern: domain (without api. prefix) + /api/v
        domain = parsed.netloc.removeprefix("api.")
        pattern = f"{domain}/api/v"

        idx = abs_url.find(pattern)
        if idx != -1:
            new_base_url = abs_url[: idx + len(pattern) + 1]
            return abs_url, new_base_url

    raise ValueError(f"Unexpected redirect URL: {abs_url!r}")
