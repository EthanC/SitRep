import base64
import hashlib
import json
from typing import Any, Dict, Optional, Union

import httpx
from github import Github, InputFileContent
from github.Gist import Gist
from github.Rate import Rate
from httpx import Response, codes
from loguru import logger


class Utility:
    """Utilitarian functions designed for SitRep."""

    def GET(self: Any, url: str, raw: bool = False) -> Optional[Union[str, bytes]]:
        """Perform an HTTP GET request and return its response."""

        try:
            res: Response = httpx.get(url)
        except Exception as e:
            logger.error(f"GET failed {url}, {e}")

            return

        status: int = res.status_code

        if raw is True:
            data: bytes = res.content
        else:
            data: str = res.text

        logger.debug(f"(HTTP {status}) GET {url}")
        logger.trace(data)

        if codes.is_error(status) is False:
            return data
        else:
            logger.error(f"(HTTP {status}) GET failed {url}")

    def POST(self: Any, url: str, payload: Dict[str, Any]) -> bool:
        """Perform an HTTP POST request and return its status."""

        res: Response = httpx.post(
            url, data=json.dumps(payload), headers={"content-type": "application/json"}
        )

        status: int = res.status_code
        data: str = res.text

        logger.debug(f"(HTTP {status}) POST {url}")
        logger.trace(data)

        if codes.is_error(status) is False:
            return True
        else:
            logger.error(f"(HTTP {status}) POST failed {url}")

            return False

    def GitLogin(self: Any) -> Github:
        """Authenticate with GitHub using the configured credentials."""

        try:
            git: Github = Github(self.config["github"]["accessToken"], timeout=120)

            rates: Rate = git.get_rate_limit().core
            reset: str = rates.reset.strftime("%x at %X")
        except Exception as e:
            logger.critical(f"Failed to authenticate with GitHub, {e}")

            exit(1)

        logger.success("Authenticated with GitHub")
        logger.debug(
            f"{rates.remaining:,}/{rates.limit:,} requests remaining, resets {reset}"
        )

        return git

    def GetGist(self: Any, filename: str) -> Optional[Union[Gist, bool]]:
        """
        Search the authenticated GitHub user's Gists for the provided
        hash, Return False upon error.
        """

        try:
            for gist in self.git.get_user().get_gists():
                if list(gist.files)[0] == filename:
                    return gist
        except Exception as e:
            logger.error(f"Failed to get Gist {filename}, {e}")

            return False

    def GetGistRaw(self: Any, gist: Gist, filename: str) -> Optional[str]:
        """Return the raw contents of the provided Gist."""

        return Utility.GET(self, gist.files[filename].raw_url)

    def CreateGist(self: Any, source: Dict[str, Any]) -> None:
        """
        Create a Gist for the authenticated GitHub user using the provided
        data source.
        """

        filename: str = source["filename"]
        content: str = source["new"]["raw"]
        url: str = source["url"]

        public: bool = self.config["github"].get("public", False)

        try:
            data: Dict[str, InputFileContent] = {filename: InputFileContent(content)}

            self.git.get_user().create_gist(public, data, url)

            logger.success(f"Created Gist {filename} ({url})")
        except Exception as e:
            logger.error(f"Failed to create Gist {filename} ({url}), {e}")
            logger.trace(content)

    def UpdateGist(self: Any, source: Dict[str, Any]) -> None:
        """
        Update a Gist for the authenticated GitHub user using the provided
        data source.
        """

        filename: str = source["filename"]
        content: str = source["new"]["raw"]
        url: str = source["url"]
        gist: Gist = source["old"]["gist"]

        data: Dict[str, InputFileContent] = {filename: InputFileContent(content)}

        try:
            gist.edit(url, data)

            logger.success(f"Updated Gist {filename} ({url})")
        except Exception as e:
            logger.error(f"Failed to update Gist {filename} ({url}), {e}")
            logger.trace(content)

    def MD5(self: Any, input: Optional[str]) -> Optional[str]:
        """Return an MD5 hash for the provided string."""

        if input is None:
            return

        return hashlib.md5(input.encode("utf-8")).hexdigest()

    def Base64(self: Any, input: Optional[bytes]) -> Optional[str]:
        """Return a Base64 encoded string for the provided bytes."""

        if input is None:
            return

        return base64.b64encode(input).decode("utf-8")

    def Base64Size(self: Any, input: str) -> int:
        """Return the size in bytes for the provided Base64 encoded string."""

        return len(base64.b64decode(input))

    def FormatJSON(self: Any, input: Optional[str]) -> Optional[str]:
        """Format the provided JSON string with consistent indentation."""

        if input is None:
            return

        try:
            return json.dumps(json.loads(input), indent=4)
        except Exception as e:
            logger.error(f"Failed to format JSON data, {e}")
            logger.trace(input)

    def CountRange(self: Any, new: int, old: int) -> str:
        """Calculate the difference between the provided integers."""

        symbol: str = ""

        if new > old:
            symbol = "+"
        elif new < old:
            symbol = "-"

        return f"{symbol}{int(abs(new - old)):,}"

    def Truncate(
        self: Any,
        input: str,
        length: int,
        elipses: bool = True,
        split: Optional[str] = None,
    ) -> str:
        """
        Truncate the provided string to the specified length. Optionally append
        an elipses or cleanly truncate at a specific character.
        """

        if len(input) <= length:
            return input

        result: str = input[:length]

        if split is not None:
            result = result.rsplit(split, 1)[0]

        if elipses is True:
            if split == "\n":
                result += "\n"

            result += "..."

        return result
