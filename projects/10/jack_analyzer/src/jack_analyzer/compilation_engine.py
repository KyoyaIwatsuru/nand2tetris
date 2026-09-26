from .const import Identifier, Tokens, TokenType, escape_xml
from .jack_tokenizer import JackTokenizer


class CompilationEngine:
    def __init__(self, filepath):
        self.wf = open(filepath[:-5] + ".myImpl.xml", "w")
        self.tokenizer = JackTokenizer(filepath)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.wf.close()

    def compileClass(self):
        self.write_element_start("class")

        self.compile_keyword([Tokens.CLASS])
        self.compile_class_name()
        self.compile_symbol(Tokens.LEFT_CURLY_BRACKET)

        while self.next_is_class_var_dec():
            self.compileClassVarDec()

        while self.next_is_subroutine_dec():
            self.compileSubroutine()

        self.compile_symbol(Tokens.RIGHT_CURLY_BRACKET)

        self.write_element_end("class")

    def compileClassVarDec(self):
        self.write_element_start("classVarDec")

        self.compile_keyword([Tokens.STATIC, Tokens.FIELD])
        self.compile_type()
        self.compile_var_name()

        while self.next_is(Tokens.COMMA):
            self.compile_symbol(Tokens.COMMA)
            self.compile_var_name()

        self.compile_symbol(Tokens.SEMI_COLON)

        self.write_element_end("classVarDec")

    def compile_type(self):
        if self.next_is([Tokens.INT, Tokens.CHAR, Tokens.BOOLEAN]):
            self.compile_keyword([Tokens.INT, Tokens.CHAR, Tokens.BOOLEAN])
        elif isinstance(self.tokenizer.see_next(), Identifier):
            self.compile_identifier()
        else:
            self.advance_token()
            self.raise_unexpected("a type")

    def compileSubroutine(self):
        self.write_element_start("subroutineDec")

        self.compile_keyword(
            [Tokens.CONSTRUCTOR, Tokens.FUNCTION, Tokens.METHOD]
        )
        if self.tokenizer.see_next() == Tokens.VOID:
            self.compile_keyword(Tokens.VOID)
        else:
            self.compile_type()
        self.compile_subroutine_name()
        self.compile_symbol(Tokens.LEFT_ROUND_BRACKET)
        self.compileParameterList()
        self.compile_symbol(Tokens.RIGHT_ROUND_BRACKET)
        self.compileSubroutineBody()

        self.write_element_end("subroutineDec")

    def compileParameterList(self):
        self.write_element_start("parameterList")

        if self.tokenizer.see_next() in [
            Tokens.INT,
            Tokens.CHAR,
            Tokens.BOOLEAN,
        ] or isinstance(self.tokenizer.see_next(), Identifier):
            self.compile_type()
            self.compile_var_name()

            while self.next_is(Tokens.COMMA):
                self.compile_symbol(Tokens.COMMA)
                self.compile_type()
                self.compile_var_name()

        self.write_element_end("parameterList")

    def compileSubroutineBody(self):
        self.write_element_start("subroutineBody")

        self.compile_symbol(Tokens.LEFT_CURLY_BRACKET)
        while self.next_is(Tokens.VAR):
            self.compileVarDec()

        self.compileStatements()
        self.compile_symbol(Tokens.RIGHT_CURLY_BRACKET)

        self.write_element_end("subroutineBody")

    def compileVarDec(self):
        self.write_element_start("varDec")
        self.compile_keyword(Tokens.VAR)
        self.compile_type()
        self.compile_var_name()
        while self.next_is(Tokens.COMMA):
            self.compile_symbol(Tokens.COMMA)
            self.compile_var_name()
        self.compile_symbol(Tokens.SEMI_COLON)
        self.write_element_end("varDec")

    def compile_class_name(self):
        self.compile_identifier()

    def compile_subroutine_name(self):
        self.compile_identifier()

    def compile_var_name(self):
        self.compile_identifier()

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
        self.compile_var_name()
        if self.next_is(Tokens.LEFT_BOX_BRACKET):
            self.compile_symbol(Tokens.LEFT_BOX_BRACKET)
            self.compileExpression()
            self.compile_symbol(Tokens.RIGHT_BOX_BRACKET)
        self.compile_symbol(Tokens.EQUAL)
        self.compileExpression()
        self.compile_symbol(Tokens.SEMI_COLON)
        self.write_element_end("letStatement")

    def compileIf(self):
        self.write_element_start("ifStatement")
        self.compile_keyword(Tokens.IF)
        self.compile_symbol(Tokens.LEFT_ROUND_BRACKET)
        self.compileExpression()
        self.compile_symbol(Tokens.RIGHT_ROUND_BRACKET)
        self.compile_symbol(Tokens.LEFT_CURLY_BRACKET)
        self.compileStatements()
        self.compile_symbol(Tokens.RIGHT_CURLY_BRACKET)
        if self.next_is(Tokens.ELSE):
            self.compile_keyword(Tokens.ELSE)
            self.compile_symbol(Tokens.LEFT_CURLY_BRACKET)
            self.compileStatements()
            self.compile_symbol(Tokens.RIGHT_CURLY_BRACKET)
        self.write_element_end("ifStatement")

    def compileWhile(self):
        self.write_element_start("whileStatement")
        self.compile_keyword(Tokens.WHILE)
        self.compile_symbol(Tokens.LEFT_ROUND_BRACKET)
        self.compileExpression()
        self.compile_symbol(Tokens.RIGHT_ROUND_BRACKET)
        self.compile_symbol(Tokens.LEFT_CURLY_BRACKET)
        self.compileStatements()
        self.compile_symbol(Tokens.RIGHT_CURLY_BRACKET)
        self.write_element_end("whileStatement")

    def compileDo(self):
        self.write_element_start("doStatement")
        self.compile_keyword(Tokens.DO)
        self.compile_subroutine_call()
        self.compile_symbol(Tokens.SEMI_COLON)
        self.write_element_end("doStatement")

    def compileReturn(self):
        self.write_element_start("returnStatement")
        self.compile_keyword(Tokens.RETURN)
        if not self.next_is(Tokens.SEMI_COLON):
            self.compileExpression()
        self.compile_symbol(Tokens.SEMI_COLON)
        self.write_element_end("returnStatement")

    def compileExpression(self):
        self.write_element_start("expression")
        self.compileTerm()
        while self.next_is(
            [
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
        ):
            self.compile_symbol(
                [
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
            )
            self.compileTerm()
        self.write_element_end("expression")

    def compileTerm(self):
        self.ensure_more_tokens()
        self.write_element_start("term")

        if self.next_type_is(TokenType.INT_CONST):
            self.compile_integer_constant()
        elif self.next_type_is(TokenType.STRING_CONST):
            self.compile_string_constant()
        elif self.next_is(
            [
                Tokens.TRUE,
                Tokens.FALSE,
                Tokens.NULL,
                Tokens.THIS,
            ]
        ):
            self.compile_keyword(
                [
                    Tokens.TRUE,
                    Tokens.FALSE,
                    Tokens.NULL,
                    Tokens.THIS,
                ]
            )
        elif self.next_type_is(TokenType.IDENTIFIER):
            if self.next_is(Tokens.LEFT_BOX_BRACKET, idx=1):
                self.compile_var_name()
                self.compile_symbol(Tokens.LEFT_BOX_BRACKET)
                self.compileExpression()
                self.compile_symbol(Tokens.RIGHT_BOX_BRACKET)
            elif self.next_is([Tokens.LEFT_ROUND_BRACKET, Tokens.DOT], idx=1):
                self.compile_subroutine_call()
            else:
                self.compile_var_name()

        elif self.next_is(Tokens.LEFT_ROUND_BRACKET):
            self.compile_symbol(Tokens.LEFT_ROUND_BRACKET)
            self.compileExpression()
            self.compile_symbol(Tokens.RIGHT_ROUND_BRACKET)
        elif self.next_is([Tokens.TILDE, Tokens.MINUS]):
            self.compile_symbol([Tokens.TILDE, Tokens.MINUS])
            self.compileTerm()
        else:
            self.advance_token()
            self.raise_unexpected("a term")
        self.write_element_end("term")

    def compile_subroutine_call(self):
        if self.next_is(Tokens.LEFT_ROUND_BRACKET, idx=1):
            self.compile_subroutine_name()
            self.compile_symbol(Tokens.LEFT_ROUND_BRACKET)
            self.compileExpressionList()
            self.compile_symbol(Tokens.RIGHT_ROUND_BRACKET)
        else:
            self.compile_identifier()
            self.compile_symbol(Tokens.DOT)
            self.compile_subroutine_name()
            self.compile_symbol(Tokens.LEFT_ROUND_BRACKET)
            self.compileExpressionList()
            self.compile_symbol(Tokens.RIGHT_ROUND_BRACKET)

    def compileExpressionList(self):
        self.write_element_start("expressionList")
        if not self.next_is(Tokens.RIGHT_ROUND_BRACKET):
            self.compileExpression()
            while self.next_is(Tokens.COMMA):
                self.compile_symbol(Tokens.COMMA)
                self.compileExpression()
        self.write_element_end("expressionList")

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
        else:
            self.raise_unexpected(self.quoted(tokens))

    def compile_integer_constant(self):
        self.advance_token()
        if self.tokenizer.tokenType() == TokenType.INT_CONST:
            self.write_element("integerConstant", self.tokenizer.intVal())
        else:
            self.raise_unexpected("an integer constant")

    def compile_string_constant(self):
        self.advance_token()
        if self.tokenizer.tokenType() == TokenType.STRING_CONST:
            self.write_element("stringConstant", self.tokenizer.stringVal())
        else:
            self.raise_unexpected("a string constant")

    def compile_identifier(self):
        self.advance_token()
        if self.tokenizer.tokenType() == TokenType.IDENTIFIER:
            self.write_element("identifier", self.tokenizer.identifier())
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
