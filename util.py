import hashlib
import json
import os
from datetime import datetime

import requests

from logger import Log


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
            Log.Error(self, f"Failed to GET {url} (HTTP {res.status_code})")

            return None

    def POST(self, url: str, data: dict):
        """
        Send an HTTP POST request containing the provided data to the
        specified URL.
        """

        headers = {"content-type": "application/json"}
        data = json.dumps(data)

        req = requests.post(url, headers=headers, data=data)

        # HTTP 204 (No Content)
        if req.status_code == 204:
            return True
        else:
            return req.status_code

    def UploadImage(self, clientId: str, image: bytes):
        """Return the url of the provided image uploaded to Imgur."""

        payload = {"image": image}
        headers = {"Authorization": f"Client-ID {clientId}"}

        req = requests.post(
            "https://api.imgur.com/3/image", headers=headers, data=payload
        )

        # HTTP 200 (OK)
        if req.status_code == 200:
            return json.loads(req.text)["data"]["link"]
        else:
            Log.Error(self, f"Failed to upload image (HTTP {req.status_code})")

            return None

    def MD5(self, input: str):
        """Return an MD5 hash of the provided string."""

        return hashlib.md5(input.encode("utf-8")).hexdigest()

    def nowISO(self):
        """Return the current utc time in ISO8601 timestamp format."""

        return datetime.utcnow().isoformat()

    def WriteFile(
        self, filename: str, extension: str, data: str, directory: str = "data/"
    ):
        """
        Write the provided data to the specified file.
        
        Optionally specify a relative directory, defaults to `data/`.
        """

        try:
            with open(
                f"{directory}{filename}.{extension}", "w", encoding="utf-8"
            ) as file:
                file.write(data)
        except Exception as e:
            Log.Error(self, f"Failed to write {filename}.{extension}, {e}")

    def ReadFile(self, filename: str, extension: str, directory: str = "data/"):
        """
        Read and return the contents of the specified file.

        Optionally specify a relative directory, defaults to `data/`.
        """

        try:
            with open(
                f"{directory}{filename}.{extension}", "r", encoding="utf-8"
            ) as file:
                return file.read()
        except Exception as e:
            Log.Error(self, f"Failed to read {filename}.{extension}, {e}")

    def DeleteFile(self, filename: str, extension: str, directory: str = "data/"):
        """ToDo"""

        try:
            os.remove(f"{directory}{filename}.{extension}")
        except Exception as e:
            Log.Error(self, f"Failed to delete {filename}.{extension}, {e}")
