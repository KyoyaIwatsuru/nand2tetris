from .const import IdentifierKind


class Symbol:
    def __init__(self, var_type, kind, index):
        self.type = var_type
        self.kind = kind
        self.index = index


class SymbolTable:
    def __init__(self):
        self.static_table = {}
        self.field_table = {}
        self.arg_table = {}
        self.var_table = {}

    def reset(self):
        self.arg_table = {}
        self.var_table = {}

    def define(self, name, var_type, kind):
        table = self._table_for(kind)
        table[name] = Symbol(var_type, kind, len(table))

    def varCount(self, kind):
        return len(self._table_for(kind))

    def kindOf(self, name):
        symbol = self._find(name)
        return symbol.kind if symbol else None

    def typeOf(self, name):
        return self._find(name).type

    def indexOf(self, name):
        return self._find(name).index

    def _table_for(self, kind):
        if kind == IdentifierKind.STATIC:
            return self.static_table
        elif kind == IdentifierKind.FIELD:
            return self.field_table
        elif kind == IdentifierKind.ARG:
            return self.arg_table
        elif kind == IdentifierKind.VAR:
            return self.var_table
        else:
            raise Exception(f"Unknown kind: {kind}")

    def _find(self, name):
        for table in (
            self.arg_table,
            self.var_table,
            self.field_table,
            self.static_table,
        ):
            if name in table:
                return table[name]
        return None
