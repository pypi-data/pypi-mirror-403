"""
Z3 SMT Solver wrapper for direct constraint solving.
Provides both high-level logic program parsing and direct Z3 API access.
"""

from collections import OrderedDict
from typing import Optional, Tuple, List, Dict, Any, Union
import io
import sys
from contextlib import redirect_stdout, redirect_stderr

try:
    from z3 import (
        Solver, sat, unsat, unknown,
        Int, Ints, Real, Reals, Bool, Bools,
        IntSort, RealSort, BoolSort, BitVecSort, ArraySort,
        And, Or, Not, Implies, Xor, If,
        ForAll, Exists,
        Function, Const, Array, BitVec, BitVecs,
        Distinct, Sum, Product,
        simplify, solve, prove,
        EnumSort, Datatype,
        IntVal, RealVal, BoolVal, BitVecVal,
        is_true, is_false,
        set_param, get_param,
    )
    Z3_AVAILABLE = True
except ImportError:
    Z3_AVAILABLE = False

from .translator import CodeTranslator


class Z3SolverError(Exception):
    """Exception raised for Z3 solver errors."""
    pass


class Z3DirectSolver:
    """Direct Z3 solver wrapper for SMT-LIB and Python Z3 code execution."""

    def __init__(self, timeout_ms: int = 30000):
        """Initialize the solver with optional timeout."""
        if not Z3_AVAILABLE:
            raise Z3SolverError("Z3 solver is not installed. Please install z3-solver package.")
        self.timeout_ms = timeout_ms
        self.solver = Solver()
        self.solver.set("timeout", timeout_ms)
        self._variables: Dict[str, Any] = {}
        self._constraints: List[Any] = []

    def reset(self):
        """Reset the solver state."""
        self.solver.reset()
        self._variables = {}
        self._constraints = []

    def add_variable(self, name: str, var_type: str, **kwargs) -> str:
        """Add a variable to the solver context.

        Args:
            name: Variable name
            var_type: Type of variable (int, real, bool, bitvec, array)
            **kwargs: Additional arguments (e.g., bits for bitvec)

        Returns:
            String representation of the created variable
        """
        if var_type == "int":
            self._variables[name] = Int(name)
        elif var_type == "real":
            self._variables[name] = Real(name)
        elif var_type == "bool":
            self._variables[name] = Bool(name)
        elif var_type == "bitvec":
            bits = kwargs.get("bits", 32)
            self._variables[name] = BitVec(name, bits)
        else:
            raise Z3SolverError(f"Unknown variable type: {var_type}")

        return f"Created {var_type} variable: {name}"

    def add_constraint(self, constraint_str: str) -> str:
        """Add a constraint to the solver.

        Args:
            constraint_str: Z3 Python constraint expression as string

        Returns:
            Confirmation message
        """
        # Create a namespace with Z3 functions and user variables
        namespace = {
            'And': And, 'Or': Or, 'Not': Not, 'Implies': Implies, 'Xor': Xor, 'If': If,
            'ForAll': ForAll, 'Exists': Exists,
            'Distinct': Distinct, 'Sum': Sum, 'Product': Product,
            'Int': Int, 'Real': Real, 'Bool': Bool,
            'IntSort': IntSort, 'RealSort': RealSort, 'BoolSort': BoolSort,
            'IntVal': IntVal, 'RealVal': RealVal, 'BoolVal': BoolVal,
            'sat': sat, 'unsat': unsat, 'unknown': unknown,
            **self._variables
        }

        try:
            constraint = eval(constraint_str, {"__builtins__": {}}, namespace)
            self.solver.add(constraint)
            self._constraints.append(constraint_str)
            return f"Added constraint: {constraint_str}"
        except Exception as e:
            raise Z3SolverError(f"Failed to add constraint: {e}")

    def check(self) -> Tuple[str, Optional[str]]:
        """Check satisfiability of current constraints.

        Returns:
            Tuple of (result, model_or_none)
        """
        result = self.solver.check()

        if result == sat:
            model = self.solver.model()
            model_str = "\n".join([f"{d.name()} = {model[d]}" for d in model.decls()])
            return "sat", model_str
        elif result == unsat:
            return "unsat", None
        else:
            return "unknown", None

    def get_model(self) -> Optional[str]:
        """Get the model if satisfiable."""
        if self.solver.check() == sat:
            model = self.solver.model()
            return "\n".join([f"{d.name()} = {model[d]}" for d in model.decls()])
        return None

    def push(self):
        """Push a new context onto the solver stack."""
        self.solver.push()

    def pop(self):
        """Pop a context from the solver stack."""
        self.solver.pop()


