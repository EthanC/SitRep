import difflib
import json
import logging
from sys import exit

import coloredlogs
from github import Github, InputFileContent

from util import Utility

log = logging.getLogger(__name__)
coloredlogs.install(level="INFO", fmt="[%(asctime)s] %(message)s", datefmt="%I:%M:%S")


class SitRep:
    """
    SitRep is a JSON file-watching service which generates a diff report
    and notifies the user via Discord.
    """

    def main(self):
        print("SitRep - JSON file-watching diff service")
        print("https://github.com/EthanC/SitRep\n")

        initialized = SitRep.LoadConfiguration(self)

        self.textFormats = ["json", "txt"]

        if initialized is True:
            self.git = SitRep.LoginGitHub(self)

            if self.git is not None:
                log.info("Authenticated with GitHub")

                for url in self.jsonURLs:
                    SitRep.Watch(self, url, "json")

    def LoadConfiguration(self):
        """
        Set the configuration values specified in configuration.json
        
        Return True if configuration sucessfully loaded.
        """

        configuration = json.loads(Utility.ReadFile(self, "configuration", "json"))

        try:
            self.accessToken = configuration["github"]["accessToken"]
            self.jsonURLs = configuration["urls"]["json"]
            self.avatar = configuration["webhook"]["avatarURL"]
            self.color = configuration["webhook"]["color"]
            self.webhook = configuration["webhook"]["url"]
            self.username = configuration["webhook"]["username"]

            log.info("Loaded configuration")

            return True
        except Exception as e:
            log.critical(f"Failed to load configuration, {e}")

    def LoginGitHub(self):
        """ToDo"""

        git = Github(self.accessToken)

        try:
            ratelimit = git.get_rate_limit().core
        except Exception as e:
            log.critical(f"Failed to authenticate with GitHub, {e}")

            return

        log.debug(
            f"Rate Limit - Remaining: {ratelimit.remaining}, Total: {ratelimit.limit}"
        )

        if ratelimit.remaining < len(self.jsonURLs):
            log.critical(f"Insufficient GitHub requests remaining, rate limited")

            return

        return git

    def Watch(self, url: str, extension: str):
        """ToDo"""

        filename = Utility.MD5(self, url)
        newData = Utility.GET(self, url)

        if (filename is not None) and (newData is not None):
            gist = SitRep.GetGist(self, filename, extension)

            if gist is False:
                log.info(f"{url} is not yet watched, creating it")
                SitRep.CreateGist(self, filename, extension, newData, url)
            elif gist is not None:
                if extension in self.textFormats:
                    diff = SitRep.Diff(
                        self,
                        extension,
                        newData,
                        gist.files[f"{filename}.{extension}"].content,
                    )

                    if diff is not None:
                        log.info(f"{filename}.{extension} has changed")

                        codeblock = SitRep.GenerateCodeblock(self, diff)
                        additions, deletions = SitRep.CountChanges(self, diff)

                        notified = SitRep.Notify(
                            self,
                            filename,
                            extension,
                            url,
                            codeblock,
                            additions,
                            deletions,
                            f"[Gist]({gist.html_url}/revisions)",
                        )

                        if notified == True:
                            SitRep.UpdateGist(
                                self, gist, filename, extension, newData, url
                            )
                else:
                    log.warning(f"{url} is not a supported data type")

    def CreateGist(self, filename: str, extension: str, data: str, url: str):
        """ToDo"""

        try:
            data = {
                f"{filename}.{extension}": InputFileContent(
                    json.dumps(json.loads(data), indent=4)
                )
            }
            desc = f"Watched by SitRep (https://github.com/EthanC/SitRep) | {url}"

            self.git.get_user().create_gist(False, data, desc)
        except Exception as e:
            log.error(f"Failed to create Gist, {e}")

    def GetGist(self, filename: str, extension: str):
        """ToDo"""

        try:
            # Hacky solution to getting the desired Gist without
            # storing its ID locally.
            for gist in self.git.get_user().get_gists():
                if list(gist.files)[0] == f"{filename}.{extension}":
                    return gist

            return False
        except Exception as e:
            log.error(f"Failed to get Gist, {e}")

    def UpdateGist(self, gist, filename: str, extension: str, data: str, url: str):
        """ToDo"""

        desc = f"Watched by SitRep (https://github.com/EthanC/SitRep) | {url}"
        data = {
            f"{filename}.{extension}": InputFileContent(
                json.dumps(json.loads(data), indent=4)
            )
        }

        gist.edit(desc, data)

    def Diff(self, extension: str, newData: str, oldData):
        """
        Return a diff report of the specified local file compared to
        the provided raw data.
        """

        if (oldData is not None) and (newData is not None):
            if extension == "json":
                # Format JSON data for an accurate diff report
                oldData = json.dumps(json.loads(oldData), indent=4)
                newData = json.dumps(json.loads(newData), indent=4)

            if Utility.MD5(self, oldData) != Utility.MD5(self, newData):
                diff = difflib.Differ().compare(oldData.splitlines(), newData.splitlines())

                return list(diff)

    def GenerateCodeblock(self, diff: list):
        """ToDo"""

        data = ""

        for line in diff:
            if (line.startswith("+ ")) or (line.startswith("- ")):
                # Remove first indentation level on JSON data
                line = line.replace("+     ", "+ ")
                line = line.replace("-     ", "- ")

                data += f"{line}\n"

        # The character limit of a Discord Embed Description is 2,048
        # if codeblock exceeds 1,900 (to be safe), truncate it
        if len(data) > 1900:
            data = data[:1900]
            data = data.rsplit("\n", 1)[0]
            data += "\n...\n"

        return f"```diff\n{data}```"

    def CountChanges(self, diff: list):
        """ToDo"""

        additions = 0
        deletions = 0

        for line in diff:
            if line.startswith("+ "):
                additions += 1
            if line.startswith("- "):
                deletions += 1

        return additions, deletions

    def Notify(
        self,
        filename: str,
        extension: str,
        url: str,
        codeblock: str,
        additions: int,
        deletions: int,
        gist: str,
    ):
        """
        Send the provided diff report to the configured Discord Webhook
        using a Rich Embed.
        """

        data = {
            "username": self.username,
            "avatar_url": self.avatar,
            "embeds": [
                {
                    "color": int(self.color, base=16),
                    "author": {
                        "name": "SitRep",
                        "url": "https://github.com/EthanC/SitRep",
                        "icon_url": "https://i.imgur.com/YDZgxh2.png",
                    },
                    "description": f"{url}\n{codeblock}",
                    "fields": [
                        {"name": "Additions", "value": additions, "inline": True},
                        {"name": "Deletions", "value": deletions, "inline": True},
                        {"name": "Diff", "value": gist, "inline": True,},
                    ],
                    "footer": {"text": f"{filename}.{extension}"},
                    "timestamp": Utility.nowISO(self),
                }
            ],
        }

        status = Utility.Webhook(self, self.webhook, data)

        # HTTP 204 (No Content)
        if status == 204:
            return True
        else:
            log.error(
                f"Failed to notify of changes in {filename}.{extension} (HTTP {status})"
            )


if __name__ == "__main__":
    try:
        SitRep.main(SitRep)
    except KeyboardInterrupt:
        log.info("Exiting...")
        exit()
