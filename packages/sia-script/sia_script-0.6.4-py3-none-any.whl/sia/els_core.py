"""
SIA ENTERPRISE LOGIC STUDIO - CORE RUNTIME
===========================================
Author: Nagesh
Version: 5.0 - Complete Syllabus with Fixed Semantics
-----------------------------------------

Core runtime engine with strict ABAP semantics.
Single source of truth for variables.
No silent None returns.
Proper boolean context.
"""

import re
import sys
import datetime
import json
from typing import List, Dict, Any, Optional, Union, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum

# =====================================================
# ===============     TYPE SYSTEM     ================
# =====================================================

class ABAPType:
    """ABAP type system with strict validation and conversion"""
    
    TYPE_MAP = {
        'I': ('integer', 0, None),
        'C': ('character', ' ', 1),  # Default length 1
        'STRING': ('string', '', None),
        'F': ('float', 0.0, None),
        'P': ('packed', 0, None),
        'N': ('numeric', '0', None),
        'D': ('date', '00000000', 8),
        'T': ('time', '000000', 6),
        'X': ('hexadecimal', '00', None),
        'BOOL': ('boolean', False, None)  # Added for strict boolean handling
    }
    
    def __init__(self, type_name: str, length: Optional[int] = None):
        self.name = type_name.upper()
        if self.name not in self.TYPE_MAP:
            raise ValueError(f"Unknown ABAP type: {type_name}")
        
        self.kind, self.default, self.default_length = self.TYPE_MAP[self.name]
        self.length = length if length is not None else self.default_length
        
        # ABAP defaults
        if self.name == 'C' and self.length is None:
            self.length = 1  # Default length for TYPE C
    
    def validate(self, value: Any) -> Any:
        """Validate and convert value to this type following strict ABAP rules"""
        if value is None:
            return self.default_value()
        
        str_value = str(value)
        
        if self.name == 'I':
            try:
                # ABAP: Convert to integer, truncate decimal
                return int(float(str_value))
            except (ValueError, TypeError):
                return 0
                
        elif self.name == 'C':
            # ABAP C type: fixed length, space-padded, no truncation warning
            if self.length:
                # Pad with spaces to exact length
                if len(str_value) > self.length:
                    # Silent truncation (ABAP behavior)
                    return str_value[:self.length]
                else:
                    return str_value.ljust(self.length)
            return str_value
            
        elif self.name == 'STRING':
            return str_value
            
        elif self.name == 'F':
            try:
                return float(str_value)
            except (ValueError, TypeError):
                return 0.0
                
        elif self.name == 'D':  # YYYYMMDD
            clean = ''.join(c for c in str_value if c.isdigit())
            if len(clean) >= 8:
                return clean[:8]
            return clean.rjust(8, '0')
            
        elif self.name == 'T':  # HHMMSS
            clean = ''.join(c for c in str_value if c.isdigit())
            if len(clean) >= 6:
                return clean[:6]
            return clean.rjust(6, '0')
            
        elif self.name == 'N':
            # Numeric string: digits only, right-aligned, zero-padded
            digits = ''.join(c for c in str_value if c.isdigit())
            if self.length:
                return digits.rjust(self.length, '0')[:self.length]
            return digits
            
        elif self.name == 'P':
            # Packed decimal - store as integer for now
            try:
                return int(float(str_value))
            except (ValueError, TypeError):
                return 0
                
        elif self.name == 'X':
            # Hexadecimal - simple string representation
            hex_chars = '0123456789ABCDEFabcdef'
            filtered = ''.join(c for c in str_value if c in hex_chars)
            return filtered.upper()
        
        elif self.name == 'BOOL':
            # Boolean type for strict context
            if isinstance(value, bool):
                return value
            if str(value).upper() in ('TRUE', 'X', '1', 'YES'):
                return True
            return False
        
        return str_value
    
    def default_value(self) -> Any:
        """Return default value for type (ABAP initial value)"""
        if self.name == 'I':
            return 0
        elif self.name == 'C':
            if self.length:
                return ' ' * self.length
            return ' '
        elif self.name == 'STRING':
            return ''
        elif self.name == 'F':
            return 0.0
        elif self.name == 'D':
            return '00000000'
        elif self.name == 'T':
            return '000000'
        elif self.name == 'N':
            if self.length:
                return '0' * self.length
            return '0'
        elif self.name == 'P':
            return 0
        elif self.name == 'X':
            return '00'
        elif self.name == 'BOOL':
            return False
        return ''
    
    def __repr__(self):
        if self.length:
            return f"ABAPType({self.name}, LENGTH {self.length})"
        return f"ABAPType({self.name})"


class TypedVariable:
    """Variable with strict ABAP type information - SINGLE SOURCE OF TRUTH"""
    
    def __init__(self, name: str, abap_type: ABAPType, value: Any = None):
        self.name = name
        self.type = abap_type
        self.value = self.type.validate(value) if value is not None else self.type.default_value()
    
    def set_value(self, value: Any):
        """Set value with strict type validation"""
        self.value = self.type.validate(value)
    
    def get_value(self) -> Any:
        """Get typed value"""
        return self.value
    
    def get_initial(self) -> Any:
        """Get type's initial value"""
        return self.type.default_value()
    
    def __repr__(self):
        return f"TypedVariable({self.name}, {self.type}, {repr(self.value)})"


# =====================================================
# ===============   RUNTIME ENGINE    =================
# =====================================================

class RuntimeError(Exception):
    """Runtime error exception"""
    pass


class SystemVariables:
    """ABAP system variables with strict updates"""
    
    def __init__(self):
        now = datetime.datetime.now()
        self.vars = {
            'sy-subrc': 0,
            'sy-tabix': 0,
            'sy-index': 0,
            'sy-dbcnt': 0,
            'sy-uzeit': now.strftime("%H%M%S").upper(),
            'sy-datum': now.strftime("%Y%m%d")
        }
    
    def get(self, name: str) -> Any:
        """Get system variable value"""
        return self.vars.get(name)
    
    def set(self, name: str, value: Any):
        """Set system variable value with type validation"""
        # Type validation for system variables
        if name == 'sy-subrc':
            try:
                value = int(value)
                if not 0 <= value <= 8:  # Standard ABAP range
                    value = 8
            except (ValueError, TypeError):
                value = 8
        elif name == 'sy-tabix':
            try:
                value = int(value)
                if value < 0:
                    value = 0
            except (ValueError, TypeError):
                value = 0
        elif name == 'sy-index':
            try:
                value = int(value)
                if value < 0:
                    value = 0
            except (ValueError, TypeError):
                value = 0
        elif name == 'sy-dbcnt':
            try:
                value = int(value)
                if value < 0:
                    value = 0
            except (ValueError, TypeError):
                value = 0
        
        self.vars[name] = value
    
    def reset_loop_vars(self):
        """Reset loop-related system variables"""
        self.vars['sy-tabix'] = 0
        self.vars['sy-index'] = 0
    
    def update_for_success(self):
        """Set SY-SUBRC to 0 (success)"""
        self.set('sy-subrc', 0)
    
    def update_for_not_found(self):
        """Set SY-SUBRC to 4 (not found)"""
        self.set('sy-subrc', 4)
    
    def update_for_error(self):
        """Set SY-SUBRC to 8 (error)"""
        self.set('sy-subrc', 8)


