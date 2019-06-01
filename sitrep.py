import difflib
import json
import os
import sys
import time

import imgkit

from logger import Log
from util import Utility


class SitRep:
    """
    SitRep is a JSON file-watching service which generates a diff report
    and notifies the user via Discord.
    """

    def init(self):
        Log.Intro(self, "SitRep - JSON file-watching diff service")
        Log.Intro(self, "https://github.com/EthanC/SitRep\n")

        initialized = SitRep.LoadConfiguration(self)

        while initialized is True:
            for url in self.jsonURLs:
                SitRep.main(self, url, "json")

            if self.autoClean == True:
                SitRep.Clean(self)

            Log.Success(self, f"Sleeping for {self.interval}s...")
            time.sleep(self.interval)

            initialized = SitRep.LoadConfiguration(self)

    def main(self, url: str, extension: str):
        filename = Utility.MD5(self, url)
        data = Utility.GET(self, url)

        if data is not None:
            if os.path.isfile(f"data/{filename}.{extension}") == False:
                Log.Info(self, f"{filename}.{extension} does not exist, creating it")

                Utility.WriteFile(self, filename, extension, data)
            else:
                diff = SitRep.Diff(self, filename, extension, data)

                if diff is not None:
                    Log.Print(self, f"Generated diff for {filename}.{extension}")

                    diff = Utility.UploadImage(self, self.imgurClientId, diff)
                    paste = Utility.UploadPaste(
                        self, self.pastebinAPIKey, data, filename, extension
                    )

                    if diff is not None:
                        notified = SitRep.Notify(
                            self, filename, extension, url, diff, paste
                        )

                        if notified == True:
                            Utility.WriteFile(self, filename, extension, data)

    def LoadConfiguration(self):
        """
        Set the configuration values specified in configuration.json
        
        Return True if configuration sucessfully loaded.
        """

        configuration = json.loads(Utility.ReadFile(self, "configuration", "json", ""))

        try:
            self.webhook = configuration["webhook"]["url"]
            self.username = configuration["webhook"]["username"]
            self.avatar = configuration["webhook"]["avatarURL"]
            self.color = configuration["webhook"]["color"]
            self.interval = configuration["interval"]
            self.autoClean = configuration["autoClean"]
            self.imgurClientId = configuration["imgurClientId"]
            self.pastebinAPIKey = configuration["pastebinAPIKey"]
            self.jsonURLs = configuration["urls"]["json"]

            Log.Success(self, "Loaded configuration")

            return True
        except Exception as e:
            Log.Error(self, f"Failed to load configuration, {e}")

    def Diff(self, filename: str, extension: str, newData: str):
        """
        Return a diff report of the specified local file compared to
        the provided raw data.
        """

        oldData = Utility.ReadFile(self, filename, extension)

        if Utility.MD5(self, oldData) != Utility.MD5(self, newData):
            try:
                if extension == "json":
                    # Format the JSON for an accurate diff report
                    oldData = json.dumps(json.loads(oldData), indent=4).splitlines()
                    newData = json.dumps(json.loads(newData), indent=4).splitlines()

                diff = difflib.HtmlDiff(tabsize=4).make_table(
                    oldData, newData, context=True, numlines=0
                )

                options = {"encoding": "UTF-8", "quiet": ""}
                diff = imgkit.from_string(
                    diff, False, options=options, css="stylesheet.css"
                )

                return diff
            except Exception as e:
                Log.Error(
                    self, f"Failed to generate diff for {filename}.{extension}, {e}"
                )

    def Notify(self, filename: str, extension: str, url: str, image: str, paste: str):
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
                        "icon_url": "https://github.com/EthanC/SitRep/raw/master/SitRepPro.png",
                    },
                    "description": url,
                    "fields": [
                        {
                            "name": "Raw",
                            "value": f"[Pastebin]({paste})"
                        }
                    ],
                    "image": {"url": image},
                    "footer": {"text": f"{filename}.{extension}"},
                    "timestamp": Utility.nowISO(self),
                }
            ],
        }

        status = Utility.Webhook(self, self.webhook, data)

        if status == True:
            return True
        else:
            Log.Error(
                self,
                f"Failed to notify of changes in {filename}.{extension} (HTTP {status})",
            )

    def Clean(self):
        """
        Automatically delete any files stored in the data directory which
        are no longer watched.
        """

        files = os.listdir("data/")
        watched = []
        cleaned = 0

        for url in self.jsonURLs:
            watched.append(Utility.MD5(self, url))

        for file in files:
            filename = file.split(".")[0]
            extension = file.split(".")[1]

            if filename not in watched:
                Utility.DeleteFile(self, filename, extension)

                cleaned = cleaned + 1

        if cleaned > 0:
            Log.Success(self, f"Cleaned {cleaned} unused file(s)")


if __name__ == "__main__":
    try:
        SitRep.init(SitRep)
    except KeyboardInterrupt:
        Log.Success(SitRep, "Stopping...")
        sys.exit(0)
