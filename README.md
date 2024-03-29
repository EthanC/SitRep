# SitRep

SitRep is an automated data comparison utility that reports its findings via [Discord](https://discord.com/).

<p align="center">
    <img src="https://i.imgur.com/QFJdCoE.png" draggable="false">
</p>

## Usage

Open `config_example.json` and provide the configurable values, then save and rename the file to `config.json`.

SitRep is designed to be ran using a task scheduler, such as [cron](https://crontab.guru/).

```
python sitrep.py
```

### Supported Content Types

**JSON (JavaScript Object Notation)**

-   `url`: string
-   `allowRevert`: bool (optional, default `true`)

**Images (PNG, JPG, GIF, etc.)**

-   `url`: string
-   `allowRevert`: bool (optional, default `true`)

**Text (Raw Plaintext)**

-   `fileType`: string (optional, default `txt`)
-   `url`: string
-   `allowRevert`: bool (optional, default `true`)

## Credits

-   Activision / Infinity Ward: [Call of Duty: Modern Warfare 3 SitRep Pro Perk icon](https://callofduty.fandom.com/wiki/SitRep)