class FormDef:
    """FORM subroutine definition"""
    
    def __init__(self, name: str, params: List[Tuple[str, str]], body: List['ASTNode']):
        self.name = name
        self.params = params  # (name, kind)
        self.body = body
    
    def __repr__(self):
        return f"FormDef({self.name}, {len(self.params)} params)"


class SelectionOption:
    """SELECT-OPTIONS range with full matching logic"""
    
    def __init__(self, sign: str = "I", option: str = "EQ", 
                 low: Any = None, high: Any = None):
        self.sign = sign  # I (include) or E (exclude)
        self.option = option  # EQ, NE, GT, LT, GE, LE, BT, CP, NP
        self.low = low
        self.high = high
    
    def matches(self, value: Any) -> bool:
        """Check if value matches selection option"""
        if self.low is None:
            return self.sign == "I"  # Empty range includes all if sign=I
        
        # Convert to strings for comparison
        val_str = str(value).strip()
        low_str = str(self.low).strip() if self.low is not None else ""
        high_str = str(self.high).strip() if self.high is not None else ""
        
        result = False
        
        if self.option == "EQ":
            result = val_str == low_str
        elif self.option == "NE":
            result = val_str != low_str
        elif self.option == "GT":
            try:
                result = float(val_str) > float(low_str)
            except:
                result = val_str > low_str
        elif self.option == "LT":
            try:
                result = float(val_str) < float(low_str)
            except:
                result = val_str < low_str
        elif self.option == "GE":
            try:
                result = float(val_str) >= float(low_str)
            except:
                result = val_str >= low_str
        elif self.option == "LE":
            try:
                result = float(val_str) <= float(low_str)
            except:
                result = val_str <= low_str
        elif self.option == "BT":
            if low_str and high_str:
                try:
                    result = float(low_str) <= float(val_str) <= float(high_str)
                except:
                    result = low_str <= val_str <= high_str
            else:
                result = False
        elif self.option == "CP":  # Pattern match (simplified)
            pattern = low_str.replace('*', '.*').replace('+', '.+')
            import re
            result = bool(re.match(f"^{pattern}$", val_str))
        elif self.option == "NP":  # Not pattern
            pattern = low_str.replace('*', '.*').replace('+', '.+')
            import re
            result = not bool(re.match(f"^{pattern}$", val_str))
        else:
            result = val_str == low_str  # Default to EQ
        
        # Apply sign
        if self.sign == "E":
            result = not result
        
        return result
    
    def __repr__(self):
        return f"SelectionOption({self.sign} {self.option} {self.low}:{self.high})"


class VariableScope:
    """Manages variable scopes with single source of truth"""
    
    def __init__(self):
        self.typed_vars = {}  # SINGLE SOURCE OF TRUTH: name -> TypedVariable
        self.constants = {}
        self.parameters = {}
        self.select_options = {}
        self.structures = {}
        self.table_types = {}
        self.tables = {}
        self.call_stack = []
    
    def get_variable(self, name: str) -> Any:
        """Get variable value - ONLY from typed_vars or constants"""
        # System variables
        if name.startswith('sy-'):
            return None  # Handled separately
        
        # Check local scope first (for FORM parameters)
        if self.call_stack:
            local_scope = self.call_stack[-1]
            if name in local_scope:
                return local_scope[name]
        
        # Constants override everything
        if name in self.constants:
            return self.constants[name]
        
        # SINGLE SOURCE OF TRUTH: typed_vars
        if name in self.typed_vars:
            return self.typed_vars[name].get_value()
        
        # Variable doesn't exist - raise error (no silent None!)
        raise RuntimeError(f"Variable '{name}' is not declared")
    
    def set_variable(self, name: str, value: Any, var_type: Optional[str] = None, 
                    length: Optional[int] = None, force_create: bool = False):
        """Set variable value - ONLY in typed_vars"""
        if name in self.constants:
            raise RuntimeError(f"Cannot modify constant: {name}")
        
        # Check local scope for CHANGING parameters
        if self.call_stack:
            local_scope = self.call_stack[-1]
            if name in local_scope:
                local_scope[name] = value
                return
        
        # SINGLE SOURCE OF TRUTH: Always use typed_vars
        if name in self.typed_vars:
            typed_var = self.typed_vars[name]
            typed_var.set_value(value)
        elif force_create:
            # Create new typed variable
            if var_type:
                abap_type = ABAPType(var_type, length)
            else:
                # Auto-detect type
                if isinstance(value, int):
                    abap_type = ABAPType('I')
                elif isinstance(value, float):
                    abap_type = ABAPType('F')
                elif isinstance(value, bool):
                    abap_type = ABAPType('BOOL')
                else:
                    abap_type = ABAPType('C')
            
            typed_var = TypedVariable(name, abap_type, value)
            self.typed_vars[name] = typed_var
        else:
            raise RuntimeError(f"Cannot assign to undeclared variable: {name}")
    
    def declare_variable(self, name: str, var_type: Optional[str] = None, 
                        length: Optional[int] = None, initial_value: Any = None):
        """Declare a new variable"""
        if name in self.typed_vars:
            raise RuntimeError(f"Variable '{name}' already declared")
        
        if var_type:
            abap_type = ABAPType(var_type, length)
        else:
            # Default to character type
            abap_type = ABAPType('C', length)
        
        value = abap_type.validate(initial_value) if initial_value is not None else abap_type.default_value()
        typed_var = TypedVariable(name, abap_type, value)
        self.typed_vars[name] = typed_var
    
    def declare_constant(self, name: str, value: Any, var_type: Optional[str] = None, 
                        length: Optional[int] = None):
        """Declare a constant"""
        if name in self.constants:
            raise RuntimeError(f"Constant '{name}' already declared")
        
        if var_type:
            abap_type = ABAPType(var_type, length)
            typed_value = abap_type.validate(value)
            self.constants[name] = typed_value
        else:
            self.constants[name] = value
        
        # Also create typed variable for consistency
        self.declare_variable(name, var_type, length, value)
    
    def declare_parameter(self, name: str, value: Any = None, 
                         var_type: Optional[str] = None, length: Optional[int] = None):
        """Declare a PARAMETER"""
        self.parameters[name] = value
        self.declare_variable(name, var_type, length, value)
    
    def declare_select_option(self, name: str, for_var: str, 
                             var_type: Optional[str] = None, length: Optional[int] = None):
        """Declare a SELECT-OPTIONS"""
        # SELECT-OPTIONS are range tables
        self.select_options[name] = []
        # Create typed variable for the range table
        self.declare_variable(name, 'C', 1)  # Simple type for now
    
    def push_scope(self):
        """Push new local scope onto stack"""
        self.call_stack.append({})
    
    def pop_scope(self):
        """Pop local scope from stack"""
        if self.call_stack:
            self.call_stack.pop()
    
    def save_state(self) -> Dict:
        """Save current variable state for loops"""
        state = {}
        for name, typed_var in self.typed_vars.items():
            state[name] = typed_var.get_value()
        return state
    
    def restore_state(self, state: Dict):
        """Restore variable state from snapshot"""
        for name, value in state.items():
            if name in self.typed_vars:
                self.typed_vars[name].set_value(value)


