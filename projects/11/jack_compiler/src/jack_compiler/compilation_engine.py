from .const import (
    Command,
    Identifier,
    IdentifierKind,
    Segment,
    Tokens,
    TokenType,
    escape_xml,
)
from .jack_tokenizer import JackTokenizer
from .symbol_table import SymbolTable


class CompilationEngine:
    def __init__(self, filepath, vm_writer):
        self.wf = open(filepath[:-5] + ".myImpl.xml", "w")
        self.tokenizer = JackTokenizer(filepath)
        self.symbol_table = SymbolTable()
        self.vm_writer = vm_writer
        self.class_name = None
        self.label_num = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.wf.close()

    def compileClass(self):
        self.write_element_start("class")

        self.compile_keyword([Tokens.CLASS])
        self.class_name = self.compile_class_name()
        self.compile_symbol(Tokens.LEFT_CURLY_BRACKET)

        while self.next_is_class_var_dec():
            self.compileClassVarDec()

        while self.next_is_subroutine_dec():
            self.compileSubroutine()

        self.compile_symbol(Tokens.RIGHT_CURLY_BRACKET)

        self.write_element_end("class")

    def compileClassVarDec(self):
        self.write_element_start("classVarDec")

        kind_token = self.compile_keyword([Tokens.STATIC, Tokens.FIELD])
        kind = (
            IdentifierKind.STATIC
            if kind_token == Tokens.STATIC
            else IdentifierKind.FIELD
        )
        var_type = self.compile_type()
        self.compile_var_name(kind=kind, var_type=var_type)

        while self.next_is(Tokens.COMMA):
            self.compile_symbol(Tokens.COMMA)
            self.compile_var_name(kind=kind, var_type=var_type)

        self.compile_symbol(Tokens.SEMI_COLON)

        self.write_element_end("classVarDec")

    def compile_type(self):
        if self.next_is([Tokens.INT, Tokens.CHAR, Tokens.BOOLEAN]):
            keyword = self.compile_keyword(
                [Tokens.INT, Tokens.CHAR, Tokens.BOOLEAN]
            )
            return keyword.token
        elif isinstance(self.tokenizer.see_next(), Identifier):
            return self.compile_class_name()
        else:
            self.advance_token()
            self.raise_unexpected("a type")

    def compileSubroutine(self):
        self.write_element_start("subroutineDec")

        subroutine_kind = self.compile_keyword(
            [Tokens.CONSTRUCTOR, Tokens.FUNCTION, Tokens.METHOD]
        )
        if self.tokenizer.see_next() == Tokens.VOID:
            self.compile_keyword(Tokens.VOID)
        else:
            self.compile_type()
        subroutine_name = self.compile_subroutine_name()

        self.symbol_table.reset()
        if subroutine_kind == Tokens.METHOD:
            self.symbol_table.define(
                "this", self.class_name, IdentifierKind.ARG
            )

        self.compile_symbol(Tokens.LEFT_ROUND_BRACKET)
        self.compileParameterList()
        self.compile_symbol(Tokens.RIGHT_ROUND_BRACKET)
        self.compileSubroutineBody(subroutine_name, subroutine_kind)

        self.write_element_end("subroutineDec")

    def compileParameterList(self):
        self.write_element_start("parameterList")

        if self.tokenizer.see_next() in [
            Tokens.INT,
            Tokens.CHAR,
            Tokens.BOOLEAN,
        ] or isinstance(self.tokenizer.see_next(), Identifier):
            var_type = self.compile_type()
            self.compile_var_name(kind=IdentifierKind.ARG, var_type=var_type)

            while self.next_is(Tokens.COMMA):
                self.compile_symbol(Tokens.COMMA)
                var_type = self.compile_type()
                self.compile_var_name(
                    kind=IdentifierKind.ARG, var_type=var_type
                )

        self.write_element_end("parameterList")

    def compileSubroutineBody(self, subroutine_name, subroutine_kind):
        self.write_element_start("subroutineBody")

        self.compile_symbol(Tokens.LEFT_CURLY_BRACKET)
        num_locals = 0
        while self.next_is(Tokens.VAR):
            num_locals += self.compileVarDec()

        self.vm_writer.writeFunction(
            f"{self.class_name}.{subroutine_name}", num_locals
        )

        if subroutine_kind == Tokens.CONSTRUCTOR:
            self.vm_writer.writePush(
                Segment.CONST,
                self.symbol_table.varCount(IdentifierKind.FIELD),
            )
            self.vm_writer.writeCall("Memory.alloc", 1)
            self.vm_writer.writePop(Segment.POINTER, 0)
        elif subroutine_kind == Tokens.METHOD:
            self.vm_writer.writePush(Segment.ARG, 0)
            self.vm_writer.writePop(Segment.POINTER, 0)

        self.compileStatements()
        self.compile_symbol(Tokens.RIGHT_CURLY_BRACKET)

        self.write_element_end("subroutineBody")

    def compileVarDec(self):
        self.write_element_start("varDec")
        self.compile_keyword(Tokens.VAR)
        var_type = self.compile_type()
        num_vars = 0
        self.compile_var_name(kind=IdentifierKind.VAR, var_type=var_type)
        num_vars += 1
        while self.next_is(Tokens.COMMA):
            self.compile_symbol(Tokens.COMMA)
            self.compile_var_name(kind=IdentifierKind.VAR, var_type=var_type)
            num_vars += 1
        self.compile_symbol(Tokens.SEMI_COLON)
        self.write_element_end("varDec")

        return num_vars

    def compile_class_name(self):
        return self.compile_identifier()

    def compile_subroutine_name(self):
        return self.compile_identifier()

    def compile_var_name(self, kind=None, var_type=None):
        name = self.tokenizer.see_next().token
        self.compile_identifier()
        if kind is not None:
            self.symbol_table.define(name, var_type, kind)
        return name

    def compileStatements(self):
        self.write_element_start("statements")

        while self.next_is_statement():
            self.compile_statement()

        self.write_element_end("statements")

    def compile_statement(self):
        if self.next_is(Tokens.LET):
            self.compileLet()
        elif self.next_is(Tokens.IF):
            self.compileIf()
        elif self.next_is(Tokens.WHILE):
            self.compileWhile()
        elif self.next_is(Tokens.DO):
            self.compileDo()
        elif self.next_is(Tokens.RETURN):
            self.compileReturn()

    def compileLet(self):
        self.write_element_start("letStatement")
        self.compile_keyword(Tokens.LET)
        name = self.compile_var_name()

        is_array = self.next_is(Tokens.LEFT_BOX_BRACKET)
        if is_array:
            self.compile_symbol(Tokens.LEFT_BOX_BRACKET)
            self.compileExpression()
            self.compile_symbol(Tokens.RIGHT_BOX_BRACKET)
            self.write_push_variable(name)
            self.vm_writer.writeArithmetic(Command.ADD)

        self.compile_symbol(Tokens.EQUAL)
        self.compileExpression()
        self.compile_symbol(Tokens.SEMI_COLON)

        if is_array:
            self.vm_writer.writePop(Segment.TEMP, 0)
            self.vm_writer.writePop(Segment.POINTER, 1)
            self.vm_writer.writePush(Segment.TEMP, 0)
            self.vm_writer.writePop(Segment.THAT, 0)
        else:
            self.write_pop_variable(name)

        self.write_element_end("letStatement")

    def compileIf(self):
        self.write_element_start("ifStatement")
        self.compile_keyword(Tokens.IF)
        self.compile_symbol(Tokens.LEFT_ROUND_BRACKET)
        self.compileExpression()
        self.compile_symbol(Tokens.RIGHT_ROUND_BRACKET)

        self.vm_writer.writeArithmetic(Command.NOT)
        label_else = self.get_new_label()
        label_end = self.get_new_label()
        self.vm_writer.writeIf(label_else)

        self.compile_symbol(Tokens.LEFT_CURLY_BRACKET)
        self.compileStatements()
        self.compile_symbol(Tokens.RIGHT_CURLY_BRACKET)
        self.vm_writer.writeGoto(label_end)
        self.vm_writer.writeLabel(label_else)

        if self.next_is(Tokens.ELSE):
            self.compile_keyword(Tokens.ELSE)
            self.compile_symbol(Tokens.LEFT_CURLY_BRACKET)
            self.compileStatements()
            self.compile_symbol(Tokens.RIGHT_CURLY_BRACKET)
        self.vm_writer.writeLabel(label_end)

        self.write_element_end("ifStatement")

    def compileWhile(self):
        self.write_element_start("whileStatement")

        label_top = self.get_new_label()
        label_end = self.get_new_label()
        self.vm_writer.writeLabel(label_top)

        self.compile_keyword(Tokens.WHILE)
        self.compile_symbol(Tokens.LEFT_ROUND_BRACKET)
        self.compileExpression()
        self.compile_symbol(Tokens.RIGHT_ROUND_BRACKET)
        self.vm_writer.writeArithmetic(Command.NOT)
        self.vm_writer.writeIf(label_end)

        self.compile_symbol(Tokens.LEFT_CURLY_BRACKET)
        self.compileStatements()
        self.compile_symbol(Tokens.RIGHT_CURLY_BRACKET)
        self.vm_writer.writeGoto(label_top)
        self.vm_writer.writeLabel(label_end)

        self.write_element_end("whileStatement")

    def compileDo(self):
        self.write_element_start("doStatement")
        self.compile_keyword(Tokens.DO)
        self.compile_subroutine_call()
        self.compile_symbol(Tokens.SEMI_COLON)

        self.vm_writer.writePop(Segment.TEMP, 0)

        self.write_element_end("doStatement")

    def compileReturn(self):
        self.write_element_start("returnStatement")
        self.compile_keyword(Tokens.RETURN)
        if not self.next_is(Tokens.SEMI_COLON):
            self.compileExpression()
        else:
            self.vm_writer.writePush(Segment.CONST, 0)
        self.compile_symbol(Tokens.SEMI_COLON)

        self.vm_writer.writeReturn()

        self.write_element_end("returnStatement")

    def compileExpression(self):
        self.write_element_start("expression")
        self.compileTerm()

        operators = [
            Tokens.PLUS,
            Tokens.MINUS,
            Tokens.MULTI,
            Tokens.DIV,
            Tokens.AND,
            Tokens.PIPE,
            Tokens.LESS_THAN,
            Tokens.GREATER_THAN,
            Tokens.EQUAL,
        ]
        while self.next_is(operators):
            op = self.compile_symbol(operators)
            self.compileTerm()
            self.write_operator(op)

        self.write_element_end("expression")

    def compileTerm(self):
        self.ensure_more_tokens()
        self.write_element_start("term")

        if self.next_type_is(TokenType.INT_CONST):
            value = self.compile_integer_constant()
            self.vm_writer.writePush(Segment.CONST, value)
        elif self.next_type_is(TokenType.STRING_CONST):
            value = self.compile_string_constant()
            self.write_push_string(value)
        elif self.next_is(
            [Tokens.TRUE, Tokens.FALSE, Tokens.NULL, Tokens.THIS]
        ):
            keyword = self.compile_keyword(
                [Tokens.TRUE, Tokens.FALSE, Tokens.NULL, Tokens.THIS]
            )
            self.write_keyword_constant(keyword)
        elif self.next_type_is(TokenType.IDENTIFIER):
            if self.next_is(Tokens.LEFT_BOX_BRACKET, idx=1):
                name = self.compile_var_name()
                self.compile_symbol(Tokens.LEFT_BOX_BRACKET)
                self.compileExpression()
                self.compile_symbol(Tokens.RIGHT_BOX_BRACKET)
                self.write_push_variable(name)
                self.vm_writer.writeArithmetic(Command.ADD)
                self.vm_writer.writePop(Segment.POINTER, 1)
                self.vm_writer.writePush(Segment.THAT, 0)
            elif self.next_is([Tokens.LEFT_ROUND_BRACKET, Tokens.DOT], idx=1):
                self.compile_subroutine_call()
            else:
                name = self.compile_var_name()
                self.write_push_variable(name)

        elif self.next_is(Tokens.LEFT_ROUND_BRACKET):
            self.compile_symbol(Tokens.LEFT_ROUND_BRACKET)
            self.compileExpression()
            self.compile_symbol(Tokens.RIGHT_ROUND_BRACKET)
        elif self.next_is([Tokens.TILDE, Tokens.MINUS]):
            op = self.compile_symbol([Tokens.TILDE, Tokens.MINUS])
            self.compileTerm()
            if op == Tokens.TILDE:
                self.vm_writer.writeArithmetic(Command.NOT)
            else:
                self.vm_writer.writeArithmetic(Command.NEG)
        else:
            self.advance_token()
            self.raise_unexpected("a term")
        self.write_element_end("term")

    def compile_subroutine_call(self):
        if self.next_is(Tokens.LEFT_ROUND_BRACKET, idx=1):
            subroutine_name = self.compile_subroutine_name()
            self.compile_symbol(Tokens.LEFT_ROUND_BRACKET)
            self.vm_writer.writePush(Segment.POINTER, 0)
            num_args = self.compileExpressionList()
            self.compile_symbol(Tokens.RIGHT_ROUND_BRACKET)
            self.vm_writer.writeCall(
                f"{self.class_name}.{subroutine_name}", num_args + 1
            )
        else:
            first_name = self.tokenizer.see_next().token
            if self.symbol_table.kindOf(first_name) is not None:
                var_name = self.compile_var_name()
                self.compile_symbol(Tokens.DOT)
                subroutine_name = self.compile_subroutine_name()
                self.compile_symbol(Tokens.LEFT_ROUND_BRACKET)
                self.write_push_variable(var_name)
                num_args = self.compileExpressionList()
                self.compile_symbol(Tokens.RIGHT_ROUND_BRACKET)
                class_name = self.symbol_table.typeOf(var_name)
                self.vm_writer.writeCall(
                    f"{class_name}.{subroutine_name}", num_args + 1
                )
            else:
                class_name = self.compile_class_name()
                self.compile_symbol(Tokens.DOT)
                subroutine_name = self.compile_subroutine_name()
                self.compile_symbol(Tokens.LEFT_ROUND_BRACKET)
                num_args = self.compileExpressionList()
                self.compile_symbol(Tokens.RIGHT_ROUND_BRACKET)
                self.vm_writer.writeCall(
                    f"{class_name}.{subroutine_name}", num_args
                )

    def compileExpressionList(self):
        self.write_element_start("expressionList")
        num_args = 0
        if not self.next_is(Tokens.RIGHT_ROUND_BRACKET):
            self.compileExpression()
            num_args += 1
            while self.next_is(Tokens.COMMA):
                self.compile_symbol(Tokens.COMMA)
                self.compileExpression()
                num_args += 1
        self.write_element_end("expressionList")

        return num_args

    def write_operator(self, op):
        if op == Tokens.PLUS:
            self.vm_writer.writeArithmetic(Command.ADD)
        elif op == Tokens.MINUS:
            self.vm_writer.writeArithmetic(Command.SUB)
        elif op == Tokens.MULTI:
            self.vm_writer.writeCall("Math.multiply", 2)
        elif op == Tokens.DIV:
            self.vm_writer.writeCall("Math.divide", 2)
        elif op == Tokens.AND:
            self.vm_writer.writeArithmetic(Command.AND)
        elif op == Tokens.PIPE:
            self.vm_writer.writeArithmetic(Command.OR)
        elif op == Tokens.LESS_THAN:
            self.vm_writer.writeArithmetic(Command.LT)
        elif op == Tokens.GREATER_THAN:
            self.vm_writer.writeArithmetic(Command.GT)
        elif op == Tokens.EQUAL:
            self.vm_writer.writeArithmetic(Command.EQ)

    def write_keyword_constant(self, keyword):
        if keyword == Tokens.TRUE:
            self.vm_writer.writePush(Segment.CONST, 0)
            self.vm_writer.writeArithmetic(Command.NOT)
        elif keyword in (Tokens.FALSE, Tokens.NULL):
            self.vm_writer.writePush(Segment.CONST, 0)
        elif keyword == Tokens.THIS:
            self.vm_writer.writePush(Segment.POINTER, 0)

    def write_push_string(self, value):
        self.vm_writer.writePush(Segment.CONST, len(value))
        self.vm_writer.writeCall("String.new", 1)
        for char in value:
            self.vm_writer.writePush(Segment.CONST, ord(char))
            self.vm_writer.writeCall("String.appendChar", 2)

    def write_push_variable(self, name):
        self.vm_writer.writePush(
            self.segment_of(name), self.symbol_table.indexOf(name)
        )

    def write_pop_variable(self, name):
        self.vm_writer.writePop(
            self.segment_of(name), self.symbol_table.indexOf(name)
        )

    def segment_of(self, name):
        kind = self.symbol_table.kindOf(name)
        if kind == IdentifierKind.STATIC:
            return Segment.STATIC
        elif kind == IdentifierKind.FIELD:
            return Segment.THIS
        elif kind == IdentifierKind.ARG:
            return Segment.ARG
        elif kind == IdentifierKind.VAR:
            return Segment.LOCAL
        else:
            raise Exception(f"Unknown variable: {name}")

    def get_new_label(self):
        self.label_num += 1
        return f"LABEL_{self.label_num}"

    def next_is_class_var_dec(self):
        return self.next_is([Tokens.STATIC, Tokens.FIELD])

    def next_type_is(self, token_type):
        return self.tokenizer.see_next().type == token_type

    def next_is_subroutine_dec(self):
        return self.next_is(
            [Tokens.CONSTRUCTOR, Tokens.FUNCTION, Tokens.METHOD]
        )

    def next_is_statement(self):
        return self.next_is(
            [Tokens.LET, Tokens.IF, Tokens.WHILE, Tokens.DO, Tokens.RETURN]
        )

    def next_is(self, tokens, idx=0):
        if isinstance(tokens, list):
            return self.tokenizer.see_next(idx=idx) in tokens
        else:
            return self.tokenizer.see_next(idx=idx) == tokens

    def ensure_more_tokens(self):
        if not self.tokenizer.hasMoreTokens():
            self.raise_syntax_error("unexpected end of file")

    def advance_token(self):
        self.ensure_more_tokens()
        self.tokenizer.advance()

    def as_list(self, tokens):
        return tokens if isinstance(tokens, list) else [tokens]

    def compile_keyword(self, tokens):
        self.advance_token()
        if (
            self.tokenizer.tokenType() == TokenType.KEYWORD
            and self.tokenizer.keyWord() in self.as_list(tokens)
        ):
            self.write_element("keyword", self.tokenizer.keyWord().token)
            return self.tokenizer.keyWord()
        else:
            self.raise_unexpected(self.quoted(tokens))

    def compile_symbol(self, tokens):
        self.advance_token()
        expected = [token.token for token in self.as_list(tokens)]
        if (
            self.tokenizer.tokenType() == TokenType.SYMBOL
            and self.tokenizer.symbol() in expected
        ):
            self.write_element("symbol", self.tokenizer.symbol())
            return self.tokenizer.current_token
        else:
            self.raise_unexpected(self.quoted(tokens))

    def compile_integer_constant(self):
        self.advance_token()
        if self.tokenizer.tokenType() == TokenType.INT_CONST:
            self.write_element("integerConstant", self.tokenizer.intVal())
            return self.tokenizer.intVal()
        else:
            self.raise_unexpected("an integer constant")

    def compile_string_constant(self):
        self.advance_token()
        if self.tokenizer.tokenType() == TokenType.STRING_CONST:
            self.write_element("stringConstant", self.tokenizer.stringVal())
            return self.tokenizer.stringVal()
        else:
            self.raise_unexpected("a string constant")

    def compile_identifier(self):
        self.advance_token()
        if self.tokenizer.tokenType() == TokenType.IDENTIFIER:
            self.write_element("identifier", self.tokenizer.identifier())
            return self.tokenizer.identifier()
        else:
            self.raise_unexpected("an identifier")

    def write_element(self, elem_name, value):
        text = escape_xml(value)
        self.wf.write(f"<{elem_name}> {text} </{elem_name}>\n")

    def write_element_start(self, elem_name):
        self.wf.write(f"<{elem_name}>\n")

    def write_element_end(self, elem_name):
        self.wf.write(f"</{elem_name}>\n")

    def quoted(self, tokens):
        return " or ".join(
            f"'{token.token}'" for token in self.as_list(tokens)
        )

    def current_text(self):
        kind = self.tokenizer.tokenType()
        if kind == TokenType.KEYWORD:
            text = self.tokenizer.keyWord().token
        elif kind == TokenType.SYMBOL:
            text = self.tokenizer.symbol()
        elif kind == TokenType.IDENTIFIER:
            text = self.tokenizer.identifier()
        elif kind == TokenType.INT_CONST:
            text = self.tokenizer.intVal()
        else:
            return f'"{self.tokenizer.stringVal()}"'
        return f"'{text}'"

    def raise_unexpected(self, expected):
        line = self.tokenizer.current_token_line()
        self.raise_syntax_error(
            f"expected {expected} but found {self.current_text()}"
            f" at line {line}"
        )

    def raise_syntax_error(self, msg):
        raise Exception(msg)
