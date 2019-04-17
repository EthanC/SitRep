import hashlib
import json
from datetime import datetime

import requests


def GET(url: str, headers={}):
    """
    Return the response of a successful HTTP GET request to the specified
    URL with the optionally provided header values.
    """

    res = requests.get(url, headers=headers)

    # HTTP 200 (OK)
    if res.status_code == 200:
        return res.text
    else:
        return None


def POST(url: str, data: dict):
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
        return f"{req.text} (HTTP {req.status_code})"


def UploadImage(clientId: str, image: bytes):
    """Return the url of the provided image uploaded to Imgur."""

    payload = {"image": image}
    headers = {"Authorization": f"Client-ID {clientId}"}

    req = requests.post("https://api.imgur.com/3/image", headers=headers, data=payload)

    if req.status_code == 200:
        return json.loads(req.text)["data"]["link"]
    else:
        return None


def MD5(input: str):
    """Return an MD5 hash of the provided string."""

    return hashlib.md5(input.encode("utf-8")).hexdigest()


def now():
    """Return the current local time in 12-hour format."""

    return datetime.now().strftime("%I:%M:%S")


def nowTimestamp():
    """Return the current utc time in ISO8601 timestamp format."""

    return datetime.utcnow().isoformat()