class RuntimeEnv:
    """
    Runtime environment for strict ABAP execution.
    Uses VariableScope as single source of truth.
    """
    
    def __init__(self):
        # Core storage - SINGLE SOURCE OF TRUTH
        self.vars = VariableScope()
        
        # Database and tables
        self.db = {}
        self.db_snapshots = []
        
        # Subroutines
        self.forms = {}  # FORM definitions
        self.classes = {}
        self.objects = {}
        
        # System
        self.sy = SystemVariables()
        self.output = []
        
        # Execution control
        self.in_declaration_phase = True
        self.execution_started = False
        
        # Loop control
        self.should_exit_loop = False
        self.should_continue = False
        self.loop_stack = []  # For nested loops
        
        # Control break simulation
        self.control_break_data = {}
        
        # Safety guards
        self.max_loop_iterations = 1000000
        
        # Load example data
        self._bootstrap()
    
    def _bootstrap(self):
        """Load example SQL tables"""
        self.db["employees"] = [
            {"id": "1", "name": "Alice", "dept": "HR", "salary": "50000"},
            {"id": "2", "name": "Bob", "dept": "IT", "salary": "60000"},
            {"id": "3", "name": "Carol", "dept": "HR", "salary": "55000"},
            {"id": "4", "name": "Dave", "dept": "IT", "salary": "65000"}
        ]
        
        self.db["departments"] = [
            {"dept_id": "HR", "dept_name": "Human Resources"},
            {"dept_id": "IT", "dept_name": "Information Technology"}
        ]
        
        # Initialize with default snapshot
        self._save_db_snapshot()
    
    def _save_db_snapshot(self):
        """Save current database state for COMMIT/ROLLBACK"""
        snapshot = {}
        for table, rows in self.db.items():
            snapshot[table] = [row.copy() for row in rows]
        self.db_snapshots.append(snapshot)
        
        # Keep only last 10 snapshots
        if len(self.db_snapshots) > 10:
            self.db_snapshots.pop(0)
    
    def _restore_db_snapshot(self):
        """Restore database to last snapshot"""
        if self.db_snapshots:
            snapshot = self.db_snapshots.pop()
            self.db = snapshot
        else:
            self.db = {}
    
    def get_variable(self, name: str) -> Any:
        """Get variable value - with proper error handling"""
        try:
            if name.startswith('sy-'):
                return self.sy.get(name)
            return self.vars.get_variable(name)
        except RuntimeError:
            # For backward compatibility during transition
            return ""
    
    def set_variable(self, name: str, value: Any, var_type: Optional[str] = None, 
                    length: Optional[int] = None, force_create: bool = False):
        """Set variable value - with proper error handling"""
        if name.startswith('sy-'):
            self.sy.set(name, value)
            return
        
        try:
            self.vars.set_variable(name, value, var_type, length, force_create)
        except RuntimeError as e:
            # For assignment to undeclared variables in execution phase
            if not self.in_declaration_phase and force_create:
                self.vars.set_variable(name, value, var_type, length, True)
            else:
                raise e
    
    def push_loop(self):
        """Push loop context onto stack"""
        self.loop_stack.append({
            'should_exit': False,
            'should_continue': False
        })
    
    def pop_loop(self):
        """Pop loop context from stack"""
        if self.loop_stack:
            return self.loop_stack.pop()
        return None
    
    def current_loop(self):
        """Get current loop context"""
        if self.loop_stack:
            return self.loop_stack[-1]
        return None
    
    def check_loop_control(self) -> Tuple[bool, bool]:
        """Check if loop should exit or continue"""
        if not self.loop_stack:
            return False, False
        
        loop_ctx = self.current_loop()
        should_exit = loop_ctx.get('should_exit', False)
        should_continue = loop_ctx.get('should_continue', False)
        
        # Reset for next iteration
        if should_exit:
            loop_ctx['should_exit'] = False
        if should_continue:
            loop_ctx['should_continue'] = False
        
        return should_exit, should_continue


# =====================================================
# ===============   EXPRESSION EVALUATION   ===========
# =====================================================

def eval_expr(env: RuntimeEnv, expr: 'ASTNode') -> Any:
    """Evaluate an expression node with strict ABAP rules - NEVER returns None"""
    
    from .els_parser import Number, String, Var, Field, FuncCall, BinOp, UnaryOp
    
    if isinstance(expr, Number):
        return expr.val
    
    if isinstance(expr, String):
        return expr.val
    
    if isinstance(expr, Var):
        value = env.get_variable(expr.name)
        # If variable doesn't exist, return empty string (not None!)
        if value is None:
            return ""
        return value
    
    if isinstance(expr, Field):
        struct_val = env.get_variable(expr.struct)
        if isinstance(struct_val, dict):
            return struct_val.get(expr.field, "")
        return ""
    
    if isinstance(expr, FuncCall):
        return eval_func_call(env, expr)
    
    if isinstance(expr, BinOp):
        return eval_binop(env, expr)
    
    if isinstance(expr, UnaryOp):
        return eval_unaryop(env, expr)
    
    # If we get here, expression type is not handled
    raise RuntimeError(f"Cannot evaluate expression: {type(expr).__name__}")


def eval_expr_force(env: RuntimeEnv, expr: 'ASTNode') -> Any:
    """Evaluate expression, always returning a valid value"""
    try:
        result = eval_expr(env, expr)
        if result is None:
            return ""
        return result
    except:
        return ""


