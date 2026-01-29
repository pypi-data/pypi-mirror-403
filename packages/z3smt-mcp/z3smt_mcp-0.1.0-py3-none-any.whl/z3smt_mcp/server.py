"""
MCP Server for Z3/SMT Solver.

This server exposes Z3 SMT solver capabilities through the Model Context Protocol,
enabling constraint solving, logical reasoning, and satisfiability checking.
"""

import asyncio
import json
from typing import Any, Optional
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    CallToolResult,
)

from .solver import (
    Z3DirectSolver,
    SMTLibSolver,
    LogicProgramSolver,
    solve_z3_python,
    Z3SolverError,
    Z3_AVAILABLE,
)


# Global solver instances for session management
_sessions: dict[str, Z3DirectSolver] = {}


def get_or_create_session(session_id: str = "default") -> Z3DirectSolver:
    """Get or create a solver session."""
    if session_id not in _sessions:
        _sessions[session_id] = Z3DirectSolver()
    return _sessions[session_id]


def clear_session(session_id: str = "default") -> bool:
    """Clear a solver session."""
    if session_id in _sessions:
        _sessions[session_id].reset()
        return True
    return False


def delete_session(session_id: str) -> bool:
    """Delete a solver session entirely."""
    if session_id in _sessions:
        del _sessions[session_id]
        return True
    return False


# Define available tools
TOOLS = [
    Tool(
        name="solve",
        description="""Execute Z3 Python code to solve SMT constraints.

The code can use any Z3 Python API functions. Common imports (Solver, Int, Real, Bool, And, Or, Not, etc.) are pre-loaded.

Example:
```python
x = Int('x')
y = Int('y')
solver = Solver()
solver.add(x + y == 10)
solver.add(x - y == 4)
if solver.check() == sat:
    print(solver.model())
```""",
        inputSchema={
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Z3 Python code to execute"
                },
                "timeout_ms": {
                    "type": "integer",
                    "description": "Timeout in milliseconds (default: 30000)",
                    "default": 30000
                }
            },
            "required": ["code"]
        }
    ),
    Tool(
        name="solve_smtlib",
        description="""Solve an SMT problem in SMT-LIB 2.0 format.

Example:
```
(declare-const x Int)
(declare-const y Int)
(assert (= (+ x y) 10))
(assert (= (- x y) 4))
(check-sat)
(get-model)
```""",
        inputSchema={
            "type": "object",
            "properties": {
                "smtlib_code": {
                    "type": "string",
                    "description": "SMT-LIB 2.0 format code"
                },
                "timeout_ms": {
                    "type": "integer",
                    "description": "Timeout in milliseconds (default: 30000)",
                    "default": 30000
                }
            },
            "required": ["smtlib_code"]
        }
    ),
    Tool(
        name="check_sat",
        description="""Check satisfiability of a list of constraints.

Provide constraints as Z3 Python expressions. Variables will be auto-declared based on usage.

Example constraints:
- "x + y == 10"
- "x > 0"
- "And(x < 100, y < 100)"
""",
        inputSchema={
            "type": "object",
            "properties": {
                "constraints": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of Z3 constraint expressions"
                },
                "variables": {
                    "type": "object",
                    "description": "Variable declarations: {name: type} where type is 'int', 'real', 'bool', or 'bitvec:N'",
                    "additionalProperties": {"type": "string"}
                },
                "timeout_ms": {
                    "type": "integer",
                    "description": "Timeout in milliseconds (default: 30000)",
                    "default": 30000
                }
            },
            "required": ["constraints"]
        }
    ),
    Tool(
        name="prove",
        description="""Attempt to prove a theorem by showing its negation is unsatisfiable.

Provide the theorem as a Z3 expression. If the negation is unsatisfiable, the theorem is proven.

Example: prove "ForAll([x], x + 0 == x)" for integer x
""",
        inputSchema={
            "type": "object",
            "properties": {
                "theorem": {
                    "type": "string",
                    "description": "Z3 expression representing the theorem to prove"
                },
                "variables": {
                    "type": "object",
                    "description": "Variable declarations: {name: type}",
                    "additionalProperties": {"type": "string"}
                },
                "timeout_ms": {
                    "type": "integer",
                    "description": "Timeout in milliseconds (default: 30000)",
                    "default": 30000
                }
            },
            "required": ["theorem"]
        }
    ),
    Tool(
        name="simplify",
        description="""Simplify a Z3 expression.

Returns the simplified form of the given expression.

Example: simplify "And(x > 0, x > 0)" -> "x > 0"
""",
        inputSchema={
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Z3 expression to simplify"
                },
                "variables": {
                    "type": "object",
                    "description": "Variable declarations: {name: type}",
                    "additionalProperties": {"type": "string"}
                }
            },
            "required": ["expression"]
        }
    ),
    Tool(
        name="solve_logic_program",
        description="""Solve a structured logic program (Logic-LLM format).

The program should have sections:
# Declarations
- EnumSort, IntSort, Function declarations

# Constraints
- Logical constraints

Example:
```
# Declarations
Color = EnumSort([red, green, blue])
assign = Function(Object -> Color)

# Constraints
assign(obj1) != assign(obj2)
```
""",
        inputSchema={
            "type": "object",
            "properties": {
                "logic_program": {
                    "type": "string",
                    "description": "Structured logic program"
                },
                "timeout_ms": {
                    "type": "integer",
                    "description": "Timeout in milliseconds (default: 30000)",
                    "default": 30000
                }
            },
            "required": ["logic_program"]
        }
    ),
    Tool(
        name="session_add_variable",
        description="""Add a variable to the current solver session.

Supported types: int, real, bool, bitvec (with bits parameter)
""",
        inputSchema={
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Session identifier (default: 'default')",
                    "default": "default"
                },
                "name": {
                    "type": "string",
                    "description": "Variable name"
                },
                "var_type": {
                    "type": "string",
                    "enum": ["int", "real", "bool", "bitvec"],
                    "description": "Variable type"
                },
                "bits": {
                    "type": "integer",
                    "description": "Bit width for bitvec type (default: 32)",
                    "default": 32
                }
            },
            "required": ["name", "var_type"]
        }
    ),
    Tool(
        name="session_add_constraint",
        description="""Add a constraint to the current solver session.

The constraint should be a valid Z3 expression using previously declared variables.
""",
        inputSchema={
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Session identifier (default: 'default')",
                    "default": "default"
                },
                "constraint": {
                    "type": "string",
                    "description": "Z3 constraint expression"
                }
            },
            "required": ["constraint"]
        }
    ),
    Tool(
        name="session_check",
        description="""Check satisfiability of current session constraints and get the model if satisfiable.""",
        inputSchema={
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Session identifier (default: 'default')",
                    "default": "default"
                }
            }
        }
    ),
    Tool(
        name="session_push",
        description="""Push a new context onto the solver stack (for backtracking).""",
        inputSchema={
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Session identifier (default: 'default')",
                    "default": "default"
                }
            }
        }
    ),
    Tool(
        name="session_pop",
        description="""Pop a context from the solver stack (backtrack).""",
        inputSchema={
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Session identifier (default: 'default')",
                    "default": "default"
                }
            }
        }
    ),
    Tool(
        name="session_reset",
        description="""Reset the current solver session, clearing all variables and constraints.""",
        inputSchema={
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Session identifier (default: 'default')",
                    "default": "default"
                }
            }
        }
    ),
    Tool(
        name="list_sessions",
        description="""List all active solver sessions.""",
        inputSchema={
            "type": "object",
            "properties": {}
        }
    ),
]


