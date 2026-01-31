from typing import List

from bluer_options.terminal import show_usage, xtra

from bluer_ai import env


def help_share(
    tokens: List[str],
    mono: bool,
) -> str:
    options = "download,~open,~receive,~send,upload"

    port_options = xtra(
        "port.receive.=<{}>,port.send=<{}>".format(
            env.BLUER_AI_WEB_RECEIVE_PORT,
            env.BLUER_AI_WEB_SEND_PORT,
        ),
        mono=mono,
    )

    return show_usage(
        [
            "@web",
            "share",
            f"[{options}]",
            f"[{env.BLUER_AI_WEB_OBJECT}|<object-name>]",
            f"[{port_options}]",
        ],
        "share <object-name>.",
        mono=mono,
    )