def eval_binop(env: RuntimeEnv, expr: 'BinOp') -> Any:
    """Evaluate binary operation with strict ABAP rules"""
    # Evaluate operands
    left = eval_expr_force(env, expr.left)
    right = eval_expr_force(env, expr.right)
    op = expr.op
    
    # Handle None values - convert to type defaults
    if left is None:
        left = 0 if op in ("+", "-", "*", "/") else ""
    if right is None:
        right = 0 if op in ("+", "-", "*", "/") else ""
    
    # Arithmetic operations
    if op == "+":
        if isinstance(left, str) or isinstance(right, str):
            return str(left) + str(right)
        return (left or 0) + (right or 0)
    
    if op == "-":
        return (left or 0) - (right or 0)
    
    if op == "*":
        return (left or 0) * (right or 0)
    
    if op == "/":
        if right == 0:
            raise RuntimeError("Division by zero")
        return (left or 0) / (right or 0)
    
    # Comparison operations
    if op == "=":
        # Try numeric comparison first
        try:
            return float(left) == float(right)
        except:
            return str(left).strip() == str(right).strip()
    
    if op == "<>":
        try:
            return float(left) != float(right)
        except:
            return str(left).strip() != str(right).strip()
    
    if op == ">":
        try:
            return float(left) > float(right)
        except:
            return str(left) > str(right)
    
    if op == "<":
        try:
            return float(left) < float(right)
        except:
            return str(left) < str(right)
    
    if op == ">=":
        try:
            return float(left) >= float(right)
        except:
            return str(left) >= str(right)
    
    if op == "<=":
        try:
            return float(left) <= float(right)
        except:
            return str(left) <= str(right)
    
    # Logical operations
    if op == "AND":
        # Convert to boolean (ABAP allows non-boolean in logical context)
        left_bool = bool(left)
        if not left_bool:
            return False
        return bool(right)
    
    if op == "OR":
        left_bool = bool(left)
        if left_bool:
            return True
        return bool(right)
    
    raise RuntimeError(f"Unknown operator: {op}")


def eval_unaryop(env: RuntimeEnv, expr: 'UnaryOp') -> Any:
    """Evaluate unary operation"""
    if expr.op == "NOT":
        operand = eval_expr_force(env, expr.operand)
        # Convert to boolean
        return not bool(operand)
    
    raise RuntimeError(f"Unknown unary operator: {expr.op}")


def eval_func_call(env: RuntimeEnv, expr: 'FuncCall') -> Any:
    """Evaluate function call"""
    func_name = expr.name
    args = [eval_expr_force(env, arg) for arg in expr.args]
    
    if func_name == "LINES":
        if len(args) != 1:
            raise RuntimeError("LINES expects 1 argument")
        table_name = expr.args[0].name if hasattr(expr.args[0], 'name') else str(args[0])
        return len(env.vars.tables.get(table_name, []))
    
    if func_name == "STRLEN":
        if len(args) != 1:
            raise RuntimeError("STRLEN expects 1 argument")
        return len(str(args[0]))
    
    if func_name == "ABS":
        if len(args) != 1:
            raise RuntimeError("ABS expects 1 argument")
        try:
            return abs(float(args[0]))
        except ValueError:
            return 0
    
    if func_name == "CONCATENATE":
        return "".join(str(arg) for arg in args)
    
    if func_name == "UPPER":
        if len(args) != 1:
            raise RuntimeError("UPPER expects 1 argument")
        return str(args[0]).upper()
    
    if func_name == "LOWER":
        if len(args) != 1:
            raise RuntimeError("LOWER expects 1 argument")
        return str(args[0]).lower()
    
    # Unknown function - return empty string (not None!)
    return ""


def validate_boolean_condition(cond: Any, context: str = "IF") -> bool:
    """Validate that condition evaluates properly for boolean context"""
    # In ABAP, many things can be in boolean context
    # We just ensure it's not None
    if cond is None:
        raise RuntimeError(f"{context} condition evaluates to None")
    
    # Convert to boolean for evaluation
    return bool(cond)


def eval_where_with_row(env: RuntimeEnv, where_expr: 'ASTNode', row: Dict) -> bool:
    """Evaluate WHERE clause with row values as variables"""
    
    from .els_parser import Var, Number, String, Field, BinOp, UnaryOp
    
    def eval_with_row(expr: 'ASTNode') -> Any:
        if isinstance(expr, Var):
            # Check if variable exists in row first
            if expr.name in row:
                return row[expr.name]
            # Check system variables
            if expr.name.startswith('sy-'):
                return env.sy.get(expr.name)
            # Check environment variables
            return env.get_variable(expr.name) or ""
        
        if isinstance(expr, Number):
            return expr.val
        
        if isinstance(expr, String):
            return expr.val
        
        if isinstance(expr, Field):
            struct_val = eval_with_row(Var(expr.struct))
            if isinstance(struct_val, dict):
                return struct_val.get(expr.field, "")
            return ""
        
        if isinstance(expr, BinOp):
            left = eval_with_row(expr.left)
            right = eval_with_row(expr.right)
            op = expr.op
            
            if op == "=":
                return str(left).strip() == str(right).strip()
            elif op == "<>":
                return str(left).strip() != str(right).strip()
            elif op == ">":
                try:
                    return float(left) > float(right)
                except:
                    return str(left) > str(right)
            elif op == "<":
                try:
                    return float(left) < float(right)
                except:
                    return str(left) < str(right)
            elif op == ">=":
                try:
                    return float(left) >= float(right)
                except:
                    return str(left) >= str(right)
            elif op == "<=":
                try:
                    return float(left) <= float(right)
                except:
                    return str(left) <= str(right)
            elif op == "AND":
                return bool(left) and bool(right)
            elif op == "OR":
                return bool(left) or bool(right)
        
        if isinstance(expr, UnaryOp) and expr.op == "NOT":
            operand = eval_with_row(expr.operand)
            return not bool(operand)
        
        return ""
    
    result = eval_with_row(where_expr)
    return bool(result)


# =====================================================
# ===============   STATEMENT EXECUTION   =============
# =====================================================

