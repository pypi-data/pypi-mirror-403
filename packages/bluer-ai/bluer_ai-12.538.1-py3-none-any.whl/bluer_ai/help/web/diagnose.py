from typing import List

from bluer_options.terminal import show_usage, xtra


def help_diagnose(
    tokens: List[str],
    mono: bool,
) -> str:
    options = xtra("Sion,Zagros", mono=mono)

    return show_usage(
        [
            "@web",
            "diagnose",
            f"[{options}]",
        ],
        "diagnose web connection.",
        mono=mono,
    )
