# Caicurator
Caicurator finds all the CharacterAI indices from your web browser history and
then displays every bot you had ever talked to in a convenient web menu.

> [!IMPORTANT]
> This project only works with [Chromium-based browsers](https://en.wikipedia.org/wiki/Chromium_(web_browser)) (like Chrome) and [Gecko-based browsers](https://en.wikipedia.org/wiki/Gecko_(software)) (like Firefox).

# Screenshot
![](assets/menu.png)

https://github.com/user-attachments/assets/818ec3e3-1602-4237-97d2-4663e912adac


# Usage
Run `caicurator` to see this error message:

```
2026-01-24 20:40:00.067 | ERROR    | caicurator.cli:main:19 - Configuration not found. '/home/myxi/.config/caicurator/config.ini' doesn't exist.
```

Create a `config.ini` at the path that the error message says. Please head over to [Configuration](#configuration) for more information.

# Installation
## From PyPi
```
pip install caicurator
```
> [!TIP]
> You can also use [`uv`](https://docs.astral.sh/uv/getting-started/installation/) like so: 
> ```
> uv tool install caicurator
> ```

## From Source
> [!IMPORTANT]
> Installation of [Git](https://git-scm.com/) is required.

```
pip install git+https://github.com/eeriemyxi/caicurator.git
```

# Configuration
Caicurator uses a `config.ini` file to store all the configurations.

> [!TIP]
> Read about [INI file](https://en.wikipedia.org/wiki/INI_file) to learn more about the format.

```ini
[common]
LOG_PATH = <default>

[auth]
TOKEN = ...

[browser]
CHROMIUM_HISTORY_FILES = ["~/.config/vivaldi/Default/History"]
GECKO_HISTORY_FILES = ["~/.zen/3g4fsk4q.Default (release)/places.sqlite"]

[fetch]
PATH = <default>
BATCH_SIZE = 4
SLEEP_RANGE = 1, 5
HTML_GEN_INTERVAL = 2

[html]
PATH = <default>
SORTING = newest
```

`<default>` means the default value will be used. Using this means the relevant content will be under the configuration directory, e.g., `.../chars`, `.../index.html`, and `.../logs`.

***
`common.LOG_PATH` is the path to the log file.
***
`auth.TOKEN` is the token that you get from [CharacterAI](https://character.ai/). You can find the token in the dev tools of your browser.
***
- `browser.CHROMIUM_HISTORY_FILES` is a list of paths to the `History` file of your Chromium-based browsers (e.g., [Vivaldi](https://vivaldi.com/), [Chrome](https://www.google.com/chrome/)).
- `browser.GECKO_HISTORY_FILES` is a list of paths to the `places.sqlite` file of your Gecko-based browsers (e.g., [Firefox](https://www.mozilla.org/en-US/firefox/), [Zen](https://zen-browser.app/)).
***
- `fetch.PATH` is the path to the directory that contains all the character indices.
- `fetch.BATCH_SIZE` is the number of async requests that will be sent to the server.
- `fetch.SLEEP_RANGE` is the range of seconds that will be randomly chosen to sleep between each batch. 
- `fetch.HTML_GEN_INTERVAL` is the interval of generating the HTML page; e.g., `2` means generating the HTML page every 2 batches.
***
- `html.PATH` is the path to the HTML file.
- `html.SORTING` is the sorting method. It can be `newest` or `oldest`.

# Command-line Arguments
```
> caicurator --help
Usage: caicurator [OPTIONS] COMMAND [ARGS]...

  Curate and display Character AI web browser history

Options:
  -L, --log-level [trace|debug|info|success|warning|error|critical]
  -v, -V, --version               Show the version and exit.
  --help                          Show this message and exit.

Commands:
  chars  manage characters index (update)
  html   manage the HTML page (open, update)
  info   show helpful information

  🔗 Homepage: https://github.com/eeriemyxi/caicurator
```