def exec_statement(env: RuntimeEnv, stmt: 'ASTNode'):
    """Execute a single ABAP statement with strict semantics"""
    
    from .els_parser import (
        # Declarations
        DataDecl, ConstantDecl, ParameterDecl, SelectOptionsDecl,
        TypesBeginOf, DataBeginOf,
        # Forms
        FormDecl, Perform, EndForm,
        # Events
        StartOfSelection,
        # Output
        Write,
        # Data manipulation
        Assign, Clear, Move,
        # Table operations
        Append, AppendSimple, ModifyTable, DeleteTable, InsertTable, ReadTable,
        # Control flow
        Exit, Continue, Check,
        # Loops
        LoopAt, EndLoop,
        # Conditionals
        If, While, Do, Case,
        # SQL
        UpdateSQL, InsertSQL, DeleteSQL, CommitWork, RollbackWork, SelectInto,
        # Control breaks
        AtNew, AtEndOf
    )
    
    # FIX: Enforce START-OF-SELECTION phase rules
    if env.in_declaration_phase:
        # Only these statements allowed in declaration phase
        allowed_in_declaration = (
            DataDecl, ConstantDecl, ParameterDecl, SelectOptionsDecl,
            TypesBeginOf, DataBeginOf, FormDecl, EndForm, StartOfSelection
        )
        if not isinstance(stmt, allowed_in_declaration):
            # Silently skip executable statements in declaration phase
            return
    
    # Check loop control flags
    if env.loop_stack:
        should_exit, should_continue = env.check_loop_control()
        if should_exit:
            return
        if should_continue:
            return
    
    # -------------------------
    # WRITE statement
    # -------------------------
    if isinstance(stmt, Write):
        for item in stmt.items:
            if isinstance(item, String) and item.val == "\n":
                env.output.append("\n")
            else:
                # Force evaluation, never print None
                value = eval_expr_force(env, item)
                env.output.append(str(value))
        env.output.append("\n")
        return
    
    # -------------------------
    # DATA declaration
    # -------------------------
    if isinstance(stmt, DataDecl):
        value = None
        if stmt.value:
            value = eval_expr(env, stmt.value)
        
        env.vars.declare_variable(stmt.name, stmt.type_spec, stmt.length, value)
        env.sy.update_for_success()
        return
    
    # -------------------------
    # TYPES BEGIN OF
    # -------------------------
    if isinstance(stmt, TypesBeginOf):
        env.vars.structures[stmt.name] = stmt.components
        return
    
    # -------------------------
    # DATA BEGIN OF
    # -------------------------
    if isinstance(stmt, DataBeginOf):
        structure = {}
        for comp_name, comp_type, comp_length, comp_value in stmt.components:
            value = None
            if comp_value:
                value = eval_expr(env, comp_value)
            
            if comp_type:
                abap_type = ABAPType(comp_type, comp_length)
                typed_value = abap_type.validate(value)
                structure[comp_name] = typed_value
            else:
                structure[comp_name] = value
        
        env.vars.declare_variable(stmt.name, None, None, structure)
        env.sy.update_for_success()
        return
    
    # -------------------------
    # CONSTANTS declaration
    # -------------------------
    if isinstance(stmt, ConstantDecl):
        if not stmt.value:
            raise RuntimeError(f"Constant {stmt.name} must have a VALUE")
        
        value = eval_expr(env, stmt.value)
        env.vars.declare_constant(stmt.name, value, stmt.type_spec, stmt.length)
        env.sy.update_for_success()
        return
    
    # -------------------------
    # PARAMETERS declaration
    # -------------------------
    if isinstance(stmt, ParameterDecl):
        value = None
        if stmt.default:
            value = eval_expr(env, stmt.default)
        
        env.vars.declare_parameter(stmt.name, value, stmt.type_spec, stmt.length)
        return
    
    # -------------------------
    # SELECT-OPTIONS declaration
    # -------------------------
    if isinstance(stmt, SelectOptionsDecl):
        env.vars.declare_select_option(stmt.selname, stmt.for_var, stmt.type_spec, stmt.length)
        return
    
    # -------------------------
    # FORM declaration
    # -------------------------
    if isinstance(stmt, FormDecl):
        form_def = FormDef(stmt.name, stmt.params, stmt.body)
        env.forms[stmt.name] = form_def
        return
    
    # -------------------------
    # PERFORM statement
    # -------------------------
    if isinstance(stmt, Perform):
        if stmt.name not in env.forms:
            raise RuntimeError(f"FORM {stmt.name} not found")
        
        form_def = env.forms[stmt.name]
        
        # Push new scope for FORM execution
        env.vars.push_scope()
        
        try:
            # Map parameters to local scope
            param_idx = 0
            
            # Handle USING parameters (value copy)
            for param_name, param_kind in form_def.params:
                if param_kind == "USING":
                    if param_idx < len(stmt.using_params):
                        param_value = eval_expr(env, stmt.using_params[param_idx])
                        env.vars.call_stack[-1][param_name] = param_value
                        param_idx += 1
            
            # Handle CHANGING parameters (reference)
            for param_name, param_kind in form_def.params:
                if param_kind == "CHANGING":
                    if param_idx < len(stmt.changing_params):
                        # Store reference to original variable
                        changing_expr = stmt.changing_params[param_idx]
                        if isinstance(changing_expr, Var):
                            original_value = env.get_variable(changing_expr.name)
                            env.vars.call_stack[-1][param_name] = original_value
                        param_idx += 1
            
            # Execute FORM body
            for form_stmt in form_def.body:
                exec_statement(env, form_stmt)
            
            # Copy back CHANGING parameters
            param_idx = len(stmt.using_params)
            for param_name, param_kind in form_def.params:
                if param_kind == "CHANGING":
                    if param_idx < len(stmt.changing_params):
                        changing_expr = stmt.changing_params[param_idx]
                        if isinstance(changing_expr, Var):
                            new_value = env.vars.call_stack[-1].get(param_name)
                            env.set_variable(changing_expr.name, new_value, force_create=True)
                        param_idx += 1
        
        finally:
            # Pop local scope
            env.vars.pop_scope()
        
        return
    
    # -------------------------
    # START-OF-SELECTION
    # -------------------------
    if isinstance(stmt, StartOfSelection):
        env.in_declaration_phase = False
        env.execution_started = True
        return
    
    # -------------------------
    # Assignment
    # -------------------------
    if isinstance(stmt, Assign):
        value = eval_expr(env, stmt.expr)
        
        from .els_parser import Var, Field
        
        if isinstance(stmt.target, Var):
            env.set_variable(stmt.target.name, value, force_create=True)
        elif isinstance(stmt.target, Field):
            # Get or create structure
            struct_val = env.get_variable(stmt.target.struct)
            if not isinstance(struct_val, dict):
                struct_val = {}
            struct_val[stmt.target.field] = value
            env.set_variable(stmt.target.struct, struct_val, force_create=True)
        
        env.sy.update_for_success()
        return
    
    # -------------------------
    # CLEAR statement
    # -------------------------
    if isinstance(stmt, Clear):
        for target in stmt.targets:
            if isinstance(target, Var):
                # Set to type's initial value
                env.set_variable(target.name, "", force_create=True)
            elif isinstance(target, Field):
                struct_val = env.get_variable(target.struct)
                if isinstance(struct_val, dict):
                    struct_val[target.field] = ""
                    env.set_variable(target.struct, struct_val, force_create=True)
        env.sy.update_for_success()
        return
    
    # -------------------------
    # MOVE statement
    # -------------------------
    if isinstance(stmt, Move):
        source_val = eval_expr(env, stmt.source)
        
        from .els_parser import Var, Field
        
        if isinstance(stmt.target, Var):
            env.set_variable(stmt.target.name, source_val, force_create=True)
        elif isinstance(stmt.target, Field):
            struct_val = env.get_variable(stmt.target.struct)
            if not isinstance(struct_val, dict):
                struct_val = {}
            struct_val[stmt.target.field] = source_val
            env.set_variable(stmt.target.struct, struct_val, force_create=True)
        
        env.sy.update_for_success()
        return
    
    # -------------------------
    # APPEND (structured)
    # -------------------------
    if isinstance(stmt, Append):
        target = stmt.target_table
        if target not in env.vars.tables:
            env.vars.tables[target] = []
        
        row = {}
        for field, expr in stmt.source_row.items():
            row[field] = eval_expr(env, expr)
        
        env.vars.tables[target].append(row)
        env.sy.update_for_success()
        return
    
    # -------------------------
    # APPEND (simple)
    # -------------------------
    if isinstance(stmt, AppendSimple):
        src = stmt.source_var
        tgt = stmt.target_table
        
        if tgt not in env.vars.tables:
            env.vars.tables[tgt] = []
        
        value = env.get_variable(src)
        if isinstance(value, dict):
            env.vars.tables[tgt].append(value.copy())
        else:
            env.vars.tables[tgt].append(value)
        
        env.sy.update_for_success()
        return
    
    # -------------------------
    # MODIFY TABLE
    # -------------------------
    if isinstance(stmt, ModifyTable):
        table_name = stmt.table_name
        if table_name not in env.vars.tables:
            env.vars.tables[table_name] = []
        
        table = env.vars.tables[table_name]
        source_data = env.get_variable(stmt.from_var)
        
        if not isinstance(source_data, dict):
            env.sy.update_for_error()
            return
        
        key_field = stmt.key_field
        found = False
        
        for i, row in enumerate(table):
            match = True
            if key_field:
                # Match by key field
                if row.get(key_field) != source_data.get(key_field):
                    match = False
            else:
                # Match all fields that exist in source
                for k, v in source_data.items():
                    if k in row and row[k] != v:
                        match = False
                        break
            
            if match:
                # Update the row
                table[i].update(source_data)
                found = True
                break
        
        if found:
            env.sy.update_for_success()
        else:
            # If not found, append
            env.vars.tables[table_name].append(source_data.copy())
            env.sy.update_for_success()
        return
    
    # -------------------------
    # DELETE TABLE
    # -------------------------
    if isinstance(stmt, DeleteTable):
        table_name = stmt.table_name
        if table_name not in env.vars.tables:
            env.vars.tables[table_name] = []
        
        table = env.vars.tables[table_name]
        
        if stmt.key:
            key_field, key_expr = stmt.key
            key_value = eval_expr(env, key_expr)
            
            # Find and remove matching rows
            original_len = len(table)
            env.vars.tables[table_name] = [
                row for row in table 
                if not (isinstance(row, dict) and row.get(key_field) == key_value)
            ]
            
            if len(env.vars.tables[table_name]) < original_len:
                env.sy.update_for_success()
            else:
                env.sy.update_for_not_found()
        else:
            # Delete all rows
            env.vars.tables[table_name] = []
            env.sy.update_for_success()
        return
    
    # -------------------------
    # INSERT TABLE
    # -------------------------
    if isinstance(stmt, InsertTable):
        tgt = stmt.target_table
        if tgt not in env.vars.tables:
            env.vars.tables[tgt] = []
        
        src = stmt.source_var
        value = env.get_variable(src)
        
        # Check if already exists (simple check)
        table = env.vars.tables[tgt]
        if value in table:
            env.sy.update_for_error()
        else:
            if isinstance(value, dict):
                table.append(value.copy())
            else:
                table.append(value)
            env.sy.update_for_success()
        return
    
    # -------------------------
    # EXIT statement
    # -------------------------
    if isinstance(stmt, Exit):
        if env.loop_stack:
            env.current_loop()['should_exit'] = True
        return
    
    # -------------------------
    # CONTINUE statement
    # -------------------------
    if isinstance(stmt, Continue):
        if env.loop_stack:
            env.current_loop()['should_continue'] = True
        return
    
    # -------------------------
    # CHECK statement
    # -------------------------
    if isinstance(stmt, Check):
        condition = eval_expr(env, stmt.condition)
        if not validate_boolean_condition(condition, "CHECK"):
            return
        if not condition:
            if env.loop_stack:
                env.current_loop()['should_continue'] = True
        return
    
    # -------------------------
    # LOOP AT
    # -------------------------
    if isinstance(stmt, LoopAt):
        table_name = stmt.table
        if table_name not in env.vars.tables:
            env.vars.tables[table_name] = []
        
        itab = env.vars.tables[table_name]
        
        # Push loop context
        env.push_loop()
        env.sy.reset_loop_vars()
        
        # Save variable state before loop
        var_state = env.vars.save_state()
        
        for idx, row in enumerate(itab):
            env.sy.set('sy-tabix', idx + 1)
            env.sy.set('sy-index', idx + 1)
            
            # Set loop variable
            if isinstance(row, dict):
                env.set_variable(stmt.into, row.copy(), force_create=True)
            else:
                env.set_variable(stmt.into, row, force_create=True)
            
            # Execute loop body
            for inner_stmt in stmt.body:
                exec_statement(env, inner_stmt)
                
                # Check if should exit or continue
                should_exit, should_continue = env.check_loop_control()
                if should_exit:
                    break
                if should_continue:
                    continue
            
            if env.current_loop() and env.current_loop().get('should_exit'):
                break
            
            # Restore variable state for next iteration (except loop variable)
            env.vars.restore_state(var_state)
        
        # Pop loop context
        env.pop_loop()
        env.sy.reset_loop_vars()
        return
    
    # -------------------------
    # AT NEW control break
    # -------------------------
    if isinstance(stmt, AtNew):
        # Get current value of the field
        current_val = env.get_variable(stmt.field)
        prev_key = f"at_new_{stmt.field}"
        prev_val = env.control_break_data.get(prev_key)
        
        if prev_val is None or prev_val != current_val:
            # Execute AT NEW body
            for s in stmt.body:
                exec_statement(env, s)
            
            # Update stored value
            env.control_break_data[prev_key] = current_val
        return
    
    # -------------------------
    # AT END OF control break
    # -------------------------
    if isinstance(stmt, AtEndOf):
        # For simplicity, always execute AT END OF
        # In real ABAP, this would need lookahead
        for s in stmt.body:
            exec_statement(env, s)
        return
    
    # -------------------------
    # READ TABLE
    # -------------------------
    if isinstance(stmt, ReadTable):
        table_name = stmt.table_name
        if table_name not in env.vars.tables:
            env.vars.tables[table_name] = []
        
        itab = env.vars.tables[table_name]
        found = False
        
        for idx, row in enumerate(itab):
            match = True
            
            if stmt.key:
                key_field, key_expr = stmt.key
                expected_value = eval_expr(env, key_expr)
                
                if not isinstance(row, dict) or row.get(key_field) != expected_value:
                    match = False
            
            if match:
                found = True
                env.sy.set('sy-subrc', 0)
                env.sy.set('sy-tabix', idx + 1)
                
                if stmt.into:
                    if isinstance(row, dict):
                        env.set_variable(stmt.into, row.copy(), force_create=True)
                    else:
                        env.set_variable(stmt.into, row, force_create=True)
                break
        
        if not found:
            env.sy.set('sy-subrc', 4)
            env.sy.set('sy-tabix', 0)
        return
    
    # -------------------------
    # IF statement
    # -------------------------
    if isinstance(stmt, If):
        cond = eval_expr(env, stmt.cond)
        if validate_boolean_condition(cond, "IF") and cond:
            for s in stmt.then_body:
                exec_statement(env, s)
            return
        
        for elif_cond, elif_body in stmt.elif_list:
            cond_val = eval_expr(env, elif_cond)
            if validate_boolean_condition(cond_val, "ELSEIF") and cond_val:
                for s in elif_body:
                    exec_statement(env, s)
                return
        
        for s in stmt.else_body:
            exec_statement(env, s)
        return
    
    # -------------------------
    # WHILE statement
    # -------------------------
    if isinstance(stmt, While):
        # Push loop context
        env.push_loop()
        
        iteration_limit = env.max_loop_iterations
        iterations = 0
        
        # Save variable state before loop
        var_state = env.vars.save_state()
        
        while iterations < iteration_limit:
            iterations += 1
            cond = eval_expr(env, stmt.cond)
            if not validate_boolean_condition(cond, "WHILE") or not cond:
                break
            
            # Execute loop body
            for s in stmt.body:
                exec_statement(env, s)
                
                # Check loop control
                should_exit, should_continue = env.check_loop_control()
                if should_exit:
                    env.current_loop()['should_exit'] = False
                    break
                if should_continue:
                    continue
            
            if env.current_loop() and env.current_loop().get('should_exit'):
                env.current_loop()['should_exit'] = False
                break
            
            # Restore variable state for next iteration
            env.vars.restore_state(var_state)
        
        if iterations >= iteration_limit:
            raise RuntimeError("WHILE loop exceeded maximum iteration limit")
        
        # Pop loop context
        env.pop_loop()
        return
    
    # -------------------------
    # DO statement
    # -------------------------
    if isinstance(stmt, Do):
        times = 1
        if stmt.times_expr:
            times_val = eval_expr(env, stmt.times_expr)
            times = int(times_val) if times_val else 1
        
        # Add iteration limit check
        if times > env.max_loop_iterations:
            raise RuntimeError(f"DO loop exceeds maximum iteration limit: {times} > {env.max_loop_iterations}")
        
        # Push loop context
        env.push_loop()
        
        # Save variable state before loop
        var_state = env.vars.save_state()
        
        for i in range(times):
            env.sy.set('sy-index', i + 1)
            
            # Execute loop body
            for s in stmt.body:
                exec_statement(env, s)
                
                # Check loop control
                should_exit, should_continue = env.check_loop_control()
                if should_exit:
                    env.current_loop()['should_exit'] = False
                    break
                if should_continue:
                    continue
            
            if env.current_loop() and env.current_loop().get('should_exit'):
                env.current_loop()['should_exit'] = False
                break
            
            # Restore variable state for next iteration
            env.vars.restore_state(var_state)
        
        env.sy.set('sy-index', 0)
        
        # Pop loop context
        env.pop_loop()
        return
    
    # -------------------------
    # CASE statement
    # -------------------------
    if isinstance(stmt, Case):
        value = eval_expr(env, stmt.expr)
        
        for case_val, case_body in stmt.cases:
            case_eval = eval_expr(env, case_val)
            if value == case_eval:
                for s in case_body:
                    exec_statement(env, s)
                return
        
        # WHEN OTHERS
        for s in stmt.others_body:
            exec_statement(env, s)
        return
    
    # -------------------------
    # SELECT statement
    # -------------------------
    if isinstance(stmt, SelectInto):
        src_table = env.db.get(stmt.table_name, [])
        result = []
        
        for row in src_table:
            # Apply WHERE clause if present
            if stmt.where:
                try:
                    where_result = eval_where_with_row(env, stmt.where, row)
                    if not where_result:
                        continue
                except:
                    continue
            
            # Select fields
            if stmt.fields == ["*"]:
                filtered_row = row.copy()
            else:
                filtered_row = {field: row.get(field, '') for field in stmt.fields}
            
            result.append(filtered_row)
        
        # Apply ORDER BY if specified
        if stmt.order_by and result:
            def get_sort_key(row):
                keys = []
                for field in stmt.order_by:
                    value = row.get(field, '')
                    # Try numeric sort first
                    try:
                        keys.append(float(value))
                    except:
                        keys.append(str(value))
                return tuple(keys)
            
            result.sort(key=get_sort_key)
        
        env.vars.tables[stmt.into_table] = result
        env.sy.set('sy-dbcnt', len(result))
        env.sy.set('sy-subrc', 0 if len(result) > 0 else 4)
        return
    
    # -------------------------
    # UPDATE SQL
    # -------------------------
    if isinstance(stmt, UpdateSQL):
        table_name = stmt.table_name
        if table_name not in env.db:
            env.sy.update_for_error()
            return
        
        set_values = {}
        for field, expr in stmt.set_clause.items():
            set_values[field] = eval_expr(env, expr)
        
        rows_updated = 0
        
        for row in env.db[table_name]:
            match = True
            
            if stmt.where:
                try:
                    where_result = eval_where_with_row(env, stmt.where, row)
                    if not where_result:
                        match = False
                except:
                    match = False
            
            if match:
                row.update(set_values)
                rows_updated += 1
        
        env.sy.set('sy-dbcnt', rows_updated)
        env.sy.update_for_success() if rows_updated > 0 else env.sy.update_for_not_found()
        return
    
    # -------------------------
    # INSERT SQL
    # -------------------------
    if isinstance(stmt, InsertSQL):
        table_name = stmt.table_name
        if table_name not in env.db:
            env.db[table_name] = []
        
        row = {}
        for field, expr in stmt.values.items():
            row[field] = eval_expr(env, expr)
        
        env.db[table_name].append(row)
        env.sy.set('sy-dbcnt', 1)
        env.sy.update_for_success()
        return
    
    # -------------------------
    # DELETE SQL
    # -------------------------
    if isinstance(stmt, DeleteSQL):
        table_name = stmt.table_name
        if table_name not in env.db:
            env.sy.update_for_error()
            return
        
        rows_deleted = 0
        new_rows = []
        
        for row in env.db[table_name]:
            match = True
            
            if stmt.where:
                try:
                    where_result = eval_where_with_row(env, stmt.where, row)
                    if not where_result:
                        match = False
                except:
                    match = False
            
            if match:
                rows_deleted += 1
            else:
                new_rows.append(row)
        
        env.db[table_name] = new_rows
        env.sy.set('sy-dbcnt', rows_deleted)
        env.sy.update_for_success() if rows_deleted > 0 else env.sy.update_for_not_found()
        return
    
    # -------------------------
    # COMMIT WORK
    # -------------------------
    if isinstance(stmt, CommitWork):
        env._save_db_snapshot()
        return
    
    # -------------------------
    # ROLLBACK WORK
    # -------------------------
    if isinstance(stmt, RollbackWork):
        env._restore_db_snapshot()
        return


