import argparse


from blueness import module
from blueness.argparse.generic import sys_exit

from bluer_ai import NAME
from bluer_ai.plugins.web.accessible import is_accessible
from bluer_ai.logger import logger

NAME = module.name(__file__, NAME)

parser = argparse.ArgumentParser(NAME)
parser.add_argument(
    "task",
    type=str,
    help="is_accessible",
)
parser.add_argument(
    "--count",
    type=int,
    default=-1,
    help="-1: forever",
)
parser.add_argument(
    "--log",
    type=int,
    default=-1,
    help="0 | 1",
)
parser.add_argument(
    "--loop",
    type=int,
    default=0,
    help="0 | 1",
)
parser.add_argument(
    "--object_name",
    type=str,
    default="",
)
parser.add_argument(
    "--sleep",
    type=int,
    default=5,
    help="in seconds",
)
parser.add_argument(
    "--timeout",
    type=int,
    default=3,
    help="in seconds",
)
parser.add_argument(
    "--timestamp",
    type=int,
    default=0,
    help="0 | 1",
)
parser.add_argument(
    "--url",
    type=str,
)
args = parser.parse_args()

success = False
if args.task == "is_accessible":
    success = True
    print(
        int(
            is_accessible(
                args.url,
                timeout=args.timeout,
            )
        )
    )
else:
    success = None

sys_exit(logger, NAME, args.task, success)
