#!/usr/bin/env python3

import argparse
from pathlib import Path

import arklog

from robotransform import Store, dump_aadl


def main():
    parser = argparse.ArgumentParser(description="RoboTransform CLI.")
    parser.add_argument(
        "path",
        type=Path,
        help="Path to a rct file."
    )
    args = parser.parse_args()

    if args.path.exists():
        arklog.debug(f"Path exists: ({args.path}).")
        store = Store((args.path,))
        arklog.info(dump_aadl(store))
    else:
        arklog.debug(f"Path does not exist: ({args.path.resolve()}).")


if __name__ == "__main__":
    main()
