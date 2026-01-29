"""
Code translator for converting logical statements to Z3 Python code.
Adapted from Logic-LLM project (https://github.com/teacherpeterpan/Logic-LLM).
"""

from collections import OrderedDict, namedtuple
from enum import Enum
import re
from typing import List, Tuple, Dict, Any

TAB_STR = "    "


class CodeTranslator:
    """Translates logical statements to Z3 Python code."""

    class LineType(Enum):
        DECL = 1
        CONS = 2

    class ListValType(Enum):
        INT = 1
        ENUM = 2

    StdCodeLine = namedtuple("StdCodeLine", "line line_type")

    @staticmethod
    def translate_enum_sort_declaration(enum_sort_name: str, enum_sort_values: List[str]) -> List["CodeTranslator.StdCodeLine"]:
        """Translate an enum sort declaration to Z3 code."""
        if all(x.isdigit() for x in enum_sort_values):
            return [CodeTranslator.StdCodeLine(f"{enum_sort_name}_sort = IntSort()", CodeTranslator.LineType.DECL)]

        line = "{}, ({}) = EnumSort({}, [{}])".format(
            f"{enum_sort_name}_sort",
            ", ".join(enum_sort_values),
            f"'{enum_sort_name}'",
            ", ".join([f"'{x}'" for x in enum_sort_values])
        )
        return [CodeTranslator.StdCodeLine(line, CodeTranslator.LineType.DECL)]

    @staticmethod
    def translate_int_sort_declaration(int_sort_name: str, int_sort_values: List[str]) -> List["CodeTranslator.StdCodeLine"]:
        """Translate an integer sort declaration to Z3 code."""
        line1 = CodeTranslator.StdCodeLine(f"{int_sort_name}_sort = IntSort()", CodeTranslator.LineType.DECL)
        line2 = "{} = Ints('{}')".format(
            ", ".join([str(x) for x in int_sort_values]),
            " ".join([str(x) for x in int_sort_values])
        )
        line2 = CodeTranslator.StdCodeLine(line2, CodeTranslator.LineType.DECL)

        line3 = "{} = [{}]".format(
            int_sort_name,
            ", ".join([str(x) for x in int_sort_values])
        )
        line3 = CodeTranslator.StdCodeLine(line3, CodeTranslator.LineType.DECL)
        return [line1, line2, line3]

    @staticmethod
    def translate_list_declaration(list_name: str, list_members: List[str]) -> List["CodeTranslator.StdCodeLine"]:
        """Translate a list declaration to Z3 code."""
        line = "{} = [{}]".format(
            list_name,
            ", ".join(list_members),
        )
        return [CodeTranslator.StdCodeLine(line, CodeTranslator.LineType.DECL)]

    @staticmethod
    def type_str_to_type_sort(arg: str) -> str:
        """Convert a type string to a Z3 sort."""
        if arg == "bool":
            return "BoolSort()"
        elif arg == "int":
            return "IntSort()"
        else:
            return f"{arg}_sort"

    @staticmethod
    def translate_function_declaration(function_name: str, function_args: List[str]) -> List["CodeTranslator.StdCodeLine"]:
        """Translate a function declaration to Z3 code."""
        args = []
        for arg in function_args:
            args.append(CodeTranslator.type_str_to_type_sort(arg))

        line = "{} = Function('{}', {})".format(
            function_name,
            function_name,
            ", ".join(args),
        )
        return [CodeTranslator.StdCodeLine(line, CodeTranslator.LineType.DECL)]

    @staticmethod
    def extract_paired_token_index(statement: str, start_index: int, left_token: str, right_token: str) -> int:
        """Find the matching closing token for a given opening token."""
        if statement[start_index] != left_token:
            raise RuntimeError("Invalid argument")

        level = 1
        for i in range(start_index + 1, len(statement)):
            if statement[i] == left_token:
                level += 1
            elif statement[i] == right_token:
                level -= 1
            if level == 0:
                return i
        raise RuntimeError(f"No matching {right_token} found for {left_token}")

    @staticmethod
    def extract_temperal_variable_name_and_scope(scope_contents: str) -> List[List[str]]:
        """Extract variable names and their scopes from a scope string."""
        scope_fragments = [x.strip() for x in scope_contents.split(",")]
        return [x.split(":") for x in scope_fragments]

    @staticmethod
    def handle_count_function(statement: str) -> str:
        """Transform Count function to Z3-compatible Sum expression."""
        index = statement.find("Count(")
        content_start_index = index + len("Count")
        content_end_index = CodeTranslator.extract_paired_token_index(statement, content_start_index, "(", ")")
        count_arg_contents = statement[content_start_index + 1:content_end_index]
        scope_end_index = CodeTranslator.extract_paired_token_index(count_arg_contents, 0, "[", "]")
        scope_contents = count_arg_contents[1:scope_end_index]
        vars_and_scopes = CodeTranslator.extract_temperal_variable_name_and_scope(scope_contents)
        count_expr = count_arg_contents[scope_end_index + 1:].lstrip(", ")

        transformed_count_statement = "Sum([{} {}])".format(
            count_expr,
            " ".join([f"for {var} in {scope}" for var, scope in vars_and_scopes])
        )

        statement = statement[:index] + transformed_count_statement + statement[content_end_index + 1:]
        return statement

    @staticmethod
    def handle_distinct_function(statement: str) -> str:
        """Transform Distinct function to Z3-compatible expression."""
        scoped_distinct_regex = r"Distinct\(\[([a-zA-Z0-9_]+):([a-zA-Z0-9_]"
        match = re.search(scoped_distinct_regex, statement)
        if not match:
            return statement
        index = match.start()
        content_start_index = index + len("Distinct")
        content_end_index = CodeTranslator.extract_paired_token_index(statement, content_start_index, "(", ")")
        distinct_arg_contents = statement[content_start_index + 1:content_end_index]
        scope_end_index = CodeTranslator.extract_paired_token_index(distinct_arg_contents, 0, "[", "]")
        scope_contents = distinct_arg_contents[1:scope_end_index]
        vars_and_scopes = CodeTranslator.extract_temperal_variable_name_and_scope(scope_contents)
        distinct_expr = distinct_arg_contents[scope_end_index + 1:].lstrip(", ")
        assert len(vars_and_scopes) == 1
        transformed_distinct_statement = "Distinct([{} for {} in {}])".format(
            distinct_expr,
            vars_and_scopes[0][0],
            vars_and_scopes[0][1],
        )

        statement = statement[:index] + transformed_distinct_statement + statement[content_end_index + 1:]
        return statement

    @staticmethod
    def handle_quantifier_function(statement: str, scoped_list_to_type: Dict[str, "CodeTranslator.ListValType"]) -> Tuple[List[str], str]:
        """Transform quantifier functions (ForAll, Exists) to Z3-compatible expressions."""
        scoped_quantifier_regex = r"(Exists|ForAll)\(\[([a-zA-Z0-9_]+):([a-zA-Z0-9_]"
        match = re.search(scoped_quantifier_regex, statement)
        if not match:
            return [], statement
        quant_name = match.group(1)

        index = match.start()
        content_start_index = index + len(quant_name)
        content_end_index = CodeTranslator.extract_paired_token_index(statement, content_start_index, "(", ")")
        quant_arg_contents = statement[content_start_index + 1:content_end_index]
        scope_end_index = CodeTranslator.extract_paired_token_index(quant_arg_contents, 0, "[", "]")
        scope_contents = quant_arg_contents[1:scope_end_index]
        vars_and_scopes = CodeTranslator.extract_temperal_variable_name_and_scope(scope_contents)
        quant_expr = quant_arg_contents[scope_end_index + 1:].lstrip(", ")

        var_need_declaration = []
        var_need_compresion = []
        for (var_name, var_scope) in vars_and_scopes:
            if var_scope in scoped_list_to_type:
                if scoped_list_to_type[var_scope] == CodeTranslator.ListValType.ENUM:
                    var_need_declaration.append((var_name, var_scope))
                else:
                    var_need_compresion.append((var_name, var_scope))
            else:
                assert var_scope in ["int", "bool"]
                var_need_declaration.append((var_name, var_scope))

        decl_lines = []
        std_scope = []
        if var_need_declaration:
            for (var_name, var_scope) in var_need_declaration:
                decl_lines.append(f"{var_name} = Const('{var_name}', {CodeTranslator.type_str_to_type_sort(var_scope)})")
                std_scope.append(var_name)
            std_constraint = "{}([{}], {})".format(quant_name, ", ".join(std_scope), quant_expr)
        else:
            std_constraint = quant_expr

        if var_need_compresion:
            logic_f = "And" if quant_name == "ForAll" else "Or"
            std_constraint = "{}([{} {}])".format(
                logic_f, std_constraint,
                " ".join([f"for {var_name} in {var_scope}" for (var_name, var_scope) in var_need_compresion])
            )

        std_constraint = statement[:index] + std_constraint + statement[content_end_index + 1:]
        return decl_lines, std_constraint

    @staticmethod
    def translate_constraint(constraint: str, scoped_list_to_type: Dict[str, "CodeTranslator.ListValType"]) -> List["CodeTranslator.StdCodeLine"]:
        """Translate a constraint to Z3 code."""
        # Handle special operators into standard python operators
        while "Count(" in constraint:
            constraint = CodeTranslator.handle_count_function(constraint)

        scoped_distinct_regex = r"Distinct\(\[([a-zA-Z0-9_]+):([a-zA-Z0-9_]"
        while re.search(scoped_distinct_regex, constraint):
            constraint = CodeTranslator.handle_distinct_function(constraint)

        scoped_quantifier_regex = r"(Exists|ForAll)\(\[([a-zA-Z0-9_]+):([a-zA-Z0-9_]"
        all_decl_lines = []
        while re.search(scoped_quantifier_regex, constraint):
            decl_lines, constraint = CodeTranslator.handle_quantifier_function(constraint, scoped_list_to_type)
            all_decl_lines += decl_lines

        lines = [CodeTranslator.StdCodeLine(l, CodeTranslator.LineType.DECL) for l in all_decl_lines]
        lines.append(CodeTranslator.StdCodeLine(constraint, CodeTranslator.LineType.CONS))
        return lines

    @staticmethod
    def assemble_solve_code(declaration_lines: List["CodeTranslator.StdCodeLine"],
                            constraint_lines: List["CodeTranslator.StdCodeLine"]) -> str:
        """Assemble Z3 code for solving constraints."""
        lines = []

        header_lines = [
            "from z3 import *",
            ""
        ]

        lines += header_lines
        lines += [x.line for x in declaration_lines]
        lines += [""]

        lines += ["solver = Solver()"]
        for line in constraint_lines:
            if line.line_type == CodeTranslator.LineType.DECL:
                lines += [line.line]
            else:
                lines += [f"solver.add({line.line})"]

        lines += [""]
        lines += ["result = solver.check()"]
        lines += ["if result == sat:"]
        lines += [f"{TAB_STR}print('sat')"]
        lines += [f"{TAB_STR}print(solver.model())"]
        lines += ["elif result == unsat:"]
        lines += [f"{TAB_STR}print('unsat')"]
        lines += ["else:"]
        lines += [f"{TAB_STR}print('unknown')"]

        return "\n".join(lines)

    @staticmethod
    def assemble_check_sat_code(declaration_lines: List["CodeTranslator.StdCodeLine"],
                                constraint_lines: List["CodeTranslator.StdCodeLine"]) -> str:
        """Assemble Z3 code for checking satisfiability only."""
        lines = []

        header_lines = [
            "from z3 import *",
            ""
        ]

        lines += header_lines
        lines += [x.line for x in declaration_lines]
        lines += [""]

        lines += ["solver = Solver()"]
        for line in constraint_lines:
            if line.line_type == CodeTranslator.LineType.DECL:
                lines += [line.line]
            else:
                lines += [f"solver.add({line.line})"]

        lines += [""]
        lines += ["result = solver.check()"]
        lines += ["print(str(result))"]

        return "\n".join(lines)