class SMTLibSolver:
    """Solver for SMT-LIB format input."""

    def __init__(self, timeout_ms: int = 30000):
        if not Z3_AVAILABLE:
            raise Z3SolverError("Z3 solver is not installed. Please install z3-solver package.")
        self.timeout_ms = timeout_ms

    def solve_smtlib(self, smtlib_code: str) -> str:
        """Solve an SMT-LIB format problem.

        Args:
            smtlib_code: SMT-LIB 2.0 format code

        Returns:
            Solver output
        """
        from z3 import parse_smt2_string, Solver

        try:
            solver = Solver()
            solver.set("timeout", self.timeout_ms)

            # Parse the SMT-LIB code
            assertions = parse_smt2_string(smtlib_code)
            solver.add(assertions)

            result = solver.check()

            if result == sat:
                model = solver.model()
                model_lines = [f"{d.name()} = {model[d]}" for d in model.decls()]
                return f"sat\nModel:\n" + "\n".join(model_lines)
            elif result == unsat:
                return "unsat"
            else:
                return "unknown"
        except Exception as e:
            raise Z3SolverError(f"SMT-LIB parsing/solving error: {e}")


class LogicProgramSolver:
    """Solver for structured logic programs (Logic-LLM format)."""

    def __init__(self, timeout_ms: int = 30000):
        if not Z3_AVAILABLE:
            raise Z3SolverError("Z3 solver is not installed. Please install z3-solver package.")
        self.timeout_ms = timeout_ms
        self.logic_program: Optional[str] = None
        self.standard_code: Optional[str] = None
        self.flag: bool = False

        # Parsed components
        self.declared_enum_sorts: OrderedDict = OrderedDict()
        self.declared_int_sorts: OrderedDict = OrderedDict()
        self.declared_lists: OrderedDict = OrderedDict()
        self.declared_int_lists: OrderedDict = OrderedDict()
        self.declared_functions: OrderedDict = OrderedDict()
        self.variable_constraints: List[str] = []
        self.constraints: List[str] = []

    def parse_logic_program(self, logic_program: str) -> bool:
        """Parse a structured logic program.

        Args:
            logic_program: Logic program with sections for Declarations, Constraints

        Returns:
            True if parsing succeeded
        """
        self.logic_program = logic_program

        try:
            lines = [x for x in logic_program.splitlines() if x.strip()]

            # Find section indices
            declaration_start = None
            constraint_start = None

            for i, line in enumerate(lines):
                if "# Declarations" in line or "#Declarations" in line:
                    declaration_start = i
                elif "# Constraints" in line or "#Constraints" in line:
                    constraint_start = i

            if declaration_start is None:
                # Simple mode: treat all lines as constraints
                self.constraints = [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]
            else:
                if constraint_start is None:
                    constraint_start = len(lines)

                declaration_statements = lines[declaration_start + 1:constraint_start]
                constraint_statements = lines[constraint_start + 1:]

                self._parse_declarations(declaration_statements)
                self.constraints = [x.split(':::')[0].strip() for x in constraint_statements if x.strip()]

            self.flag = True
            return True
        except Exception as e:
            self.flag = False
            raise Z3SolverError(f"Failed to parse logic program: {e}")

    def _parse_declarations(self, declaration_statements: List[str]):
        """Parse declaration statements."""
        enum_sort_declarations = OrderedDict()
        int_sort_declarations = OrderedDict()
        function_declarations = OrderedDict()

        pure_declarations = [x for x in declaration_statements if "Sort" in x or "Function" in x]
        self.variable_constraints = [x for x in declaration_statements if "Sort" not in x and "Function" not in x]

        for s in pure_declarations:
            s = s.strip()
            if "EnumSort" in s:
                sort_name = s.split("=")[0].strip()
                sort_member_str = s.split("=")[1].strip()
                start = sort_member_str.find("(") + 1
                end = sort_member_str.rfind(")")
                inner = sort_member_str[start:end]
                if "[" in inner:
                    start = inner.find("[") + 1
                    end = inner.rfind("]")
                    members_str = inner[start:end]
                else:
                    members_str = inner
                sort_members = [x.strip().strip("'\"") for x in members_str.split(",")]
                enum_sort_declarations[sort_name] = sort_members
            elif "IntSort" in s:
                sort_name = s.split("=")[0].strip()
                sort_member_str = s.split("=")[1].strip()
                start = sort_member_str.find("[") + 1
                end = sort_member_str.rfind("]")
                members_str = sort_member_str[start:end]
                sort_members = [x.strip() for x in members_str.split(",")]
                int_sort_declarations[sort_name] = sort_members
            elif "Function" in s:
                function_name = s.split("=")[0].strip()
                func_str = s.split("=")[1].strip()
                start = func_str.find("(") + 1
                end = func_str.rfind(")")
                args_str = func_str[start:end]
                args_str = args_str.replace("->", ",").replace("[", "").replace("]", "")
                function_args = [x.strip() for x in args_str.split(",")]
                function_declarations[function_name] = function_args

        already_declared = set()
        for name, members in enum_sort_declarations.items():
            if all(x not in already_declared for x in members):
                self.declared_enum_sorts[name] = members
                already_declared.update(members)
            self.declared_lists[name] = members

        self.declared_int_sorts = int_sort_declarations
        for name, members in int_sort_declarations.items():
            self.declared_int_lists[name] = members

        self.declared_functions = function_declarations

    def to_z3_code(self) -> str:
        """Convert parsed logic program to Z3 Python code."""
        if not self.flag:
            raise Z3SolverError("No logic program parsed or parsing failed")

        declaration_lines = []

        # Translate enum sorts
        for name, members in self.declared_enum_sorts.items():
            declaration_lines += CodeTranslator.translate_enum_sort_declaration(name, members)

        # Translate int sorts
        for name, members in self.declared_int_sorts.items():
            declaration_lines += CodeTranslator.translate_int_sort_declaration(name, members)

        # Translate lists
        for name, members in self.declared_lists.items():
            declaration_lines += CodeTranslator.translate_list_declaration(name, members)

        # Build scoped list type mapping
        scoped_list_to_type = {}
        for name, members in self.declared_lists.items():
            if all(x.isdigit() for x in members):
                scoped_list_to_type[name] = CodeTranslator.ListValType.INT
            else:
                scoped_list_to_type[name] = CodeTranslator.ListValType.ENUM

        for name, members in self.declared_int_lists.items():
            scoped_list_to_type[name] = CodeTranslator.ListValType.INT

        # Translate functions
        for name, args in self.declared_functions.items():
            declaration_lines += CodeTranslator.translate_function_declaration(name, args)

        # Translate constraints
        constraint_lines = []
        for constraint in self.constraints:
            constraint_lines += CodeTranslator.translate_constraint(constraint, scoped_list_to_type)

        self.standard_code = CodeTranslator.assemble_solve_code(declaration_lines, constraint_lines)
        return self.standard_code

    def execute(self) -> Tuple[Optional[str], str]:
        """Execute the generated Z3 code and return results.

        Returns:
            Tuple of (result, error_message)
        """
        if not self.standard_code:
            self.to_z3_code()

        # Capture stdout/stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        try:
            # Create execution namespace
            exec_globals = {"__builtins__": __builtins__}

            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec(self.standard_code, exec_globals)

            output = stdout_capture.getvalue().strip()
            error = stderr_capture.getvalue().strip()

            if error:
                return None, error
            return output, ""
        except Exception as e:
            return None, str(e)


