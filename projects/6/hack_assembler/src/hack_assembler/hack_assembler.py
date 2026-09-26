import argparse
import os.path
import re

from . import code
from .parser import A_INSTRUCTION, C_INSTRUCTION, L_INSTRUCTION, Parser
from .symbol_table import SymbolTable

symbol_pattern = re.compile(r"([0-9]+)|([a-zA-Z_.$:][a-zA-Z0-9_.$:]*)")


def main():
    parser = argparse.ArgumentParser(
        description="Assemble a Hack .asm file into a .hack file."
    )
    parser.add_argument("asm_file", type=str, help="path to the .asm file")

    args = parser.parse_args()
    asm_file = args.asm_file

    save_file = os.path.splitext(asm_file)[0] + ".hack"

    st = SymbolTable()

    with Parser(asm_file) as p:
        op_address = 0

        while p.hasMoreLines():
            p.advance()
            instruction_type = p.instructionType()
            if (
                instruction_type == A_INSTRUCTION
                or instruction_type == C_INSTRUCTION
            ):
                op_address += 1
            elif instruction_type == L_INSTRUCTION:
                label = p.symbol()
                m = symbol_pattern.fullmatch(label)
                if m is None or m.group(2) is None:
                    raise Exception(f"Invalid label: {label}")
                st.addEntry(label, op_address)

    with Parser(asm_file) as p:
        with open(save_file, "w") as wf:
            while p.hasMoreLines():
                p.advance()
                instruction_type = p.instructionType()

                if instruction_type == A_INSTRUCTION:
                    symbol = p.symbol()
                    m = symbol_pattern.fullmatch(symbol)
                    if m is None:
                        raise Exception(f"Invalid symbol: {symbol}")

                    if m.group(1):
                        bincode = "0" + int2bin(int(m.group(1)), 15)
                    elif m.group(2):
                        symbol = m.group(2)
                        if st.contains(symbol):
                            address = st.getAddress(symbol)
                            bincode = "0" + int2bin(address, 15)
                        else:
                            st.addVariable(symbol)
                            address = st.getAddress(symbol)
                            bincode = "0" + int2bin(address, 15)

                elif instruction_type == C_INSTRUCTION:
                    bincode = (
                        "111"
                        + code.comp(p.comp())
                        + code.dest(p.dest())
                        + code.jump(p.jump())
                    )

                if instruction_type != L_INSTRUCTION:
                    wf.write(bincode + "\n")


def int2bin(value, bit_num):
    bin_value = bin(value)[2:]
    if len(bin_value) > bit_num:
        raise Exception("Over binary size")
    return "0" * (bit_num - len(bin_value)) + bin_value


if __name__ == "__main__":
    main()
