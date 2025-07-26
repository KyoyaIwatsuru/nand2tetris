import re

A_INSTRUCTION = 0
C_INSTRUCTION = 1
L_INSTRUCTION = 2

A_INSTRUCTION_PATTERN = re.compile(r"@([0-9a-zA-Z_\.\$:]+)")
L_INSTRUCTION_PATTERN = re.compile(r"\(([0-9a-zA-Z_\.\$:]*)\)")
C_INSTRUCTION_PATTERN = re.compile(r"(?:(A?M?D?)=)?([^;]+)(?:;(.+))?")


class Parser:
    def __init__(self, filepath):
        self.current_instruction = None
        self.f_hack = open(filepath)

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.f_hack.close()

    def hasMoreLines(self):
        current_pos = self.f_hack.tell()
        line = self.f_hack.readline()
        self.f_hack.seek(current_pos)
        return bool(line)

    def advance(self):
        while True:
            line = self.f_hack.readline()
            if not line:
                self.current_instruction = None
                break

            line_trimmed = line.strip().replace(" ", "")
            comment_i = line_trimmed.find("//")
            if comment_i != -1:
                line_trimmed = line_trimmed[:comment_i]

            if line_trimmed != "":
                self.current_instruction = line_trimmed
                break

    def instructionType(self):
        if self.current_instruction[0] == "@":
            return A_INSTRUCTION
        elif self.current_instruction[0] == "(":
            return L_INSTRUCTION
        else:
            return C_INSTRUCTION

    def symbol(self):
        instruction_type = self.instructionType()
        if instruction_type == A_INSTRUCTION:
            m = A_INSTRUCTION_PATTERN.match(self.current_instruction)
            if not m:
                raise Exception("Parsing symbol failed")
            return m.group(1)

        elif instruction_type == L_INSTRUCTION:
            m = L_INSTRUCTION_PATTERN.match(self.current_instruction)
            if not m:
                raise Exception("Parsing symbol failed")
            return m.group(1)
        else:
            raise Exception(
                "Current instruction is not A_INSTRUCTION or L_INSTRUCTION"
            )

    def dest(self):
        instruction_type = self.instructionType()
        if instruction_type == C_INSTRUCTION:
            m = C_INSTRUCTION_PATTERN.match(self.current_instruction)
            return m.group(1)
        else:
            raise Exception("Current instruction is not C_INSTRUCTION")

    def comp(self):
        instruction_type = self.instructionType()
        if instruction_type == C_INSTRUCTION:
            m = C_INSTRUCTION_PATTERN.match(self.current_instruction)
            return m.group(2)
        else:
            raise Exception("Current instruction is not C_INSTRUCTION")

    def jump(self):
        instruction_type = self.instructionType()
        if instruction_type == C_INSTRUCTION:
            m = C_INSTRUCTION_PATTERN.match(self.current_instruction)
            return m.group(3)
        else:
            raise Exception("Current instruction is not C_INSTRUCTION")