def execute_program(program: 'Program', input_params: Dict[str, Any] = None) -> str:
    """Execute entire program and return output"""
    env = RuntimeEnv()
    
    # Apply input parameters if provided
    if input_params:
        for name, value in input_params.items():
            env.vars.parameters[name] = value
            env.set_variable(name, value, force_create=True)
    
    # Two-phase execution
    declaration_statements = []
    execution_statements = []
    in_execution_phase = False
    
    for stmt in program.statements:
        from .els_parser import StartOfSelection
        if isinstance(stmt, StartOfSelection):
            in_execution_phase = True
            execution_statements.append(stmt)
        elif in_execution_phase:
            execution_statements.append(stmt)
        else:
            declaration_statements.append(stmt)
    
    # Execute declaration phase
    for stmt in declaration_statements:
        try:
            exec_statement(env, stmt)
        except RuntimeError as e:
            raise RuntimeError(f"Runtime error in declaration phase: {e}")
    
    # Execute execution phase
    for stmt in execution_statements:
        try:
            exec_statement(env, stmt)
        except RuntimeError as e:
            raise RuntimeError(f"Runtime error in execution phase: {e}")
    
    # Join output
    return "".join(env.output)


# =====================================================
# ===============   PUBLIC API   ======================
# =====================================================

def extract_sia_block(code: str) -> str:
    """Extract content inside *sia ... sia*"""
    start = code.find("*sia")
    end = code.rfind("sia*")
    
    if start == -1 or end == -1:
        raise RuntimeError(
            "Missing SIA wrapper. Expected code inside:\n"
            "*sia\n"
            "   ... ABAP code ...\n"
            "sia*"
        )
    
    inner = code[start + 4:end].strip()
    return inner


