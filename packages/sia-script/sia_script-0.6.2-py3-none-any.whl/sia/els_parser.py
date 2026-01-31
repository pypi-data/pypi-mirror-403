"""
SIA ENTERPRISE LOGIC STUDIO - PARSER MODULE
===========================================
Parser and AST definitions with strict ABAP semantics.
Connected to els_core.py runtime.
"""

import re
from typing import List, Dict, Any, Optional, Union, Tuple, Callable

# =====================================================
# ===============     AST DEFINITIONS    ==============
# =====================================================

class ASTNode:
    """Base class for all AST nodes"""
    pass


class Program(ASTNode):
    """Root program node"""
    
    def __init__(self, statements: List[ASTNode]):
        self.statements = statements
    
    def __repr__(self):
        return f"Program({len(self.statements)} statements)"


# ----- Structure Definitions -----

class TypesBeginOf(ASTNode):
    """TYPES BEGIN OF structure"""
    
    def __init__(self, name: str, components: List[Tuple[str, str, Optional[int]]]):
        self.name = name
        self.components = components  # (field_name, type_name, length)
    
    def __repr__(self):
        return f"TypesBeginOf({self.name}, {len(self.components)} fields)"


class DataBeginOf(ASTNode):
    """DATA BEGIN OF structure variable"""
    
    def __init__(self, name: str, components: List[Tuple[str, str, Optional[int], Optional[ASTNode]]]):
        self.name = name
        self.components = components  # (field_name, type_name, length, value)
    
    def __repr__(self):
        return f"DataBeginOf({self.name})"


# ----- Control Breaks (NEW!) -----

class AtNew(ASTNode):
    """AT NEW control break"""
    
    def __init__(self, field: str, body: List[ASTNode]):
        self.field = field
        self.body = body
    
    def __repr__(self):
        return f"AtNew({self.field})"


class AtEndOf(ASTNode):
    """AT END OF control break"""
    
    def __init__(self, field: str, body: List[ASTNode]):
        self.field = field
        self.body = body
    
    def __repr__(self):
        return f"AtEndOf({self.field})"


# ----- Data Declaration -----

class DataDecl(ASTNode):
    """DATA statement with LENGTH support"""
    
    def __init__(self, name: str, type_spec: Optional[str] = None, 
                 length: Optional[int] = None, value: Optional[ASTNode] = None):
        self.name = name
        self.type_spec = type_spec
        self.length = length
        self.value = value
    
    def __repr__(self):
        length_str = f" LENGTH {self.length}" if self.length else ""
        return f"DataDecl({self.name}, TYPE {self.type_spec}{length_str})"


class ConstantDecl(ASTNode):
    """CONSTANTS statement"""
    
    def __init__(self, name: str, type_spec: Optional[str] = None,
                 length: Optional[int] = None, value: Optional[ASTNode] = None):
        self.name = name
        self.type_spec = type_spec
        self.length = length
        self.value = value
    
    def __repr__(self):
        return f"ConstantDecl({self.name})"


class ParameterDecl(ASTNode):
    """PARAMETERS statement"""
    
    def __init__(self, name: str, type_spec: Optional[str] = None,
                 length: Optional[int] = None, default: Optional[ASTNode] = None):
        self.name = name
        self.type_spec = type_spec
        self.length = length
        self.default = default
    
    def __repr__(self):
        return f"ParameterDecl({self.name})"


class SelectOptionsDecl(ASTNode):
    """SELECT-OPTIONS statement"""
    
    def __init__(self, selname: str, for_var: str, type_spec: Optional[str] = None,
                 length: Optional[int] = None):
        self.selname = selname
        self.for_var = for_var
        self.type_spec = type_spec
        self.length = length
    
    def __repr__(self):
        return f"SelectOptionsDecl({self.selname} FOR {self.for_var})"


# ----- Subroutines -----

class FormDecl(ASTNode):
    """FORM definition"""
    
    def __init__(self, name: str, params: List[Tuple[str, str]],  # (name, kind)
                 body: List[ASTNode]):
        self.name = name
        self.params = params  # 'USING' or 'CHANGING'
        self.body = body
    
    def __repr__(self):
        return f"FormDecl({self.name}, {len(self.params)} params)"


class Perform(ASTNode):
    """PERFORM statement"""
    
    def __init__(self, name: str, using_params: List[ASTNode] = None,
                 changing_params: List[ASTNode] = None):
        self.name = name
        self.using_params = using_params or []
        self.changing_params = changing_params or []
    
    def __repr__(self):
        return f"Perform({self.name})"


class EndForm(ASTNode):
    """ENDFORM marker"""
    
    def __repr__(self):
        return "EndForm()"


# ----- Events -----

class StartOfSelection(ASTNode):
    """START-OF-SELECTION event"""
    
    def __repr__(self):
        return "StartOfSelection()"


# ----- Statements -----

class Write(ASTNode):
    """WRITE statement"""
    
    def __init__(self, items: List[ASTNode]):
        self.items = items
    
    def __repr__(self):
        return f"Write({len(self.items)} items)"


class Assign(ASTNode):
    """Assignment statement"""
    
    def __init__(self, target: ASTNode, expr: ASTNode):
        self.target = target
        self.expr = expr
    
    def __repr__(self):
        return f"Assign({self.target} = {self.expr})"


class Clear(ASTNode):
    """CLEAR statement"""
    
    def __init__(self, targets: List[ASTNode]):
        self.targets = targets
    
    def __repr__(self):
        return f"Clear({len(self.targets)} targets)"


class Move(ASTNode):
    """MOVE statement"""
    
    def __init__(self, source: ASTNode, target: ASTNode):
        self.source = source
        self.target = target
    
    def __repr__(self):
        return f"Move({self.source} -> {self.target})"


