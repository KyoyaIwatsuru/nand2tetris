#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import glob
import os.path

from code_writer import CodeWriter
from constants import (
    C_ARITHMETIC,
    C_CALL,
    C_FUNCTION,
    C_GOTO,
    C_IF,
    C_LABEL,
    C_POP,
    C_PUSH,
    C_RETURN,
)
from parser import Parser


def main():
    parser = argparse.ArgumentParser(description="Process some integers.")
    parser.add_argument("path", type=str, help="vm file or folder")

    args = parser.parse_args()
    path = args.path

    if path.endswith(".vm"):
        with CodeWriter(path[:-3] + ".asm") as code_writer:
            translate_file(path, code_writer)
            code_writer._write_infinite_loop()
        print("Translated to", path[:-3] + ".asm")
    else:
        if path.endswith("/"):
            path = path[:-1]
        with CodeWriter(
            path + "/" + os.path.basename(path) + ".asm"
        ) as code_writer:
            files = glob.glob("%s/*" % path)
            for file in files:
                if file.endswith(".vm"):
                    translate_file(file, code_writer)
            code_writer._write_infinite_loop()
        print("Translated to", path + "/" + os.path.basename(path) + ".asm")


def translate_file(file, code_writer):
    filename, _ = os.path.splitext(os.path.basename(file))
    code_writer.set_file_name(filename)
    with Parser(file) as parser:
        while parser.hasMoreLines():
            parser.advance()
            code_writer.write_code("// " + " ".join(parser.current_command))

            if parser.commandType() == C_ARITHMETIC:
                code_writer.write_arithmetic(parser.arg1())
            elif parser.commandType() == C_PUSH:
                code_writer.write_push_pop(
                    C_PUSH, parser.arg1(), parser.arg2()
                )
            elif parser.commandType() == C_POP:
                code_writer.write_push_pop(C_POP, parser.arg1(), parser.arg2())
            elif parser.commandType() == C_LABEL:
                code_writer.write_label(parser.arg1())
            elif parser.commandType() == C_GOTO:
                code_writer.write_goto(parser.arg1())
            elif parser.commandType() == C_IF:
                code_writer.write_if(parser.arg1())
            elif parser.commandType() == C_FUNCTION:
                code_writer.write_function(parser.arg1(), parser.arg2())
            elif parser.commandType() == C_CALL:
                code_writer.write_call(parser.arg1(), parser.arg2())
            elif parser.commandType() == C_RETURN:
                code_writer.write_return()


if __name__ == "__main__":
    main()
