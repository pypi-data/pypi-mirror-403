#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
bakcode package entry point
"""
from __future__ import print_function
import argparse
from .packer import do_pack
from .revealer import do_reveal


def main():
    p = argparse.ArgumentParser(description="bakcode: pack directory to HEX parts and reveal back.")
    g = p.add_mutually_exclusive_group(required=True)

    g.add_argument("-p", "--pack", nargs=3, metavar=("INPUT_DIR", "OUTPUT_DIR", "SIZE"),
                   help="디렉토리를 HEX 파츠로 분할")
    g.add_argument("-r", "--reveal", nargs=2, metavar=("INPUT_DIR", "OUTPUT_DIR"),
                   help="HEX 파츠를 복원하여 최종 결과를 OUTPUT_DIR 로 생성")
    args = p.parse_args()

    if args.pack:
        in_dir, out_dir, size_str = args.pack
        do_pack(in_dir, out_dir, size_str)
    elif args.reveal:
        in_dir, out_dir = args.reveal
        do_reveal(in_dir, out_dir)


if __name__ == "__main__":
    main()