class Append(ASTNode):
    """APPEND VALUE #(...) TO itab"""
    
    def __init__(self, source_row: Dict[str, ASTNode], target_table: str):
        self.source_row = source_row
        self.target_table = target_table
    
    def __repr__(self):
        return f"Append(structured -> {self.target_table})"


class AppendSimple(ASTNode):
    """APPEND wa TO itab"""
    
    def __init__(self, source_var: str, target_table: str):
        self.source_var = source_var
        self.target_table = target_table
    
    def __repr__(self):
        return f"AppendSimple({self.source_var} -> {self.target_table})"


class ModifyTable(ASTNode):
    """MODIFY TABLE itab FROM wa"""
    
    def __init__(self, table_name: str, from_var: str, key_field: Optional[str] = None):
        self.table_name = table_name
        self.from_var = from_var
        self.key_field = key_field
    
    def __repr__(self):
        return f"ModifyTable({self.table_name} FROM {self.from_var})"


class DeleteTable(ASTNode):
    """DELETE TABLE itab"""
    
    def __init__(self, table_name: str, key: Optional[Tuple[str, ASTNode]] = None):
        self.table_name = table_name
        self.key = key
    
    def __repr__(self):
        return f"DeleteTable({self.table_name})"


class InsertTable(ASTNode):
    """INSERT wa INTO TABLE itab"""
    
    def __init__(self, source_var: str, target_table: str):
        self.source_var = source_var
        self.target_table = target_table
    
    def __repr__(self):
        return f"InsertTable({self.source_var} -> {self.target_table})"


class ReadTable(ASTNode):
    """READ TABLE itab INTO wa WITH KEY ..."""
    
    def __init__(self, table_name: str, into: Optional[str] = None, 
                 key: Optional[Tuple[str, ASTNode]] = None, transporting: Optional[List[str]] = None):
        self.table_name = table_name
        self.into = into
        self.key = key
        self.transporting = transporting
    
    def __repr__(self):
        return f"ReadTable({self.table_name} -> {self.into})"


# ----- SQL Operations -----

class UpdateSQL(ASTNode):
    """UPDATE db_table SET ... WHERE ..."""
    
    def __init__(self, table_name: str, set_clause: Dict[str, ASTNode],
                 where_clause: Optional[ASTNode] = None):
        self.table_name = table_name
        self.set_clause = set_clause
        self.where = where_clause
    
    def __repr__(self):
        return f"UpdateSQL({self.table_name})"


class InsertSQL(ASTNode):
    """INSERT INTO db_table VALUES ..."""
    
    def __init__(self, table_name: str, values: Dict[str, ASTNode]):
        self.table_name = table_name
        self.values = values
    
    def __repr__(self):
        return f"InsertSQL({self.table_name})"


class DeleteSQL(ASTNode):
    """DELETE FROM db_table WHERE ..."""
    
    def __init__(self, table_name: str, where_clause: Optional[ASTNode] = None):
        self.table_name = table_name
        self.where = where_clause
    
    def __repr__(self):
        return f"DeleteSQL({self.table_name})"


class CommitWork(ASTNode):
    """COMMIT WORK statement"""
    
    def __repr__(self):
        return "CommitWork()"


class RollbackWork(ASTNode):
    """ROLLBACK WORK statement"""
    
    def __repr__(self):
        return "RollbackWork()"


class SelectInto(ASTNode):
    """SELECT statement with enhanced WHERE and ORDER BY"""
    
    def __init__(self, fields: List[str], table_name: str, 
                 into_table: str, where_clause: Optional[ASTNode] = None,
                 order_by: Optional[List[str]] = None):
        self.fields = fields
        self.table_name = table_name
        self.into_table = into_table
        self.where = where_clause
        self.order_by = order_by or []
    
    def __repr__(self):
        order_str = f" ORDER BY {self.order_by}" if self.order_by else ""
        return f"SelectInto({self.table_name} -> {self.into_table}{order_str})"


# ----- Loop Control -----

class Exit(ASTNode):
    """EXIT statement"""
    
    def __init__(self, from_loop: bool = True):
        self.from_loop = from_loop
    
    def __repr__(self):
        return "Exit()"


class Continue(ASTNode):
    """CONTINUE statement"""
    
    def __repr__(self):
        return "Continue()"


class Check(ASTNode):
    """CHECK statement"""
    
    def __init__(self, condition: ASTNode):
        self.condition = condition
    
    def __repr__(self):
        return f"Check({self.condition})"


class LoopAt(ASTNode):
    """LOOP AT itab INTO wa"""
    
    def __init__(self, table: str, into: str, body: List[ASTNode]):
        self.table = table
        self.into = into
        self.body = body
    
    def __repr__(self):
        return f"LoopAt({self.table} -> {self.into})"


class EndLoop(ASTNode):
    """ENDLOOP marker"""
    
    def __repr__(self):
        return "EndLoop()"


# ----- Control Structures -----

class If(ASTNode):
    """IF statement"""
    
    def __init__(self, cond: ASTNode, then_body: List[ASTNode], 
                 elif_list: List[Tuple[ASTNode, List[ASTNode]]], 
                 else_body: List[ASTNode]):
        self.cond = cond
        self.then_body = then_body
        self.elif_list = elif_list
        self.else_body = else_body
    
    def __repr__(self):
        return f"If(cond={self.cond})"


class While(ASTNode):
    """WHILE statement"""
    
    def __init__(self, cond: ASTNode, body: List[ASTNode]):
        self.cond = cond
        self.body = body
    
    def __repr__(self):
        return f"While(cond={self.cond})"


class Do(ASTNode):
    """DO statement"""
    
    def __init__(self, times_expr: Optional[ASTNode], body: List[ASTNode]):
        self.times_expr = times_expr
        self.body = body
    
    def __repr__(self):
        return f"Do(times={self.times_expr})"


