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

    def main(self):
        Log.Intro(self, "SitRep - JSON file-watching diff service")
        Log.Intro(self, "https://github.com/EthanC/SitRep\n")

        initialized = SitRep.LoadConfiguration(self)

        while initialized is True:
            for url in self.fullURLs:
                filename = Utility.MD5(self, url)
                data = Utility.GET(self, url)

                if data is not None:
                    if os.path.isfile(f"data/{filename}.json") == False:
                        Log.Info(self, f"{filename}.json does not exist, creating it")

                        Utility.WriteFile(self, filename, "json", data)
                    else:
                        diff = SitRep.Diff(self, filename, data)

                        if diff is not None:
                            Log.Print(self, f"{filename} has changed")

                            diff = Utility.UploadImage(self, self.imgurClientId, diff)

                            if diff is not None:
                                notified = SitRep.Notify(self, filename, url, diff)

                                if notified == True:
                                    Utility.WriteFile(self, filename, "json", data)

            Log.Success(self, f"Sleeping for {self.interval}s...")
            time.sleep(self.interval)
            initialized = SitRep.LoadConfiguration(self)

    def LoadConfiguration(self):
        """
        Set the configuration values specified in configuration.json
        
        Return True if configuration sucessfully loaded, otherwise return False.
        """

        configuration = json.loads(Utility.ReadFile(self, "configuration", "json", ""))

        try:
            self.webhook = configuration["webhook"]["url"]
            self.username = configuration["webhook"]["username"]
            self.avatar = configuration["webhook"]["avatarURL"]
            self.color = configuration["webhook"]["color"]
            self.interval = configuration["interval"]
            self.imgurClientId = configuration["imgurClientId"]
            self.fullURLs = configuration["urls"]["full"]

            Log.Success(self, "Loaded configuration")

            return True
        except Exception as e:
            Log.Error(self, f"Failed to load configuration, {e}")

    def Diff(self, filename: str, newData: str):
        """
        Return a diff report of the specified local file compared to
        the provided raw data.
        """

        oldData = Utility.ReadFile(self, filename, "json")

        if Utility.MD5(self, oldData) == Utility.MD5(self, newData):
            return None
        else:
            try:
                # Format the JSON for an accurate diff report
                oldData = json.dumps(json.loads(oldData), indent=2).splitlines()
                newData = json.dumps(json.loads(newData), indent=2).splitlines()

                diff = difflib.HtmlDiff(tabsize=4).make_table(oldData, newData)

                options = {"encoding": "utf-8", "log-level": "none"}
                diff = imgkit.from_string(
                    diff, False, options=options, css="stylesheet.css"
                )

                return diff
            except Exception as e:
                Log.Error(self, f"Failed to generate diff for {filename}, {e}")

                return None

    def Notify(self, filename: str, url: str, image: str):
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
                    "image": {"url": image},
                    "footer": {"text": filename},
                    "timestamp": Utility.nowISO(self),
                }
            ],
        }

        status = Utility.POST(self, self.webhook, data)

        if status == True:
            return True
        else:
            Log.Error(
                self, f"Failed to notify of changes in {filename} (HTTP {status})"
            )


if __name__ == "__main__":
    try:
        SitRep.main(SitRep)
    except KeyboardInterrupt:
        sys.exit(0)
