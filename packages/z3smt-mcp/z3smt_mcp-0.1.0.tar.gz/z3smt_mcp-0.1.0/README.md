# Z3/SMT MCP Server

An MCP (Model Context Protocol) server that exposes Z3/SMT solver capabilities for constraint solving, logical reasoning, and satisfiability checking.

## Features

- **Direct Z3 Python code execution** - Run arbitrary Z3 Python code
- **SMT-LIB 2.0 support** - Parse and solve SMT-LIB format problems
- **Constraint checking** - Check satisfiability of constraint lists
- **Theorem proving** - Prove theorems by showing unsatisfiability of negation
- **Expression simplification** - Simplify Z3 expressions
- **Logic program solving** - Parse and solve structured logic programs (Logic-LLM format)
- **Session management** - Incremental solving with push/pop support

## Installation

```bash
# Using pip
pip install z3smt-mcp

# Or install from source
git clone https://github.com/z3smt-mcp/z3smt-mcp
cd z3smt-mcp
pip install -e .
```

### Requirements

- Python >= 3.10
- z3-solver >= 4.12.0
- mcp >= 1.0.0

## Usage

### Running the Server

```bash
# Run directly
z3smt-mcp

# Or via Python
python -m z3smt_mcp.server
```

### Claude Desktop Configuration

Add to your Claude Desktop config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "z3smt": {
      "command": "z3smt-mcp"
    }
  }
}
```

Or if installed from source:

```json
{
  "mcpServers": {
    "z3smt": {
      "command": "python",
      "args": ["-m", "z3smt_mcp.server"]
    }
  }
}
```

## Available Tools

### `solve`

Execute Z3 Python code directly. All Z3 imports are pre-loaded.

```python
# Example: Solve a system of linear equations
x = Int('x')
y = Int('y')
solver = Solver()
solver.add(x + y == 10)
solver.add(x - y == 4)
if solver.check() == sat:
    print(solver.model())
# Output: [y = 3, x = 7]
```

### `solve_smtlib`

Solve problems in SMT-LIB 2.0 format.

```smt2
(declare-const x Int)
(declare-const y Int)
(assert (= (+ x y) 10))
(assert (= (- x y) 4))
(check-sat)
(get-model)
```

### `check_sat`

Check satisfiability of a list of constraints with automatic variable detection.

```json
{
  "constraints": ["x + y == 10", "x > 0", "y > 0", "x < y"]
}
```

### `prove`

Prove a theorem by showing its negation is unsatisfiable.

```json
{
  "theorem": "Implies(And(x > 0, y > 0), x + y > 0)",
  "variables": {"x": "int", "y": "int"}
}
```

### `simplify`

Simplify a Z3 expression.

```json
{
  "expression": "And(x > 0, Or(x > 0, y > 0))"
}
```

### `solve_logic_program`

Solve structured logic programs in Logic-LLM format.

```
# Declarations
Color = EnumSort([red, green, blue])
assign = Function(Object -> Color)

# Constraints
assign(obj1) != assign(obj2)
Distinct([c:Color], assign(c))
```

### Session Management Tools

- `session_add_variable` - Add a variable to the session
- `session_add_constraint` - Add a constraint to the session
- `session_check` - Check satisfiability and get model
- `session_push` - Push a new context (for backtracking)
- `session_pop` - Pop context (backtrack)
- `session_reset` - Clear the session
- `list_sessions` - List all active sessions

## Examples

### Solving Sudoku

```python
# Create a 9x9 grid of integer variables
X = [[Int(f"x_{i}_{j}") for j in range(9)] for i in range(9)]

solver = Solver()

# Each cell contains a value in 1-9
for i in range(9):
    for j in range(9):
        solver.add(And(X[i][j] >= 1, X[i][j] <= 9))

# Each row has distinct values
for i in range(9):
    solver.add(Distinct(X[i]))

# Each column has distinct values
for j in range(9):
    solver.add(Distinct([X[i][j] for i in range(9)]))

# Each 3x3 box has distinct values
for box_i in range(3):
    for box_j in range(3):
        box = [X[3*box_i + i][3*box_j + j]
               for i in range(3) for j in range(3)]
        solver.add(Distinct(box))

# Add known values (example)
solver.add(X[0][0] == 5)
solver.add(X[0][1] == 3)
# ... more constraints

if solver.check() == sat:
    m = solver.model()
    for i in range(9):
        print([m[X[i][j]] for j in range(9)])
```

### Bit-Vector Arithmetic

```python
# Solve for x where x * 3 == 21 in 8-bit arithmetic
x = BitVec('x', 8)
solver = Solver()
solver.add(x * 3 == 21)
if solver.check() == sat:
    print(solver.model())
```

### Array Theory

```python
# Find an array where a[0] + a[1] == 10
a = Array('a', IntSort(), IntSort())
solver = Solver()
solver.add(a[0] + a[1] == 10)
solver.add(a[0] > 0)
solver.add(a[1] > 0)
if solver.check() == sat:
    print(solver.model())
```

## Credits

- Z3 solver implementation adapted from [Logic-LLM](https://github.com/teacherpeterpan/Logic-LLM)
- MCP interface inspired by [clingo-mcp](https://github.com/newjerseystyle/clingo-mcp)
- Z3 Theorem Prover by Microsoft Research

## License

MIT License