class Case(ASTNode):
    """CASE statement"""
    
    def __init__(self, expr: ASTNode, cases: List[Tuple[ASTNode, List[ASTNode]]], 
                 others_body: List[ASTNode]):
        self.expr = expr
        self.cases = cases
        self.others_body = others_body
    
    def __repr__(self):
        return f"Case(expr={self.expr}, {len(self.cases)} cases)"


# ----- Expressions -----

class Var(ASTNode):
    """Variable reference"""
    
    def __init__(self, name: str):
        self.name = name
    
    def __repr__(self):
        return f"Var({self.name})"


class Number(ASTNode):
    """Numeric literal"""
    
    def __init__(self, val: str):
        self.val = int(val)
    
    def __repr__(self):
        return f"Number({self.val})"


class String(ASTNode):
    """String literal"""
    
    def __init__(self, val: str):
        self.val = val.strip("'").replace("''", "'")
    
    def __repr__(self):
        return f"String('{self.val}')"


class Field(ASTNode):
    """Field access: wa-field"""
    
    def __init__(self, struct: str, field: str):
        self.struct = struct
        self.field = field
    
    def __repr__(self):
        return f"Field({self.struct}-{self.field})"


class BinOp(ASTNode):
    """Binary operation"""
    
    def __init__(self, left: ASTNode, op: str, right: ASTNode):
        self.left = left
        self.op = op
        self.right = right
    
    def __repr__(self):
        return f"BinOp({self.left} {self.op} {self.right})"


class UnaryOp(ASTNode):
    """Unary operation"""
    
    def __init__(self, op: str, operand: ASTNode):
        self.op = op
        self.operand = operand
    
    def __repr__(self):
        return f"UnaryOp({self.op} {self.operand})"


class FuncCall(ASTNode):
    """Function call"""
    
    def __init__(self, name: str, args: List[ASTNode]):
        self.name = name.upper()
        self.args = args
    
    def __repr__(self):
        return f"FuncCall({self.name})"


# =====================================================
# ===============   LEXICAL ANALYSIS   ================
# =====================================================

class Token:
    """Lexical token with position information"""
    
    def __init__(self, kind: str, value: str, line: int, col: int):
        self.kind = kind
        self.value = value
        self.line = line
        self.col = col
    
    def __repr__(self):
        return f"Token({self.kind}, '{self.value}', line={self.line}, col={self.col})"


# ABAP keywords (strict) - Added AT NEW, AT END OF
ABAP_KEYWORDS = [
    # Data declaration
    "DATA", "TYPES", "TYPE", "LIKE", "CONSTANTS", "VALUE", "LENGTH",
    "PARAMETERS", "SELECT-OPTIONS", "FOR", "DEFAULT",
    
    # Control structures
    "IF", "ELSEIF", "ELSE", "ENDIF",
    "CASE", "WHEN", "OTHERS", "ENDCASE",
    "WHILE", "ENDWHILE",
    "DO", "TIMES", "ENDDO",
    "LOOP", "AT", "INTO", "ENDLOOP",
    
    # Control breaks (NEW!)
    "NEW", "END", "OF",
    
    # Data manipulation
    "WRITE", "CLEAR", "MOVE",
    "APPEND", "INSERT", "MODIFY", "DELETE",
    "READ", "TABLE", "WITH", "KEY",
    
    # Loop control
    "EXIT", "CONTINUE", "CHECK",
    
    # Structure definitions
    "BEGIN", "OF", "END", "OF",
    
    # SQL
    "SELECT", "FROM", "WHERE", "INTO", "ORDER", "BY",
    "UPDATE", "SET", "COMMIT", "WORK", "ROLLBACK",
    
    # Subroutines
    "FORM", "PERFORM", "USING", "CHANGING", "ENDFORM",
    
    # Events
    "START-OF-SELECTION",
    
    # OOP
    "CREATE", "OBJECT", "CLASS", "DEFINITION", "IMPLEMENTATION",
    "PUBLIC", "SECTION", "PRIVATE", "PROTECTED", "ENDCLASS",
    "CALL", "METHOD", "EXPORTING", "IMPORTING", "CHANGING",
    "RETURNING", "ME",
    
    # Logical operators
    "AND", "OR", "NOT",
    
    # System
    "SY-SUBRC", "SY-TABIX", "SY-INDEX", "SY-DBCNT", "SY-DATUM", "SY-UZEIT"
]


# Token patterns (order matters!)
TOKEN_PATTERNS = [
    ("STRING",   r"'([^']|'')*'"),  # Handle escaped quotes
    ("NUMBER",   r"\b\d+\b"),
    ("KEYWORD",  r"(?<!\w)(" + "|".join(map(re.escape, ABAP_KEYWORDS)) + r")(?!\w)"),
    ("ID",       r"[A-Za-z_][A-Za-z0-9_\-]*"),
    ("SYMBOL",   r"->|==|!=|<=|>=|:=|[-+*/=().,:<>]"),
    ("NEWLINE",  r"\n"),
    ("SKIP",     r"[ \t\r]+"),
    ("COMMENT",  r"\*.*?$|\".*?$"),
]


TOKEN_REGEX = re.compile(
    "|".join(f"(?P<{name}>{regex})" for name, regex in TOKEN_PATTERNS),
    re.MULTILINE | re.IGNORECASE
)


def tokenize_abap(src: str) -> List[Token]:
    """Convert ABAP source into tokens with strict ABAP mode"""
    tokens = []
    line = 1
    col = 1
    
    for m in TOKEN_REGEX.finditer(src):
        kind = m.lastgroup
        value = m.group()
        
        if kind == "NEWLINE":
            line += 1
            col = 1
            continue
        
        if kind == "SKIP":
            col += len(value)
            continue
        
        if kind == "COMMENT":
            col += len(value)
            continue
        
        # Normalize keywords to uppercase
        if kind == "KEYWORD":
            value = value.upper()
        
        # Normalize identifiers to lowercase
        elif kind == "ID":
            value = value.lower()
        
        tok = Token(kind, value, line, col)
        tokens.append(tok)
        col += len(value)
    
    return tokens