def create_variable_declarations(variables: dict[str, str]) -> str:
    """Create Z3 variable declaration code from a variable dict."""
    lines = []
    for name, var_type in variables.items():
        if var_type == "int":
            lines.append(f"{name} = Int('{name}')")
        elif var_type == "real":
            lines.append(f"{name} = Real('{name}')")
        elif var_type == "bool":
            lines.append(f"{name} = Bool('{name}')")
        elif var_type.startswith("bitvec:"):
            bits = int(var_type.split(":")[1])
            lines.append(f"{name} = BitVec('{name}', {bits})")
        else:
            lines.append(f"{name} = Int('{name}')")  # Default to int
    return "\n".join(lines)


async def handle_tool_call(name: str, arguments: dict[str, Any]) -> str:
    """Handle a tool call and return the result."""

    if not Z3_AVAILABLE:
        return "Error: Z3 solver is not installed. Please install z3-solver package."

    try:
        if name == "solve":
            code = arguments["code"]
            timeout_ms = arguments.get("timeout_ms", 30000)
            result = solve_z3_python(code, timeout_ms)
            return result

        elif name == "solve_smtlib":
            smtlib_code = arguments["smtlib_code"]
            timeout_ms = arguments.get("timeout_ms", 30000)
            solver = SMTLibSolver(timeout_ms)
            result = solver.solve_smtlib(smtlib_code)
            return result

        elif name == "check_sat":
            constraints = arguments["constraints"]
            variables = arguments.get("variables", {})
            timeout_ms = arguments.get("timeout_ms", 30000)

            # Build code
            code_lines = [create_variable_declarations(variables)] if variables else []

            # Auto-detect variables if not provided
            if not variables:
                # Simple heuristic: find identifiers that look like variables
                import re
                all_vars = set()
                for c in constraints:
                    # Find potential variable names (simple identifiers not in Z3 keywords)
                    identifiers = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', c)
                    z3_keywords = {'And', 'Or', 'Not', 'Implies', 'Xor', 'If', 'ForAll', 'Exists',
                                   'Distinct', 'Sum', 'Product', 'Int', 'Real', 'Bool', 'True', 'False'}
                    all_vars.update(v for v in identifiers if v not in z3_keywords)

                for var in all_vars:
                    code_lines.append(f"{var} = Int('{var}')")

            code_lines.append("solver = Solver()")
            for constraint in constraints:
                code_lines.append(f"solver.add({constraint})")

            code_lines.append("result = solver.check()")
            code_lines.append("if result == sat:")
            code_lines.append("    print('sat')")
            code_lines.append("    print(solver.model())")
            code_lines.append("elif result == unsat:")
            code_lines.append("    print('unsat')")
            code_lines.append("else:")
            code_lines.append("    print('unknown')")

            code = "\n".join(code_lines)
            result = solve_z3_python(code, timeout_ms)
            return result

        elif name == "prove":
            theorem = arguments["theorem"]
            variables = arguments.get("variables", {})
            timeout_ms = arguments.get("timeout_ms", 30000)

            code_lines = [create_variable_declarations(variables)] if variables else []

            # Auto-detect variables
            if not variables:
                import re
                identifiers = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', theorem)
                z3_keywords = {'And', 'Or', 'Not', 'Implies', 'Xor', 'If', 'ForAll', 'Exists',
                               'Distinct', 'Sum', 'Product', 'Int', 'Real', 'Bool', 'True', 'False'}
                for var in set(identifiers) - z3_keywords:
                    code_lines.append(f"{var} = Int('{var}')")

            code_lines.append("solver = Solver()")
            code_lines.append(f"solver.add(Not({theorem}))")
            code_lines.append("result = solver.check()")
            code_lines.append("if result == unsat:")
            code_lines.append("    print('proved')")
            code_lines.append("elif result == sat:")
            code_lines.append("    print('counterexample found:')")
            code_lines.append("    print(solver.model())")
            code_lines.append("else:")
            code_lines.append("    print('unknown')")

            code = "\n".join(code_lines)
            result = solve_z3_python(code, timeout_ms)
            return result

        elif name == "simplify":
            expression = arguments["expression"]
            variables = arguments.get("variables", {})

            code_lines = [create_variable_declarations(variables)] if variables else []

            # Auto-detect variables
            if not variables:
                import re
                identifiers = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', expression)
                z3_keywords = {'And', 'Or', 'Not', 'Implies', 'Xor', 'If', 'ForAll', 'Exists',
                               'Distinct', 'Sum', 'Product', 'Int', 'Real', 'Bool', 'True', 'False'}
                for var in set(identifiers) - z3_keywords:
                    code_lines.append(f"{var} = Int('{var}')")

            code_lines.append(f"result = simplify({expression})")
            code_lines.append("print(result)")

            code = "\n".join(code_lines)
            result = solve_z3_python(code)
            return result

        elif name == "solve_logic_program":
            logic_program = arguments["logic_program"]
            timeout_ms = arguments.get("timeout_ms", 30000)

            solver = LogicProgramSolver(timeout_ms)
            solver.parse_logic_program(logic_program)
            z3_code = solver.to_z3_code()
            result, error = solver.execute()

            if error:
                return f"Error: {error}\n\nGenerated Z3 code:\n{z3_code}"
            return f"Result: {result}\n\nGenerated Z3 code:\n{z3_code}"

        elif name == "session_add_variable":
            session_id = arguments.get("session_id", "default")
            var_name = arguments["name"]
            var_type = arguments["var_type"]
            bits = arguments.get("bits", 32)

            session = get_or_create_session(session_id)
            result = session.add_variable(var_name, var_type, bits=bits)
            return result

        elif name == "session_add_constraint":
            session_id = arguments.get("session_id", "default")
            constraint = arguments["constraint"]

            session = get_or_create_session(session_id)
            result = session.add_constraint(constraint)
            return result

        elif name == "session_check":
            session_id = arguments.get("session_id", "default")

            session = get_or_create_session(session_id)
            result, model = session.check()

            if model:
                return f"Result: {result}\nModel:\n{model}"
            return f"Result: {result}"

        elif name == "session_push":
            session_id = arguments.get("session_id", "default")
            session = get_or_create_session(session_id)
            session.push()
            return f"Pushed new context onto session '{session_id}'"

        elif name == "session_pop":
            session_id = arguments.get("session_id", "default")
            session = get_or_create_session(session_id)
            session.pop()
            return f"Popped context from session '{session_id}'"

        elif name == "session_reset":
            session_id = arguments.get("session_id", "default")
            clear_session(session_id)
            return f"Reset session '{session_id}'"

        elif name == "list_sessions":
            if not _sessions:
                return "No active sessions"
            session_info = []
            for sid, solver in _sessions.items():
                info = f"- {sid}: {len(solver._constraints)} constraints, {len(solver._variables)} variables"
                session_info.append(info)
            return "Active sessions:\n" + "\n".join(session_info)

        else:
            return f"Unknown tool: {name}"

    except Z3SolverError as e:
        return f"Solver error: {e}"
    except Exception as e:
        return f"Error: {e}"


@asynccontextmanager
async def server_lifespan(server: Server) -> AsyncIterator[dict[str, Any]]:
    """Server lifespan context manager."""
    # Startup
    yield {"sessions": _sessions}
    # Shutdown
    _sessions.clear()


def create_server() -> Server:
    """Create and configure the MCP server."""
    server = Server("z3smt-mcp", lifespan=server_lifespan)

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return TOOLS

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        result = await handle_tool_call(name, arguments)
        return [TextContent(type="text", text=result)]

    return server


async def run_server():
    """Run the MCP server."""
    server = create_server()
    options = server.create_initialization_options()

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options)


def main():
    """Main entry point."""
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
