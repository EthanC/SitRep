# <img src="https://i.imgur.com/YDZgxh2.png" width="32px" draggable="false"> SitRep

SitRep is a JSON file-watching service which generates a diff report and notifies the user via [Discord](https://discordapp.com).

<p align="center">
    <img src="https://i.imgur.com/DLEA1GM.png" width="650px" draggable="false">
</p>

## Requirements

-   [Python 3.7](https://www.python.org/downloads/)
-   [Requests](http://docs.python-requests.org/en/master/user/install/)
-   [PyGitHub](https://pygithub.readthedocs.io/en/latest/introduction.html#download-and-install)
-   [coloredlogs](https://pypi.org/project/coloredlogs/)

A [GitHub Access Token](https://help.github.com/en/github/authenticating-to-github/creating-a-personal-access-token-for-the-command-line) with the Gist scope is required to store files.

## Usage

Open `configuration_example.json` in your preferred text editor, fill the configurable values. Once finished, save and rename the file to `configuration.json`.

SitRep is designed to be ran using a scheduler, such as [cron](https://en.wikipedia.org/wiki/Cron).

```
python sitrep.py
```

## Credits

-   Activision / Infinity Ward: [Call of Duty: Modern Warfare 3 SitRep Pro Perk icon](https://callofduty.fandom.com/wiki/SitRep)