def solve_z3_python(code: str, timeout_ms: int = 30000) -> str:
    """Execute Z3 Python code directly.

    Args:
        code: Z3 Python code to execute
        timeout_ms: Timeout in milliseconds

    Returns:
        Output from the code execution
    """
    if not Z3_AVAILABLE:
        raise Z3SolverError("Z3 solver is not installed. Please install z3-solver package.")

    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    # Build execution namespace with Z3 imports
    exec_globals = {
        "__builtins__": __builtins__,
        "Solver": Solver, "sat": sat, "unsat": unsat, "unknown": unknown,
        "Int": Int, "Ints": Ints, "Real": Real, "Reals": Reals,
        "Bool": Bool, "Bools": Bools,
        "IntSort": IntSort, "RealSort": RealSort, "BoolSort": BoolSort,
        "BitVecSort": BitVecSort, "ArraySort": ArraySort,
        "And": And, "Or": Or, "Not": Not, "Implies": Implies, "Xor": Xor, "If": If,
        "ForAll": ForAll, "Exists": Exists,
        "Function": Function, "Const": Const, "Array": Array,
        "BitVec": BitVec, "BitVecs": BitVecs,
        "Distinct": Distinct, "Sum": Sum, "Product": Product,
        "simplify": simplify, "solve": solve, "prove": prove,
        "EnumSort": EnumSort, "Datatype": Datatype,
        "IntVal": IntVal, "RealVal": RealVal, "BoolVal": BoolVal, "BitVecVal": BitVecVal,
        "is_true": is_true, "is_false": is_false,
        "set_param": set_param, "get_param": get_param,
    }

    try:
        set_param("timeout", timeout_ms)

        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            exec(code, exec_globals)

        output = stdout_capture.getvalue().strip()
        error = stderr_capture.getvalue().strip()

        if error:
            return f"Error: {error}"
        return output if output else "Execution completed (no output)"
    except Exception as e:
        return f"Execution error: {e}"
