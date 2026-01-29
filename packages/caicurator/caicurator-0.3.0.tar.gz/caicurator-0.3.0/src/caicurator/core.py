import ast
import json
import pathlib
import shutil
import sqlite3
import tempfile

from curl_cffi import requests
from loguru import logger as log

from . import constants


def get_headers(token: str) -> dict[str, str]:
    return {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9",
        "authorization": f"Token {token}",
        "content-type": "application/json",
        "origin": "https://character.ai",
        "priority": "u=1, i",
        "referer": "https://character.ai/",
        "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Linux"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "sec-gpc": "1",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    }


def get_log_path():
    default_path = path = constants.CONFIG_DIR / "logs"
    if constants.CONFIG_FILE_PATH.exists():
        path = constants.CONFIG["common"]["LOG_PATH"]

        if path.strip() == "<default>":
            path = default_path
            path.mkdir(exist_ok=True)
            return path
    else:
        path = default_path
        default_path.mkdir(exist_ok=True)

    return pathlib.Path(path).expanduser()


def get_chars_path():
    path = constants.CONFIG["fetch"]["PATH"]

    if path.strip() == "<default>":
        path = constants.CONFIG_DIR / "chars"
        path.mkdir(exist_ok=True)
        return path

    return pathlib.Path(path).expanduser()


def get_html_path():
    path = constants.CONFIG["html"]["PATH"]

    if path.strip() == "<default>":
        path = constants.CONFIG_DIR / "index.html"
        return path

    return pathlib.Path(path).expanduser()


def get_history_file_paths_chromium():
    for path in ast.literal_eval(constants.CONFIG["browser"]["CHROMIUM_HISTORY_FILES"]):
        yield pathlib.Path(path).expanduser()


def get_filtered_urls_chromium(
    history_file_path: pathlib.Path,
) -> dict[str, tuple[str, ...]]:
    filtered_urls: dict[str, tuple[str, ...]] = {}
    with tempfile.TemporaryDirectory() as tdir:
        thist = pathlib.Path(tdir) / "History"
        shutil.copy(history_file_path, thist)
        con = sqlite3.connect(thist)
        cur = con.cursor()

        for row in cur.execute(
            "SELECT url, last_visit_time FROM urls WHERE url GLOB 'https://character.ai/chat/*'"
        ):
            try:
                url = row[0][: row[0].index("?")]
            except ValueError:
                url = row[0]
            cid = url.split("/")[-1]
            if cid in filtered_urls and filtered_urls[cid][1] > row[1]:
                continue
            filtered_urls[cid] = row

    con.close()
    return filtered_urls


def get_history_file_paths_gecko():
    for path in ast.literal_eval(constants.CONFIG["browser"]["GECKO_HISTORY_FILES"]):
        yield pathlib.Path(path).expanduser()


def get_filtered_urls_gecko(
    history_file_path: pathlib.Path,
) -> dict[str, tuple[str, ...]]:
    filtered_urls: dict[str, tuple[str, ...]] = {}

    with tempfile.TemporaryDirectory() as tdir:
        thist = pathlib.Path(tdir) / "places.sqlite"
        shutil.copy(history_file_path, thist)
        con = sqlite3.connect(thist)
        cur = con.cursor()

        for row in cur.execute(
            "SELECT url, last_visit_date FROM moz_places WHERE url GLOB 'https://character.ai/chat/*'"
        ):
            try:
                url = row[0][: row[0].index("?")]
            except ValueError:
                url = row[0]
            cid = url.split("/")[-1]
            if cid in filtered_urls and filtered_urls[cid][1] > row[1]:
                continue
            filtered_urls[cid] = row

    con.close()
    return filtered_urls


def get_char_info(char_id: str) -> tuple[str, requests.Response]:
    res = requests.post(
        "https://neo.character.ai/character/v1/get_character_info",
        json=dict(lang="en", external_id=char_id),
        headers=get_headers(constants.CONFIG["auth"]["TOKEN"]),
    )
    return char_id, res


def update_last_viewed(
    files: list[pathlib.Path], filtered_urls: dict[str, tuple[str, ...]]
):
    for path in files:
        if path.stem in filtered_urls:
            data = json.loads(path.read_text())
            data["last_viewed"] = filtered_urls[path.stem][1]
            path.write_text(json.dumps(data, indent=4))
            log.trace(
                f"saved {path.stem=} with new last_viewed={filtered_urls[path.stem][1]}"
            )


def discard_existing_chars(
    files: list[pathlib.Path], filtered_urls: dict[str, tuple[str, ...]]
):
    for path in files:
        if path.stem in filtered_urls:
            del filtered_urls[path.stem]
            log.trace(f"discarding {path.stem=} because it already exists")
