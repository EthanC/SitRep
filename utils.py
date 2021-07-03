import hashlib
import json
from typing import Any, Dict, Optional

import httpx
from github import Github, InputFileContent
from github.Gist import Gist
from github.Rate import Rate
from httpx import Response, codes
from loguru import logger


class Utility:
    """Utilitarian functions designed for SitRep."""

    def GET(self: Any, url: str) -> Optional[str]:
        """Perform an HTTP GET request and return its response."""

        res: Response = httpx.get(url)

        status: int = res.status_code
        data: str = res.text

        logger.debug(f"(HTTP {status}) GET {url}")
        logger.trace(data)

        if codes.is_error(status) is False:
            return data
        else:
            logger.error(f"(HTTP {status}) GET Failed {url}")
            logger.error(data)

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
            logger.error(f"(HTTP {status}) POST Failed {url}")
            logger.error(data)

            return False

    def GitLogin(self: Any) -> Github:
        """Authenticate with GitHub using the configured credentials."""

        try:
            git: Github = Github(self.config["github"]["accessToken"])

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

    def GetGist(self: Any, hash: str, ext: str) -> Optional[Gist]:
        """
        Search the authenticated GitHub user's Gists for the provided
        hash, return it if found.
        """

        try:
            for gist in self.git.get_user().get_gists():
                if list(gist.files)[0] == f"{hash}.{ext}":
                    return gist
        except Exception as e:
            logger.error(f"Failed to get Gist {hash}, {e}")

    def CreateGist(self: Any, source: Dict[str, Any]) -> None:
        """
        Create a Gist for the authenticated GitHub user using the provided
        data source.
        """

        hash: str = source["hash"]
        ext: str = source["ext"]
        content: str = source["new"]["raw"]
        url: str = source["url"]

        data: Dict[str, InputFileContent] = {f"{hash}.{ext}": InputFileContent(content)}
        public: bool = self.config["github"].get("public", False)

        try:
            self.git.get_user().create_gist(public, data, url)

            logger.success(f"Created Gist {hash} ({url})")
        except Exception as e:
            logger.error(f"Failed to create Gist {hash} ({url}), {e}")
            logger.trace(content)

    def UpdateGist(self: Any, source: Dict[str, Any]) -> None:
        """
        Update a Gist for the authenticated GitHub user using the provided
        data source.
        """

        hash: str = source["hash"]
        ext: str = source["ext"]
        content: str = source["new"]["raw"]
        url: str = source["url"]
        gist: Gist = source["old"]["gist"]

        data: Dict[str, InputFileContent] = {f"{hash}.{ext}": InputFileContent(content)}

        try:
            gist.edit(url, data)

            logger.success(f"Updated Gist {hash} ({url})")
        except Exception as e:
            logger.error(f"Failed to update Gist {hash} ({url}), {e}")
            logger.trace(content)

    def MD5(self: Any, input: str) -> str:
        """Return an MD5 hash for the provided string."""

        return hashlib.md5(input.encode("utf-8")).hexdigest()

    def FormatJSON(self: Any, input: str) -> str:
        """Format the provided JSON string with consistent indentation."""

        return json.dumps(json.loads(input), indent=4)

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
