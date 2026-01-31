from typing import List

from bluer_options.terminal import show_usage

from bluer_ai import env


def help_open(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@web",
            "open",
        ],
        f"open the web object ({env.BLUER_AI_WEB_OBJECT}).",
        mono=mono,
    )
