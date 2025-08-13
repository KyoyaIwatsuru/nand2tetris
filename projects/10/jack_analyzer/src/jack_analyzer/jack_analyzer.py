#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import glob

from compilation_engine import CompilationEngine


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=str, help="source file or directory")

    args = parser.parse_args()
    path = args.path

    if path.endswith(".jack"):
        compile(path)

    else:
        if path.endswith("/"):
            path = path[:-1]
        files = glob.glob("%s/*" % path)
        for filepath in files:
            if filepath.endswith(".jack"):
                compile(filepath)


def compile(filepath):
    with CompilationEngine(filepath) as ce:
        print("compiling %s ..." % filepath)
        ce.compile()


if __name__ == "__main__":
    main()
