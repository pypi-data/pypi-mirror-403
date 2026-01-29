import sys

import click
from loguru import logger as log

from . import constants, core

log.add(core.get_log_path() / "logs_{time}.log", level="DEBUG")


@click.group(help=constants.DESCRIPTION, epilog=constants.EPILOG)
@click.option(
    "--log-level",
    "-L",
    default="INFO",
    type=click.Choice(
        ["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"],
        case_sensitive=False,
    ),
)
@click.version_option(constants.VERSION, "--version", "-v", "-V")
def main(log_level: str):
    if not constants.CONFIG_FILE_PATH.exists():
        log.error(
            f"Configuration not found. '{constants.CONFIG_FILE_PATH}' doesn't exist."
        )
        sys.exit(1)

    log.remove()
    log.add(sys.stderr, level=log_level)


@main.group(short_help="manage the HTML page (open, update)")
def html():
    pass


@html.command("open", help="open the HTML page on your default web browser.")
@click.option("--update/--no-update", " /-N", is_flag=True, default=True)
@click.pass_context
def html_open(ctx: click.Context, update: bool):
    import webbrowser

    if update:
        ctx.invoke(html_update)

    webbrowser.open_new_tab(str(core.get_html_path()))


@html.command("update", help="update the HTML page with latest information.")
def html_update():
    import json

    from chameleon import PageTemplate

    template = PageTemplate(constants.TEMPLATE_PATH.read_text())
    char_data: list[dict[str, str]] = []

    for path in core.get_chars_path().glob("*.json"):
        with open(path, "r") as file:
            data: dict[str, str] = json.load(file)
            if data["status"] != "OK":
                continue
            char_data.append(data)

    chars = list(
        c["character"]
        for c in sorted(
            char_data,
            key=lambda x: x["last_viewed"],
            reverse=constants.CONFIG["html"]["SORTING"].strip().casefold() == "newest",
        )
    )

    with open(core.get_html_path(), "w") as file:
        file.write(template(chars=chars))

    log.info(f"generated index.html with {len(chars)} characters")


@main.group(short_help="manage characters index (update)")
def chars():
    pass


@chars.command(help="update the characters index with latest information.")
@click.pass_context
def update(ctx: click.Context):
    import ast
    import json
    import random
    import time
    from collections import deque
    from concurrent.futures import ThreadPoolExecutor, as_completed

    CHARS_PATH = core.get_chars_path()
    BATCH_SIZE = int(constants.CONFIG["fetch"]["BATCH_SIZE"])
    SLEEP_RANGE = ast.literal_eval(constants.CONFIG["fetch"]["SLEEP_RANGE"])

    files = list(CHARS_PATH.glob("*.json"))
    filtered_urls: dict[str, tuple[str, ...]] = {}

    for path in core.get_history_file_paths_gecko():
        filtered_urls |= core.get_filtered_urls_gecko(path)

    for path in core.get_history_file_paths_chromium():
        filtered_urls |= core.get_filtered_urls_chromium(path)

    core.update_last_viewed(files, filtered_urls)
    core.discard_existing_chars(files, filtered_urls)

    with ThreadPoolExecutor(max_workers=BATCH_SIZE) as executor:
        pending = deque(filtered_urls.keys())
        batch_num = 0

        while pending:
            batch_num += 1
            batch = [pending.popleft() for _ in range(min(BATCH_SIZE, len(pending)))]
            log.info(f"processing batch {batch_num}")

            futures = [executor.submit(core.get_char_info, cid) for cid in batch]

            for future in as_completed(futures):
                char_id, res = future.result()

                if res.status_code == 429:
                    log.warning("rate limited, rescheduling", char_id)
                    log.info("sleeping for", SLEEP_RANGE[1], "seconds")
                    pending.append(char_id)
                    time.sleep(SLEEP_RANGE[1])
                    continue
                elif res.status_code != 200:
                    log.error(f"For {char_id=} got {res.status_code=}")
                    continue

                data: dict[str, str] = res.json()  # type: ignore
                data["last_viewed"] = filtered_urls[char_id][1]

                with open(CHARS_PATH / f"{char_id}.json", "w") as f:
                    json.dump(data, f, indent=4)

                log.info(
                    f"saved {char_id=} (name={({} if not isinstance(data, dict) else data).get('character', {}).get('name')})"  # type: ignore
                )

            if batch_num % int(constants.CONFIG["fetch"]["HTML_GEN_INTERVAL"]) == 0:
                html_update.invoke(ctx)

            log.success(
                f"batch {batch_num} done ({len(pending)}/{len(filtered_urls)} | {1 - len(pending)/len(filtered_urls):.2%})",
                end="\n\n",
            )

            if pending:
                seconds = random.randint(*SLEEP_RANGE)
                log.info(f"sleeping {seconds}s")
                time.sleep(seconds)


@main.command(short_help="show helpful information")
def info():
    def show_info(key: str, value: object):
        print(f"{key:>26} :: {value}")

    show_info("Package Name", constants.PACKAGE_NAME)
    show_info("Package Description", constants.DESCRIPTION)
    show_info("Package Version", constants.VERSION)
    show_info("Log Path", core.get_log_path())
    _logs = list(core.get_log_path().glob("*.log"))
    show_info(
        "Latest Log",
        "%s (%d in total)" % (max(_logs, key=lambda p: p.stat().st_mtime), len(_logs)),
    )
    show_info("Configuration Directory", constants.CONFIG_DIR)
    show_info("Configuration File", constants.CONFIG_FILE_PATH)
    show_info("Token", constants.CONFIG["auth"]["TOKEN"])
    show_info("Character Index Directory", core.get_chars_path())
    show_info(
        "Character Index Size",
        "%d JSON files" % len(list(core.get_chars_path().glob("*.json"))),
    )
    show_info("HTML File", core.get_html_path())
    show_info(
        "Chromium History Files", list(map(str, core.get_history_file_paths_chromium()))
    )
    show_info(
        "Gecko History Files", list(map(str, core.get_history_file_paths_gecko()))
    )

    for n, line in enumerate(constants.CONFIG_FILE_PATH.read_text().splitlines()):
        show_info("Configuration File Content" if n == 0 else "", line)