# =====================================================
# ===============      PARSER         ================
# =====================================================

class ParserError(Exception):
    """Parser error exception"""
    pass


class Parser:
    """Base parser with strict ABAP expression parsing"""
    
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.in_boolean_context = False
    
    def peek(self) -> Optional[Token]:
        """Look at current token without consuming it"""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None
    
    def next(self) -> Optional[Token]:
        """Consume and return current token"""
        tok = self.peek()
        if tok:
            self.pos += 1
        return tok
    
    def accept(self, kind_or_value: str) -> Optional[Token]:
        """Accept token if it matches kind or value"""
        tok = self.peek()
        if tok and (tok.kind == kind_or_value or tok.value == kind_or_value):
            self.pos += 1
            return tok
        return None
    
    def expect(self, kind_or_value: str) -> Token:
        """Expect token of given kind or value, raise error if not found"""
        tok = self.peek()
        if not tok or (tok.kind != kind_or_value and tok.value != kind_or_value):
            raise ParserError(
                f"Expected {kind_or_value}, got {tok} at line {tok.line if tok else 'EOF'}"
            )
        self.pos += 1
        return tok
    
    def lookahead(self, value: str) -> bool:
        """Check if next token has given value"""
        tok = self.peek()
        return tok and tok.value == value
    
    def reset_context(self):
        """Reset boolean context flag"""
        self.in_boolean_context = False
    
    # --------------------------------------------
    #  Expression Parsing with strict ABAP rules
    # --------------------------------------------
    
    def parse_primary(self) -> ASTNode:
        """Parse primary expression (atoms, parentheses)"""
        tok = self.peek()
        if not tok:
            raise ParserError("Unexpected end in expression")
        
        # Number literal
        if tok.kind == "NUMBER":
            self.next()
            return Number(tok.value)
        
        # String literal
        if tok.kind == "STRING":
            self.next()
            return String(tok.value)
        
        # Identifier or Keyword
        if tok.kind in ("ID", "KEYWORD"):
            self.next()
            name = tok.value
            
            # Function call
            if self.accept("("):
                args = []
                if not self.accept(")"):
                    while True:
                        args.append(self.parse_expression())
                        if self.accept(")"):
                            break
                        self.expect(",")
                return FuncCall(name, args)
            
            # System variable
            if name.startswith("sy-"):
                return Var(name)
            
            return Var(name)
        
        # Parenthesized expression
        if self.accept("("):
            expr = self.parse_expression()
            self.expect(")")
            return expr
        
        raise ParserError(f"Unexpected token {tok} in expression")
    
    def parse_field_access(self) -> ASTNode:
        """Parse field access: var-field (only in non-expression contexts)"""
        var = self.expect("ID").value.lower()
        self.expect("-")
        field = self.expect("ID").value.lower()
        return Field(var, field)
    
    def parse_unary(self) -> ASTNode:
        """Parse unary operators - only NOT allowed in boolean context"""
        if self.accept("NOT"):
            operand = self.parse_unary()
            return UnaryOp("NOT", operand)
        return self.parse_primary()
    
    def parse_multiplicative(self) -> ASTNode:
        """Parse *, /"""
        node = self.parse_unary()
        
        while True:
            tok = self.peek()
            if tok and tok.value in ("*", "/"):
                op = self.next().value
                right = self.parse_unary()
                node = BinOp(node, op, right)
            else:
                break
        
        return node
    
    def parse_additive(self) -> ASTNode:
        """Parse +, -"""
        node = self.parse_multiplicative()
        
        while True:
            tok = self.peek()
            if tok and tok.value in ("+", "-"):
                op = self.next().value
                right = self.parse_multiplicative()
                node = BinOp(node, op, right)
            else:
                break
        
        return node
    
    def parse_comparison(self) -> ASTNode:
        """Parse comparisons: =, <>, >, <, >=, <="""  
        node = self.parse_additive()
        
        tok = self.peek()
        if tok and tok.value in ("=", "<>", ">", "<", ">=", "<="):
            op = self.next().value
            right = self.parse_additive()
            return BinOp(node, op, right)
        
        return node
    
    def parse_and(self) -> ASTNode:
        """Parse AND expressions"""
        node = self.parse_comparison()
        
        while self.accept("AND"):
            right = self.parse_comparison()
            node = BinOp(node, "AND", right)
        
        return node
    
    def parse_or(self) -> ASTNode:
        """Parse OR expressions"""
        node = self.parse_and()
        
        while self.accept("OR"):
            right = self.parse_and()
            node = BinOp(node, "OR", right)
        
        return node
    
    def parse_expression(self) -> ASTNode:
        """Top-level expression parser"""
        return self.parse_or()


