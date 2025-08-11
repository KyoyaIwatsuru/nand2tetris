from constants import C_POP, C_PUSH, POINTER_BASE_ADDRESS, TEMP_BASE_ADDRESS


class CodeWriter:
    def __init__(self, filepath):
        self.f = open(filepath, "w")
        self.if_label_num = 0
        self.return_label_num = 0
        self.current_function_name = "init"

        self.write_init()

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.f.close()

    def set_file_name(self, file_name):
        self.current_translated_file_name = file_name

    def write_arithmetic(self, command):
        if command in ["add", "sub", "and", "or"]:
            self.write_binary_operation(command)
        elif command in ["neg", "not"]:
            self.write_unary_operation(command)
        elif command in ["eq", "gt", "lt"]:
            self.write_comp_operation(command)

    def write_push_pop(self, command, segment, index):
        index = int(index)

        if command == C_PUSH:
            if segment == "constant":
                self.write_codes(["@%d" % index, "D=A"])
                self.write_push_from_d_register()
            elif segment in ["local", "argument", "this", "that"]:
                self.write_push_from_virtual_segment(segment, index)
            elif segment in ["temp", "pointer"]:
                self.write_push_from_static_segment(segment, index)
            if segment == "static":
                self.write_codes(
                    [
                        "@%s.%d" % (self.current_translated_file_name, index),
                    ]
                )
                self.write_code("D=M")
                self.write_push_from_d_register()

        elif command == C_POP:
            if segment in ["local", "argument", "this", "that"]:
                self.write_pop_from_virtual_segment(segment, index)
            elif segment in ["temp", "pointer"]:
                self.write_pop_from_static_segment(segment, index)
            if segment == "static":
                self.write_pop_to_m_register()
                self.write_codes(
                    [
                        "D=M",
                        "@%s.%d" % (self.current_translated_file_name, index),
                    ]
                )
                self.write_code("M=D")

    def write_label(self, label):
        self.write_code("(%s)" % self.get_label_name(label))

    def write_goto(self, label):
        self.write_codes(["@%s" % self.get_label_name(label), "0;JMP"])

    def write_if(self, label):
        self.write_pop_to_m_register()
        self.write_codes(["D=M", "@%s" % self.get_label_name(label), "D;JNE"])

    def write_function(self, function_name, num_of_vars):
        self.write_codes(["(%s)" % function_name, "D=0"])
        for i in range(int(num_of_vars)):
            self.write_push_from_d_register()

        self.current_function_name = function_name

    def write_call(self, function_name, num_of_args):
        return_label = self.get_new_return_label()
        self.write_codes(["// return-label", "@%s" % return_label, "D=A"])
        self.write_push_from_d_register()
        self.write_codes(
            [
                "@LCL",
                "D=M",
            ]
        )
        self.write_push_from_d_register()
        self.write_codes(
            [
                "@ARG",
                "D=M",
            ]
        )
        self.write_push_from_d_register()
        self.write_codes(
            [
                "@THIS",
                "D=M",
            ]
        )
        self.write_push_from_d_register()
        self.write_codes(
            [
                "@THAT",
                "D=M",
            ]
        )
        self.write_push_from_d_register()

        self.write_codes(
            [
                "@SP",
                "D=M",
                "@5",
                "D=D-A",
                "@%d" % int(num_of_args),
                "D=D-A",
                "@ARG",
                "M=D",
                "@SP",
                "D=M",
                "@LCL",
                "M=D",
            ]
        )

        self.write_codes(
            [
                "@%s" % function_name,
                "0;JMP",
                "(%s)" % return_label,
            ]
        )

    def write_return(self):
        self.write_codes(
            [
                "@LCL",
                "D=M",
                "@R13",
                "M=D",
                "@5",
                "D=A",
                "@R13",
                "A=M-D",
                "D=M",
                "@R14",
                "M=D",
            ]
        )
        self.write_pop_to_m_register()
        self.write_codes(
            [
                "D=M",
                "@ARG",
                "A=M",
                "M=D",
                "@ARG",
                "D=M+1",
                "@SP",
                "M=D",
                "@R13",
                "AM=M-1",
                "D=M",
                "@THAT",
                "M=D",
                "@R13",
                "AM=M-1",
                "D=M",
                "@THIS",
                "M=D",
                "@R13",
                "AM=M-1",
                "D=M",
                "@ARG",
                "M=D",
                "@R13",
                "AM=M-1",
                "D=M",
                "@LCL",
                "M=D",
                "@R14",
                "A=M",
                "0;JMP",
            ]
        )

    def write_init(self):
        self.write_set_sp(256)
        self.write_call("Sys.init", 0)

    def write_set_sp(self, address):
        self.write_codes(["@%d" % address, "D=A", "@SP", "M=D"])

    def write_binary_operation(self, command):
        self.write_pop_to_m_register()
        self.write_code("D=M")
        self.write_pop_to_m_register()
        if command == "add":
            self.write_code("D=D+M")
        elif command == "sub":
            self.write_code("D=M-D")
        elif command == "and":
            self.write_code("D=D&M")
        elif command == "or":
            self.write_code("D=D|M")
        self.write_push_from_d_register()

    def write_unary_operation(self, command):
        self.write_codes(
            [
                "@SP",
                "A=M-1",
            ]
        )
        if command == "neg":
            self.write_code("M=-M")
        elif command == "not":
            self.write_code("M=!M")

    def write_comp_operation(self, command):
        self.write_pop_to_m_register()
        self.write_code("D=M")
        self.write_pop_to_m_register()
        l1 = self.get_new_if_label()
        l2 = self.get_new_if_label()
        if command == "eq":
            comp_type = "JEQ"
        elif command == "gt":
            comp_type = "JGT"
        elif command == "lt":
            comp_type = "JLT"
        self.write_codes(
            [
                "D=M-D",
                "@%s" % l1,
                "D;%s" % comp_type,
                "D=0",
                "@%s" % l2,
                "0;JMP",
                "(%s)" % l1,
                "D=-1",
                "(%s)" % l2,
            ]
        )
        self.write_push_from_d_register()

    def write_push_from_virtual_segment(self, segment, index):
        if segment == "local":
            register_name = "LCL"
        elif segment == "argument":
            register_name = "ARG"
        elif segment == "this":
            register_name = "THIS"
        elif segment == "that":
            register_name = "THAT"
        self.write_codes(["@%s" % register_name, "A=M"])
        for i in range(index):
            self.write_code("A=A+1")
        self.write_code("D=M")
        self.write_push_from_d_register()

    def write_pop_from_virtual_segment(self, segment, index):
        if segment == "local":
            register_name = "LCL"
        elif segment == "argument":
            register_name = "ARG"
        elif segment == "this":
            register_name = "THIS"
        elif segment == "that":
            register_name = "THAT"
        self.write_pop_to_m_register()
        self.write_codes(["D=M", "@%s" % register_name, "A=M"])
        for i in range(index):
            self.write_code("A=A+1")
        self.write_code("M=D")

    def write_push_from_static_segment(self, segment, index):
        if segment == "temp":
            base_address = TEMP_BASE_ADDRESS
        elif segment == "pointer":
            base_address = POINTER_BASE_ADDRESS
        self.write_codes(
            [
                "@%d" % base_address,
            ]
        )
        for i in range(index):
            self.write_code("A=A+1")
        self.write_code("D=M")
        self.write_push_from_d_register()

    def write_pop_from_static_segment(self, segment, index):
        if segment == "temp":
            base_address = TEMP_BASE_ADDRESS
        elif segment == "pointer":
            base_address = POINTER_BASE_ADDRESS
        self.write_pop_to_m_register()
        self.write_codes(
            [
                "D=M",
                "@%d" % base_address,
            ]
        )
        for i in range(index):
            self.write_code("A=A+1")
        self.write_code("M=D")

    def write_push_from_d_register(self):
        self.write_codes(["@SP", "A=M", "M=D", "@SP", "M=M+1"])

    def write_pop_to_m_register(self):
        self.write_codes(["@SP", "M=M-1", "A=M"])

    def get_new_if_label(self):
        self.if_label_num += 1
        return "_IF_LABEL_" + str(self.if_label_num)

    def get_label_name(self, label):
        try:
            return "%s$%s" % (self.current_function_name, label)
        except AttributeError:
            return "%s$%s" % ("null", label)

    def get_new_return_label(self):
        self.return_label_num += 1
        return "%s$ret.%d" % (
            self.current_function_name,
            self.return_label_num,
        )

    def write_code(self, code):
        self.f.write(code + "\n")

    def write_codes(self, codes):
        self.write_code("\n".join(codes))

    def close(self):
        self.f.close()

    def _write_infinite_loop(self):
        self.write_codes(["(END)", "@END", "0;JMP"])
