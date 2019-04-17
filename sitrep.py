import difflib
import json
import os
import sys
import time

import imgkit
from colorama import Fore, init

from util import GET, MD5, POST, UploadImage, now, nowTimestamp


class SitRep:
    """
    SitRep is a JSON file-watching service which generates a diff report
    and notifies the user via Discord.
    """

    def main(self):
        # Initialize Colorama
        init(autoreset=True)

        initialized = SitRep.LoadConfiguration(self)

        while initialized is True:
            for url in self.fullURLs:
                filename = MD5(url)
                data = GET(url)

                if data == None:
                    print(Fore.RED + f"[{now()}] Failed to GET {url}")
                else:
                    # Determine if URL is already being watched
                    if os.path.isfile(f"data/{filename}.json") == False:
                        print(
                            Fore.BLUE
                            + f"[{now()}] {filename}.json does not exist, creating it"
                        )

                        try:
                            with open(
                                f"data/{filename}.json", "w", encoding="utf-8"
                            ) as file:
                                file.write(data)
                        except Exception as e:
                            print(Fore.RED + f"Failed to create {filename}.json. {e}.")
                    # URL is already being watched, diff it
                    else:
                        diff = SitRep.Diff(self, filename, data)

                        if diff == None:
                            pass
                        else:
                            print(f"[{now()}] {filename} has changed")

                            diff = UploadImage(self.imgurClientId, diff)

                            if diff == None:
                                print(Fore.RED + f"Failed to upload {filename} diff")
                            else:
                                SitRep.Notify(self, filename, url, diff)

                                try:
                                    with open(
                                        f"data/{filename}.json", "w", encoding="utf-8"
                                    ) as file:
                                        file.write(data)
                                except Exception as e:
                                    print(
                                        Fore.RED
                                        + f"Failed to save latest {filename}.json. {e}."
                                    )

            print(Fore.GREEN + f"[{now()}] Sleeping for {self.interval}s...")
            time.sleep(self.interval)

    def LoadConfiguration(self):
        """
        Set the configuration values specified in configuration.json
        
        Return True if configuration sucessfully loaded, otherwise return False.
        """

        try:
            with open("configuration.json", "r") as configurationFile:
                configuration = json.load(configurationFile)

                self.webhook = configuration["webhook"]["url"]
                self.username = configuration["webhook"]["username"]
                self.avatar = configuration["webhook"]["avatarURL"]
                self.color = configuration["webhook"]["color"]
                self.interval = configuration["interval"]
                self.imgurClientId = configuration["imgurClientId"]
                self.fullURLs = configuration["urls"]["full"]
                # self.keyURLs = configuration["urls"]["keys"]
                # self.valueURLs = configuration["urls"]["values"]

                print(Fore.GREEN + f"[{now()}] Configuration loaded")

                return True
        except Exception as e:
            print(Fore.RED + f"[{now()}] Failed to load configuration. {e}")

            return False

    def Diff(self, filename: str, newData: str):
        """
        Return a diff report of the specified local file compared to
        the provided raw data.
        """

        with open(f"data/{filename}.json", "r") as oldFile:
            oldData = oldFile.read()

            if MD5(oldData) == MD5(newData):
                return None
            else:
                try:
                    # Format the JSON for an accurate diff report
                    oldData = json.dumps(json.loads(oldData), indent=2).splitlines()
                    newData = json.dumps(json.loads(newData), indent=2).splitlines()

                    diff = difflib.HtmlDiff(tabsize=4).make_table(
                        oldData, newData, context=True, numlines=0
                    )

                    options = {"quiet": None}
                    diff = imgkit.from_string(
                        diff, False, options=options, css="stylesheet.css"
                    )

                    return diff
                except Exception as e:
                    print(
                        Fore.RED
                        + f"[{now()}] Failed to generate diff for {filename}. {e}"
                    )

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
                        "icon_url": self.avatar,
                    },
                    "description": url,
                    "image": {"url": image},
                    "footer": {"text": filename},
                    "timestamp": nowTimestamp(),
                }
            ],
        }

        notified = POST(self.webhook, data)

        if notified == True:
            pass
        else:
            print(
                Fore.RED
                + f"[{now()}] Failed to notify of changes in {filename}. {notified}."
            )


if __name__ == "__main__":
    try:
        SitRep.main(SitRep)
    except KeyboardInterrupt:
        sys.exit(0)
