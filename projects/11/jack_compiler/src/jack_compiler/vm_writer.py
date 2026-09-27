from .const import Command, Segment


class VMWriter:
    def __init__(self, filepath):
        self.f = open(filepath, "w")

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.f.close()

    def writePush(self, segment, index):
        self.write_code(f"push {self.get_segment_str(segment)} {index}")

    def writePop(self, segment, index):
        self.write_code(f"pop {self.get_segment_str(segment)} {index}")

    def writeArithmetic(self, command):
        self.write_code(self.get_command_str(command))

    def writeLabel(self, label):
        self.write_code(f"label {label}")

    def writeGoto(self, label):
        self.write_code(f"goto {label}")

    def writeIf(self, label):
        self.write_code(f"if-goto {label}")

    def writeCall(self, name, num_args):
        self.write_code(f"call {name} {num_args}")

    def writeFunction(self, name, num_locals):
        self.write_code(f"function {name} {num_locals}")

    def writeReturn(self):
        self.write_code("return")

    def write_code(self, code):
        self.f.write(code + "\n")

    def get_segment_str(self, segment):
        if segment == Segment.CONST:
            return "constant"
        elif segment == Segment.ARG:
            return "argument"
        elif segment == Segment.LOCAL:
            return "local"
        elif segment == Segment.STATIC:
            return "static"
        elif segment == Segment.THIS:
            return "this"
        elif segment == Segment.THAT:
            return "that"
        elif segment == Segment.POINTER:
            return "pointer"
        elif segment == Segment.TEMP:
            return "temp"
        else:
            raise Exception(f"Unknown segment: {segment}")

    def get_command_str(self, command):
        if command == Command.ADD:
            return "add"
        elif command == Command.SUB:
            return "sub"
        elif command == Command.NEG:
            return "neg"
        elif command == Command.EQ:
            return "eq"
        elif command == Command.GT:
            return "gt"
        elif command == Command.LT:
            return "lt"
        elif command == Command.AND:
            return "and"
        elif command == Command.OR:
            return "or"
        elif command == Command.NOT:
            return "not"
        else:
            raise Exception(f"Unknown command: {command}")

    def close(self):
        self.f.close()