def run(code: str, input_params: Dict[str, Any] = None) -> str:
    """Execute ABAP code inside *sia ... sia*"""
    try:
        from .els_parser import tokenize_abap, FullParser
        src = extract_sia_block(code)
        tokens = tokenize_abap(src)
        parser = FullParser(tokens)
        program = parser.parse_program()
        
        output = execute_program(program, input_params)
        return output
        
    except Exception as e:
        raise RuntimeError(f"[ERROR] {e}")


def run_file(path: str, input_params: Dict[str, Any] = None) -> str:
    """Run ABAP code from a file"""
    with open(path, "r", encoding="utf-8") as f:
        return run(f.read(), input_params)


def safe_run(code: str, input_params: Dict[str, Any] = None) -> Optional[str]:
    """Same as run(), but traps errors cleanly"""
    try:
        return run(code, input_params)
    except Exception as e:
        print(f"[SIA-ELS ERROR] {e}")
        return None


def repl():
    """Interactive REPL shell for SIA-ELS"""
    print("SIA Enterprise Logic Studio - REPL (Version 5.0 - Fixed Semantics)")
    print("Enter ABAP code inside *sia ... sia* blocks.")
    print("Type ':quit' to exit.")
    print("Type ':params key=value' to set parameters (e.g., ':params p_dept=IT').")
    print("Type ':selopt name=value' to set SELECT-OPTIONS (e.g., ':selopt s_salary=50000').\n")
    
    buffer = []
    recording = False
    input_params = {}
    select_options = {}
    
    while True:
        try:
            line = input("ELS> ").rstrip("\n")
            
            if line == ":quit":
                break
            
            if line.startswith(":params"):
                parts = line.split()
                for param in parts[1:]:
                    if "=" in param:
                        key, value = param.split("=", 1)
                        input_params[key] = value
                print(f"Parameters set: {input_params}")
                continue
            
            if line.startswith(":selopt"):
                parts = line.split()
                for param in parts[1:]:
                    if "=" in param:
                        key, value = param.split("=", 1)
                        select_options[key] = value
                print(f"SELECT-OPTIONS set: {select_options}")
                continue
            
            if "*sia" in line:
                recording = True
                buffer = [line]
                
                if "sia*" in line:
                    code = "\n".join(buffer)
                    all_params = {**input_params, **select_options}
                    output = safe_run(code, all_params)
                    if output:
                        print(output, end="")
                    recording = False
                    buffer = []
                
                continue
            
            if recording:
                buffer.append(line)
                
                if "sia*" in line:
                    code = "\n".join(buffer)
                    all_params = {**input_params, **select_options}
                    output = safe_run(code, all_params)
                    if output:
                        print(output, end="")
                    recording = False
                    buffer = []
                
                continue
            
            print("Use *sia ... sia* to execute code.")
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except EOFError:
            print("\nExiting...")
            break


if __name__ == "__main__":
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        try:
            params = {}
            if len(sys.argv) > 2 and sys.argv[2] == "--params":
                param_file = sys.argv[3] if len(sys.argv) > 3 else "params.json"
                try:
                    with open(param_file, "r") as f:
                        params = json.load(f)
                except:
                    print(f"Could not load parameters from {param_file}")
            
            output = run_file(filename, params)
            print(output, end="")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        repl()