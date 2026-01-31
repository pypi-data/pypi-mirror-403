from typing import List

from bluer_options.terminal import show_usage, xtra
from bluer_ai.help.web import is_accessible


def help_identify(
    tokens: List[str],
    mono: bool,
) -> str:
    options = "".join(
        [
            xtra("count=<count>,~log,", mono=mono),
            "loop",
            xtra(",seconds=<seconds>", mono=mono),
        ]
    )

    identification_options = xtra("timestamp", mono=mono)

    args = is_accessible.args

    return show_usage(
        [
            "@web",
            "identify",
            f"[{options}]",
            f"[{identification_options}]",
        ]
        + args,
        "identify web connection.",
        mono=mono,
    )
