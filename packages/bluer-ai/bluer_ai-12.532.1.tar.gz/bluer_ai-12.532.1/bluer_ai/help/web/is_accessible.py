from typing import List

from bluer_options.terminal import show_usage

args = [
    "[--timeout 3]",
]


def help_is_accessible(
    tokens: List[str],
    mono: bool,
) -> str:

    return show_usage(
        [
            "@web",
            "is_accessible",
            "<url>",
        ]
        + args,
        "is <url> accessible?",
        mono=mono,
    )