class FullParser(Parser):
    """Full ABAP statement parser with all strict features including AT NEW"""
    
    def parse_program(self) -> Program:
        """Parse entire program"""
        statements = []
        
        while self.peek():
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
        
        return Program(statements)
    
    def parse_statement(self) -> Optional[ASTNode]:
        """Parse one ABAP statement (ends with '.')"""
        tok = self.peek()
        if not tok:
            return None
        
        # WRITE statement
        if tok.value == "WRITE":
            return self.parse_write_stmt()
        
        # DATA declaration
        if tok.value == "DATA":
            return self.parse_data_stmt()
        
        # TYPES BEGIN OF
        if tok.value == "TYPES" and self.lookahead("BEGIN"):
            return self.parse_types_begin_of()
        
        # DATA BEGIN OF
        if tok.value == "DATA" and self.lookahead("BEGIN"):
            return self.parse_data_begin_of()
        
        # CONSTANTS declaration
        if tok.value == "CONSTANTS":
            return self.parse_constants_stmt()
        
        # PARAMETERS declaration
        if tok.value == "PARAMETERS":
            return self.parse_parameters_stmt()
        
        # SELECT-OPTIONS declaration
        if tok.value == "SELECT-OPTIONS":
            return self.parse_select_options_stmt()
        
        # FORM definition
        if tok.value == "FORM":
            return self.parse_form()
        
        # PERFORM statement
        if tok.value == "PERFORM":
            return self.parse_perform()
        
        # START-OF-SELECTION
        if tok.value == "START-OF-SELECTION":
            return self.parse_start_of_selection()
        
        # UPDATE SQL
        if tok.value == "UPDATE":
            return self.parse_update_sql()
        
        # INSERT SQL
        if tok.value == "INSERT":
            return self.parse_insert_sql()
        
        # DELETE SQL
        if tok.value == "DELETE" and self.lookahead("FROM"):
            return self.parse_delete_sql()
        
        # COMMIT WORK
        if tok.value == "COMMIT":
            return self.parse_commit_work()
        
        # ROLLBACK WORK
        if tok.value == "ROLLBACK":
            return self.parse_rollback_work()
        
        # CLEAR statement
        if tok.value == "CLEAR":
            return self.parse_clear_stmt()
        
        # MOVE statement
        if tok.value == "MOVE":
            return self.parse_move_stmt()
        
        # APPEND statement
        if tok.value == "APPEND":
            return self.parse_append_stmt()
        
        # MODIFY statement
        if tok.value == "MODIFY":
            return self.parse_modify_stmt()
        
        # DELETE statement
        if tok.value == "DELETE":
            return self.parse_delete_stmt()
        
        # INSERT statement
        if tok.value == "INSERT":
            return self.parse_insert_stmt()
        
        # LOOP AT
        if tok.value == "LOOP":
            return self.parse_loop()
        
        # READ TABLE
        if tok.value == "READ":
            return self.parse_read_table()
        
        # AT NEW (Control break) - NEW!
        if tok.value == "AT" and self.lookahead("NEW"):
            return self.parse_at_new()
        
        # AT END OF (Control break) - NEW!
        if tok.value == "AT" and self.lookahead("END"):
            return self.parse_at_end_of()
        
        # EXIT statement
        if tok.value == "EXIT":
            return self.parse_exit_stmt()
        
        # CONTINUE statement
        if tok.value == "CONTINUE":
            return self.parse_continue_stmt()
        
        # CHECK statement
        if tok.value == "CHECK":
            return self.parse_check_stmt()
        
        # IF statement
        if tok.value == "IF":
            return self.parse_if_block()
        
        # WHILE statement
        if tok.value == "WHILE":
            return self.parse_while()
        
        # DO statement
        if tok.value == "DO":
            return self.parse_do()
        
        # CASE statement
        if tok.value == "CASE":
            return self.parse_case()
        
        # SELECT statement
        if tok.value == "SELECT":
            return self.parse_select()
        
        # Assignment (ID = expr)
        if tok.kind in ("ID", "KEYWORD") and self.lookahead("="):
            return self.parse_assignment()
        
        # Field assignment (ID-ID = expr)
        if tok.kind == "ID":
            # Check for field assignment
            if (self.pos + 2 < len(self.tokens) and 
                self.tokens[self.pos + 1].value == "-" and
                self.tokens[self.pos + 2].kind == "ID"):
                # Check if it's followed by = or .
                if (self.pos + 3 < len(self.tokens) and 
                    self.tokens[self.pos + 3].value in ("=", ".")):
                    if self.tokens[self.pos + 3].value == "=":
                        return self.parse_assignment()
        
        # Unknown statement - skip to next period
        while self.peek() and not self.accept("."):
            self.next()
        
        return None
    
    # -----------------------------------------------
    #  Enhanced Statement Parsers
    # -----------------------------------------------
    
    def parse_at_new(self) -> AtNew:
        """AT NEW field. ... ENDAT."""
        self.expect("AT")
        self.expect("NEW")
        
        field = self.expect("ID").value.lower()
        self.expect(".")
        
        body = []
        while self.peek() and not (self.peek().value == "ENDAT" or 
                                   (self.peek().value == "AT" and self.pos+1 < len(self.tokens) and 
                                    self.tokens[self.pos+1].value in ("NEW", "END"))):
            stmt = self.parse_statement()
            if stmt:
                body.append(stmt)
        
        self.expect("ENDAT")
        self.expect(".")
        
        return AtNew(field, body)
    
    def parse_at_end_of(self) -> AtEndOf:
        """AT END OF field. ... ENDAT."""
        self.expect("AT")
        self.expect("END")
        self.expect("OF")
        
        field = self.expect("ID").value.lower()
        self.expect(".")
        
        body = []
        while self.peek() and not (self.peek().value == "ENDAT" or 
                                   (self.peek().value == "AT" and self.pos+1 < len(self.tokens) and 
                                    self.tokens[self.pos+1].value in ("NEW", "END"))):
            stmt = self.parse_statement()
            if stmt:
                body.append(stmt)
        
        self.expect("ENDAT")
        self.expect(".")
        
        return AtEndOf(field, body)
    
    def parse_write_stmt(self) -> Write:
        """WRITE: expr [, expr ...]."""
        self.expect("WRITE")
        
        items = []
        self.accept(":")
        
        while self.peek() and not self.accept("."):
            if self.accept("/"):
                items.append(String("\n"))
                continue
            
            if self.accept(","):
                continue
            
            items.append(self.parse_expression())
        
        return Write(items)
    
    def parse_data_stmt(self) -> DataDecl:
        """DATA: lv_a TYPE i [LENGTH n] VALUE 10."""
        self.expect("DATA")
        self.accept(":")
        
        name = self.expect("ID").value.lower()
        
        type_spec = None
        length = None
        value_expr = None
        
        if self.accept("TYPE"):
            type_spec = self.expect("ID").value.upper()
            
            # Check for LENGTH
            if self.accept("LENGTH"):
                length_tok = self.expect("NUMBER")
                length = int(length_tok.value)
        
        if self.accept("VALUE"):
            value_expr = self.parse_expression()
        
        self.expect(".")
        return DataDecl(name, type_spec, length, value_expr)
    
    def parse_types_begin_of(self) -> TypesBeginOf:
        """TYPES BEGIN OF structure."""
        self.expect("TYPES")
        self.expect("BEGIN")
        self.expect("OF")
        
        name = self.expect("ID").value.lower()
        components = []
        
        while self.peek() and not (self.peek().value == "END" and self.pos+1 < len(self.tokens) and self.tokens[self.pos+1].value == "OF"):
            # Parse component: name TYPE type [LENGTH n]
            comp_name = self.expect("ID").value.lower()
            self.expect("TYPE")
            comp_type = self.expect("ID").value.upper()
            
            comp_length = None
            if self.accept("LENGTH"):
                length_tok = self.expect("NUMBER")
                comp_length = int(length_tok.value)
            
            components.append((comp_name, comp_type, comp_length))
            self.expect(".")
        
        self.expect("END")
        self.expect("OF")
        self.expect(".")
        
        return TypesBeginOf(name, components)
    
    def parse_data_begin_of(self) -> DataBeginOf:
        """DATA BEGIN OF structure variable."""
        self.expect("DATA")
        self.expect("BEGIN")
        self.expect("OF")
        
        name = self.expect("ID").value.lower()
        components = []
        
        while self.peek() and not (self.peek().value == "END" and self.pos+1 < len(self.tokens) and self.tokens[self.pos+1].value == "OF"):
            # Parse component with optional VALUE
            comp_name = self.expect("ID").value.lower()
            
            comp_type = None
            comp_length = None
            comp_value = None
            
            if self.accept("TYPE"):
                comp_type = self.expect("ID").value.upper()
                
                if self.accept("LENGTH"):
                    length_tok = self.expect("NUMBER")
                    comp_length = int(length_tok.value)
            
            if self.accept("VALUE"):
                comp_value = self.parse_expression()
            
            components.append((comp_name, comp_type, comp_length, comp_value))
            self.expect(".")
        
        self.expect("END")
        self.expect("OF")
        self.expect(".")
        
        return DataBeginOf(name, components)
    
    def parse_constants_stmt(self) -> ConstantDecl:
        """CONSTANTS: pi TYPE f VALUE '3.14'."""
        self.expect("CONSTANTS")
        self.accept(":")
        
        name = self.expect("ID").value.lower()
        
        type_spec = None
        length = None
        
        if self.accept("TYPE"):
            type_spec = self.expect("ID").value.upper()
            
            if self.accept("LENGTH"):
                length_tok = self.expect("NUMBER")
                length = int(length_tok.value)
        
        self.expect("VALUE")
        value_expr = self.parse_expression()
        self.expect(".")
        
        return ConstantDecl(name, type_spec, length, value_expr)
    
    def parse_parameters_stmt(self) -> ParameterDecl:
        """PARAMETERS: p_dept TYPE c LENGTH 10 DEFAULT 'IT'."""
        self.expect("PARAMETERS")
        self.accept(":")
        
        name = self.expect("ID").value.lower()
        
        type_spec = None
        length = None
        default_expr = None
        
        if self.accept("TYPE"):
            type_spec = self.expect("ID").value.upper()
            
            if self.accept("LENGTH"):
                length_tok = self.expect("NUMBER")
                length = int(length_tok.value)
        
        if self.accept("DEFAULT"):
            default_expr = self.parse_expression()
        
        self.expect(".")
        return ParameterDecl(name, type_spec, length, default_expr)
    
    def parse_select_options_stmt(self) -> SelectOptionsDecl:
        """SELECT-OPTIONS: s_salary FOR emp-salary."""
        self.expect("SELECT-OPTIONS")
        self.accept(":")
        
        selname = self.expect("ID").value.lower()
        self.expect("FOR")
        
        # Parse FOR variable (could be field or variable)
        for_var = self.expect("ID").value.lower()
        if self.accept("-"):
            field = self.expect("ID").value.lower()
            for_var = f"{for_var}-{field}"
        
        type_spec = None
        length = None
        
        if self.accept("TYPE"):
            type_spec = self.expect("ID").value.upper()
            
            if self.accept("LENGTH"):
                length_tok = self.expect("NUMBER")
                length = int(length_tok.value)
        
        self.expect(".")
        return SelectOptionsDecl(selname, for_var, type_spec, length)
    
    def parse_form(self) -> FormDecl:
        """FORM subr [USING ...] [CHANGING ...]."""
        self.expect("FORM")
        name = self.expect("ID").value.lower()
        
        params = []
        
        # Parse USING parameters
        if self.accept("USING"):
            while not self.accept("."):
                param_name = self.expect("ID").value.lower()
                params.append((param_name, "USING"))
                if self.accept(","):
                    continue
                break
        
        # Parse CHANGING parameters
        if self.accept("CHANGING"):
            while not self.accept("."):
                param_name = self.expect("ID").value.lower()
                params.append((param_name, "CHANGING"))
                if self.accept(","):
                    continue
                break
        
        self.expect(".")
        
        # Parse FORM body
        body = []
        while self.peek() and self.peek().value != "ENDFORM":
            stmt = self.parse_statement()
            if stmt:
                body.append(stmt)
        
        self.expect("ENDFORM")
        self.expect(".")
        
        return FormDecl(name, params, body)
    
    def parse_perform(self) -> Perform:
        """PERFORM subr [USING ...] [CHANGING ...]."""
        self.expect("PERFORM")
        name = self.expect("ID").value.lower()
        
        using_params = []
        changing_params = []
        
        # Parse USING parameters
        if self.accept("USING"):
            while not self.accept("."):
                using_params.append(self.parse_expression())
                if self.accept(","):
                    continue
                break
        
        # Parse CHANGING parameters
        if self.accept("CHANGING"):
            while not self.accept("."):
                changing_params.append(self.parse_expression())
                if self.accept(","):
                    continue
                break
        
        self.expect(".")
        return Perform(name, using_params, changing_params)
    
    def parse_start_of_selection(self) -> StartOfSelection:
        """START-OF-SELECTION."""
        self.expect("START-OF-SELECTION")
        self.expect(".")
        return StartOfSelection()
    
    def parse_update_sql(self) -> UpdateSQL:
        """UPDATE table SET field = value WHERE condition."""
        self.expect("UPDATE")
        table = self.expect("ID").value.lower()
        self.expect("SET")
        
        set_clause = {}
        while not self.accept("WHERE") and not self.accept("."):
            field = self.expect("ID").value.lower()
            self.expect("=")
            value = self.parse_expression()
            set_clause[field] = value
            if self.accept(","):
                continue
        
        where_clause = None
        if self.accept("WHERE"):
            where_clause = self.parse_expression()
        
        self.expect(".")
        return UpdateSQL(table, set_clause, where_clause)
    
    def parse_insert_sql(self) -> InsertSQL:
        """INSERT INTO table (field1, field2) VALUES (value1, value2)."""
        self.expect("INSERT")
        self.expect("INTO")
        table = self.expect("ID").value.lower()
        
        values = {}
        if self.accept("("):
            while not self.accept(")"):
                field = self.expect("ID").value.lower()
                self.expect("=")
                value = self.parse_expression()
                values[field] = value
                if self.accept(","):
                    continue
        
        self.expect(".")
        return InsertSQL(table, values)
    
    def parse_delete_sql(self) -> DeleteSQL:
        """DELETE FROM table WHERE condition."""
        self.expect("DELETE")
        self.expect("FROM")
        table = self.expect("ID").value.lower()
        
        where_clause = None
        if self.accept("WHERE"):
            where_clause = self.parse_expression()
        
        self.expect(".")
        return DeleteSQL(table, where_clause)
    
    def parse_commit_work(self) -> CommitWork:
        """COMMIT WORK."""
        self.expect("COMMIT")
        if self.accept("WORK"):
            pass
        self.expect(".")
        return CommitWork()
    
    def parse_rollback_work(self) -> RollbackWork:
        """ROLLBACK WORK."""
        self.expect("ROLLBACK")
        if self.accept("WORK"):
            pass
        self.expect(".")
        return RollbackWork()
    
    def parse_clear_stmt(self) -> Clear:
        """CLEAR: var1, var2."""
        self.expect("CLEAR")
        
        targets = []
        while self.peek() and not self.accept("."):
            if self.peek().kind == "ID":
                var_name = self.next().value.lower()
                
                if self.accept("-"):
                    field_name = self.expect("ID").value.lower()
                    targets.append(Field(var_name, field_name))
                else:
                    targets.append(Var(var_name))
            
            if self.accept(","):
                continue
        
        return Clear(targets)
    
    def parse_move_stmt(self) -> Move:
        """MOVE: source TO target."""
        self.expect("MOVE")
        
        source = self.parse_expression()
        self.expect("TO")
        
        if self.peek().kind == "ID":
            var_name = self.next().value.lower()
            
            if self.accept("-"):
                field_name = self.expect("ID").value.lower()
                target = Field(var_name, field_name)
            else:
                target = Var(var_name)
        
        self.expect(".")
        return Move(source, target)
    
    def parse_assignment(self) -> Assign:
        """Assignment: target = expr."""
        if self.peek().kind == "ID":
            var_name = self.next().value.lower()
            
            if self.accept("-"):
                field_name = self.expect("ID").value.lower()
                target = Field(var_name, field_name)
            else:
                target = Var(var_name)
        
        self.expect("=")
        expr = self.parse_expression()
        self.expect(".")
        
        return Assign(target, expr)
    
    def parse_append_stmt(self) -> Union[Append, AppendSimple]:
        """APPEND statement"""
        self.expect("APPEND")
        
        if self.accept("VALUE"):
            self.expect("#")
            self.expect("(")
            
            source_row = {}
            while not self.accept(")"):
                key = self.expect("ID").value.lower()
                self.expect("=")
                val = self.parse_expression()
                source_row[key] = val
                self.accept(",")
            
            self.expect("TO")
            target = self.expect("ID").value.lower()
            self.expect(".")
            return Append(source_row, target)
        
        source = self.expect("ID").value.lower()
        self.expect("TO")
        target = self.expect("ID").value.lower()
        self.expect(".")
        return AppendSimple(source, target)
    
    def parse_modify_stmt(self) -> ModifyTable:
        """MODIFY TABLE itab FROM wa [USING KEY ...]."""
        self.expect("MODIFY")
        self.expect("TABLE")
        
        table_name = self.expect("ID").value.lower()
        self.expect("FROM")
        from_var = self.expect("ID").value.lower()
        
        key_field = None
        if self.accept("USING"):
            self.expect("KEY")
            key_field = self.expect("ID").value.lower()
        
        self.expect(".")
        return ModifyTable(table_name, from_var, key_field)
    
    def parse_delete_stmt(self) -> DeleteTable:
        """DELETE TABLE itab [WITH KEY ...]."""
        self.expect("DELETE")
        self.expect("TABLE")
        
        table_name = self.expect("ID").value.lower()
        
        key = None
        if self.accept("WITH"):
            self.expect("KEY")
            key_field = self.expect("ID").value.lower()
            self.expect("=")
            key_value = self.parse_expression()
            key = (key_field, key_value)
        
        self.expect(".")
        return DeleteTable(table_name, key)
    
    def parse_insert_stmt(self) -> InsertTable:
        """INSERT wa INTO TABLE itab."""
        self.expect("INSERT")
        source = self.expect("ID").value.lower()
        self.expect("INTO")
        self.expect("TABLE")
        target = self.expect("ID").value.lower()
        self.expect(".")
        return InsertTable(source, target)
    
    def parse_loop(self) -> LoopAt:
        """LOOP AT itab INTO wa."""
        self.expect("LOOP")
        self.expect("AT")
        
        table = self.expect("ID").value.lower()
        self.expect("INTO")
        into = self.expect("ID").value.lower()
        self.expect(".")
        
        body = []
        while self.peek() and self.peek().value != "ENDLOOP":
            stmt = self.parse_statement()
            if stmt:
                body.append(stmt)
        
        self.expect("ENDLOOP")
        self.expect(".")
        return LoopAt(table, into, body)
    
    def parse_read_table(self) -> ReadTable:
        """READ TABLE itab INTO wa WITH KEY ..."""
        self.expect("READ")
        self.expect("TABLE")
        
        table_name = self.expect("ID").value.lower()
        
        into = None
        if self.accept("INTO"):
            into = self.expect("ID").value.lower()
        
        key = None
        transporting = None
        if self.accept("WITH"):
            self.expect("KEY")
            key_field = self.expect("ID").value.lower()
            self.expect("=")
            key_value = self.parse_expression()
            key = (key_field, key_value)
        
        self.expect(".")
        return ReadTable(table_name, into, key, transporting)
    
    def parse_exit_stmt(self) -> Exit:
        """EXIT statement."""
        self.expect("EXIT")
        self.expect(".")
        return Exit()
    
    def parse_continue_stmt(self) -> Continue:
        """CONTINUE statement."""
        self.expect("CONTINUE")
        self.expect(".")
        return Continue()
    
    def parse_check_stmt(self) -> Check:
        """CHECK condition."""
        self.expect("CHECK")
        condition = self.parse_expression()
        self.expect(".")
        return Check(condition)
    
    def parse_if_block(self) -> If:
        """IF cond. ... ELSEIF cond. ... ELSE. ... ENDIF."""
        self.expect("IF")
        cond = self.parse_expression()
        self.expect(".")
        
        then_body = []
        while self.peek() and self.peek().value not in ("ELSEIF", "ELSE", "ENDIF"):
            stmt = self.parse_statement()
            if stmt:
                then_body.append(stmt)
        
        elif_list = []
        while self.accept("ELSEIF"):
            elif_cond = self.parse_expression()
            self.expect(".")
            
            elif_body = []
            while self.peek() and self.peek().value not in ("ELSEIF", "ELSE", "ENDIF"):
                stmt = self.parse_statement()
                if stmt:
                    elif_body.append(stmt)
            
            elif_list.append((elif_cond, elif_body))
        
        else_body = []
        if self.accept("ELSE"):
            self.expect(".")
            while self.peek() and self.peek().value != "ENDIF":
                stmt = self.parse_statement()
                if stmt:
                    else_body.append(stmt)
        
        self.expect("ENDIF")
        self.expect(".")
        
        return If(cond, then_body, elif_list, else_body)
    
    def parse_while(self) -> While:
        """WHILE cond. ... ENDWHILE."""
        self.expect("WHILE")
        cond = self.parse_expression()
        self.expect(".")
        
        body = []
        while self.peek() and self.peek().value != "ENDWHILE":
            stmt = self.parse_statement()
            if stmt:
                body.append(stmt)
        
        self.expect("ENDWHILE")
        self.expect(".")
        return While(cond, body)
    
    def parse_do(self) -> Do:
        """DO n TIMES. ... ENDDO."""
        self.expect("DO")
        
        times_expr = None
        if self.peek() and self.peek().kind not in ("SYMBOL", "KEYWORD"):
            times_expr = self.parse_expression()
        
        if self.accept("TIMES"):
            pass
        
        self.expect(".")
        
        body = []
        while self.peek() and self.peek().value != "ENDDO":
            stmt = self.parse_statement()
            if stmt:
                body.append(stmt)
        
        self.expect("ENDDO")
        self.expect(".")
        return Do(times_expr, body)
    
    def parse_case(self) -> Case:
        """CASE expr. WHEN val. ... WHEN OTHERS. ... ENDCASE."""
        self.expect("CASE")
        expr = self.parse_expression()
        self.expect(".")
        
        cases = []
        others_body = []
        
        while self.peek() and self.peek().value != "ENDCASE":
            if self.accept("WHEN"):
                if self.accept("OTHERS"):
                    self.expect(".")
                    while self.peek() and self.peek().value != "ENDCASE":
                        stmt = self.parse_statement()
                        if stmt:
                            others_body.append(stmt)
                    continue
                
                value = self.parse_expression()
                self.expect(".")
                
                when_body = []
                while self.peek() and self.peek().value not in ("WHEN", "ENDCASE"):
                    stmt = self.parse_statement()
                    if stmt:
                        when_body.append(stmt)
                
                cases.append((value, when_body))
        
        self.expect("ENDCASE")
        self.expect(".")
        return Case(expr, cases, others_body)
    
    def parse_select(self) -> SelectInto:
        """SELECT * FROM table INTO TABLE itab [WHERE ...] [ORDER BY ...]."""
        self.expect("SELECT")
        
        fields = []
        if self.accept("*"):
            fields = ["*"]
        else:
            while self.peek() and self.peek().value != "FROM":
                field = self.expect("ID").value.lower()
                fields.append(field)
                self.accept(",")
        
        self.expect("FROM")
        table = self.expect("ID").value.lower()
        
        where_clause = None
        if self.accept("WHERE"):
            where_clause = self.parse_expression()
        
        order_by = []
        if self.accept("ORDER"):
            self.expect("BY")
            while self.peek() and self.peek().value not in ("INTO", "."):
                field = self.expect("ID").value.lower()
                order_by.append(field)
                if self.accept(","):
                    continue
                break
        
        self.expect("INTO")
        self.expect("TABLE")
        target = self.expect("ID").value.lower()
        self.expect(".")
        
        return SelectInto(fields, table, target, where_clause, order_by)