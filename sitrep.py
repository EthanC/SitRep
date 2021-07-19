import json
from datetime import datetime
from difflib import Differ
from sys import exit, stderr
from typing import Any, Dict, Iterator

from github import Github
from loguru import logger
from notifiers.logging import NotificationHandler

from utils import Utility


class SitRep:
    """
    SitRep is an automated data comparison utility that reports its
    findings via Discord.

    https://github.com/EthanC/SitRep
    """

    def Initialize(self: Any) -> None:
        """Initialize SitRep and begin primary functionality."""

        logger.info("SitRep")
        logger.info("https://github.com/EthanC/SitRep")

        self.config: Dict[str, Any] = SitRep.LoadConfig(self)

        SitRep.SetupLogging(self)

        self.git: Github = Utility.GitLogin(self)

        for source in self.config["dataSources"]:
            SitRep.ProcessDataSource(self, source)

        logger.success("Finished processing data sources")

    def LoadConfig(self: Any) -> Dict[str, Any]:
        """Load the configuration values specified in config.json"""

        try:
            with open("config.json", "r") as file:
                config: Dict[str, Any] = json.loads(file.read())
        except Exception as e:
            logger.critical(f"Failed to load configuration, {e}")

            exit(1)

        logger.success("Loaded configuration")

        return config

    def SetupLogging(self: Any) -> None:
        """Setup the logger using the configured values."""

        settings: Dict[str, Any] = self.config["logging"]

        if (level := settings["severity"].upper()) != "DEBUG":
            try:
                logger.remove()
                logger.add(stderr, level=level)

                logger.success(f"Set logger severity to {level}")
            except Exception as e:
                # Fallback to default logger settings
                logger.add(stderr, level="DEBUG")

                logger.error(f"Failed to set logger severity to {level}, {e}")

        if settings["discord"]["enable"] is True:
            level: str = settings["discord"]["severity"].upper()
            url: str = settings["discord"]["webhookUrl"]

            try:
                # Notifiers library does not natively support Discord at
                # this time. However, Discord will accept payloads which
                # are compatible with Slack by appending to the url.
                # https://github.com/liiight/notifiers/issues/400
                handler: NotificationHandler = NotificationHandler(
                    "slack", defaults={"webhook_url": f"{url}/slack"}
                )

                logger.add(
                    handler,
                    level=level,
                    format="```\n{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {name}:{function}:{line} - {message}\n```",
                )

                logger.success(f"Enabled logging to Discord with severity {level}")
            except Exception as e:
                logger.error(f"Failed to enable logging to Discord, {e}")

    def ProcessDataSource(self: Any, source: Dict[str, Any]) -> None:
        """Prepare to diff the provided data source."""

        source["hash"] = Utility.MD5(self, source["url"])
        source["old"] = {}
        source["new"] = {}

        old: Dict[str, Any] = source["old"]
        new: Dict[str, Any] = source["new"]

        format: str = source["contentType"].upper()

        if format == "JSON":
            source["ext"] = "json"
            source["filename"] = source["hash"] + "." + source["ext"]
            old["gist"] = Utility.GetGist(self, source["filename"])
            new["raw"] = Utility.FormatJSON(self, Utility.GET(self, source["url"]))

            if (new["raw"] is not None) and (old["gist"] is not None):
                old["raw"] = Utility.FormatJSON(
                    self, Utility.GetGistRaw(self, old["gist"], source["filename"])
                )

                SitRep.DiffJSON(self, source)
            elif (new["raw"] is not None) and (old["gist"] is None):
                Utility.CreateGist(self, source)
        else:
            logger.error(f"Data source with content type {format} is not supported")
            logger.debug(source)

    def DiffJSON(self: Any, source: Dict[str, Any]) -> None:
        """Diff the provided JSON data source."""

        filename: str = source["filename"]
        url: str = source["url"]

        old: Dict[str, Any] = source["old"]
        new: Dict[str, Any] = source["new"]

        old["hash"] = Utility.MD5(self, old["raw"])
        new["hash"] = Utility.MD5(self, new["raw"])

        if old["hash"] == new["hash"]:
            logger.info(f"No difference found in {filename} ({url})")

            return

        diff: Iterator[str] = Differ().compare(
            old["raw"].splitlines(), new["raw"].splitlines()
        )

        desc: str = ""
        additions: int = 0
        deletions: int = 0

        for line in diff:
            if line.startswith("+ "):
                additions += 1
                desc += line.replace("+     ", "+ ") + "\n"
            elif line.startswith("- "):
                deletions += 1
                desc += line.replace("-     ", "- ") + "\n"

        desc = Utility.Truncate(self, desc, 4048, split="\n")
        source["urlTrim"] = Utility.Truncate(self, url, 256)

        success: bool = SitRep.Notify(
            self,
            {
                "title": source["urlTrim"],
                "description": f"```diff\n{desc}```",
                "url": url,
                "filename": source["filename"],
                "additions": f"{additions:,}",
                "deletions": f"{deletions:,}",
                "diffUrl": source["old"]["gist"].html_url + "/revisions",
            },
        )

        # Ensure no changes go without notification
        if success is True:
            Utility.UpdateGist(self, source)

    def Notify(self: Any, embed: Dict[str, Any]) -> bool:
        """Report diff to the configured Discord webhook."""

        diffUrl: str = embed["diffUrl"]

        payload: Dict[str, Any] = {
            "username": self.config["discord"]["username"],
            "avatar_url": self.config["discord"]["avatarUrl"],
            "embeds": [
                {
                    "title": embed.get("title"),
                    "description": embed.get("description"),
                    "url": embed.get("url"),
                    "timestamp": datetime.utcnow().isoformat(),
                    "color": int("66BB6A", base=16),
                    "footer": {
                        "text": embed.get("filename"),
                    },
                    "image": {"url": embed.get("imageUrl")},
                    "author": {
                        "name": "SitRep",
                        "url": "https://github.com/EthanC/SitRep",
                        "icon_url": "https://i.imgur.com/YDZgxh2.png",
                    },
                    "fields": [
                        {
                            "name": "Additions",
                            "value": embed.get("additions"),
                            "inline": True,
                        },
                        {
                            "name": "Deletions",
                            "value": embed.get("deletions"),
                            "inline": True,
                        },
                        {
                            "name": "Diff History",
                            "value": f"[View on GitHub]({diffUrl})",
                            "inline": True,
                        },
                    ],
                }
            ],
        }

        return Utility.POST(self, self.config["discord"]["webhookUrl"], payload)


if __name__ == "__main__":
    try:
        SitRep.Initialize(SitRep)
    except KeyboardInterrupt:
        exit()
