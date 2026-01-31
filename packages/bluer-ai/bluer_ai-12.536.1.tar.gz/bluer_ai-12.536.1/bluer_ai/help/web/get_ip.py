from typing import List

from bluer_options.terminal import show_usage


def help_get_ip(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@web",
            "get_ip",
        ],
        "get IP.",
        mono=mono,
    )
