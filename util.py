import hashlib
import json
import logging
import os
from datetime import datetime

import requests

log = logging.getLogger(__name__)


class Utility:
    """Class containing utilitarian functions intended to reduce duplicate code."""

    def GET(self, url: str, headers={}):
        """
        Return the response of a successful HTTP GET request to the specified
        URL with the optionally provided header values.
        """

        res = requests.get(url, headers=headers)

        # HTTP 200 (OK)
        if res.status_code == 200:
            return res.text
        else:
            log.error(f"Failed to GET {url} (HTTP {res.status_code})")

    def Webhook(self, url: str, data: dict):
        """POST the provided data to the specified Discord webhook url."""

        headers = {"content-type": "application/json"}
        data = json.dumps(data)

        req = requests.post(url, headers=headers, data=data)

        return req.status_code

    def MD5(self, input: str):
        """Return an MD5 hash of the provided string."""

        return hashlib.md5(input.encode("utf-8")).hexdigest()

    def nowISO(self):
        """Return the current utc time in ISO8601 timestamp format."""

        return datetime.utcnow().isoformat()

    def ReadFile(self, filename: str, extension: str, directory: str = ""):
        """
        Read and return the contents of the specified file.

        Optionally specify a relative directory.
        """

        try:
            with open(
                f"{directory}{filename}.{extension}", "r", encoding="utf-8"
            ) as file:
                return file.read()
        except Exception as e:
            log.error(f"Failed to read {filename}.{extension}, {e}")
