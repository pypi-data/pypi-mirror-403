import argparse

from blueness import module
from blueness.argparse.generic import sys_exit

from bluer_options import NAME
from bluer_options.web.access import as_str as access_as_str
from bluer_options.logger import logger

NAME = module.name(__file__, NAME)

list_of_tasks = ["access_as_str"]

parser = argparse.ArgumentParser(NAME)
parser.add_argument(
    "task",
    type=str,
    help=" | ".join(list_of_tasks),
)
parser.add_argument(
    "--timestamp",
    type=int,
    default=0,
    help="0|1",
)
parser.add_argument(
    "--emoji",
    type=int,
    default=1,
    help="0|1",
)
args = parser.parse_args()

success = args.task in list_of_tasks
if args.task == "access_as_str":
    print(
        access_as_str(
            emoji=args.emoji == 1,
            timestamp=args.timestamp == 1,
        )
    )
else:
    success = None

sys_exit(logger, NAME, args.task, success)
