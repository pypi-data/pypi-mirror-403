from blueness.argparse.generic import main

from bluer_ai import NAME, VERSION, DESCRIPTION, ICON
from bluer_ai.README import build
from bluer_ai.logger import logger


main(
    ICON=ICON,
    NAME=NAME,
    DESCRIPTION=DESCRIPTION,
    VERSION=VERSION,
    main_filename=__file__,
    tasks={
        "build_README": lambda _: build.build(),
    },
    logger=logger,
)
