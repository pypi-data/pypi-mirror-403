from typing import List

from bluer_options.terminal import show_usage


def help_where_am_i(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@web",
            "where_am_i",
        ],
        "where am I?",
        mono=mono,
    )
