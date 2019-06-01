# <img src="SitRepPro.png" width="32px" draggable="false"> SitRep

SitRep is a JSON file-watching service which generates a diff report and notifies the user via [Discord](https://discordapp.com).

## Requirements

- [Python 3.7](https://www.python.org/downloads/)
- [Requests](http://docs.python-requests.org/en/master/user/install/)
- [Colorama](https://pypi.org/project/colorama/)
- [imgkit](https://github.com/jarrekk/imgkit#installation)

An [Imgur Client ID](https://apidocs.imgur.com/#intro) is required to upload the diff report images.

A [Pastebin API Key](https://pastebin.com/api#1) is required to upload the raw data to Pastebin.

## Usage

Open `configuration_example.json` in your preferred text editor, fill in all configurable values. Rename the file to `configuration.json`.

```
python sitrep.py
```

## Credits

- Activision / Infinity Ward: [Call of Duty: Modern Warfare 3 SitRep Pro Perk icon](https://callofduty.fandom.com/wiki/SitRep)
