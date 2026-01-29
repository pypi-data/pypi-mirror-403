"""Tests for the Z3 SMT solver wrapper."""

import pytest
from z3smt_mcp.solver import (
    Z3DirectSolver,
    SMTLibSolver,
    LogicProgramSolver,
    solve_z3_python,
    Z3SolverError,
    Z3_AVAILABLE,
)


pytestmark = pytest.mark.skipif(not Z3_AVAILABLE, reason="Z3 not installed")


class TestZ3DirectSolver:
    """Tests for Z3DirectSolver class."""

    def test_basic_solve(self):
        """Test basic constraint solving."""
        solver = Z3DirectSolver()
        solver.add_variable("x", "int")
        solver.add_variable("y", "int")
        solver.add_constraint("x + y == 10")
        solver.add_constraint("x - y == 4")

        result, model = solver.check()
        assert result == "sat"
        assert "x = 7" in model
        assert "y = 3" in model

    def test_unsat(self):
        """Test unsatisfiable constraints."""
        solver = Z3DirectSolver()
        solver.add_variable("x", "int")
        solver.add_constraint("x > 0")
        solver.add_constraint("x < 0")

        result, model = solver.check()
        assert result == "unsat"
        assert model is None

    def test_push_pop(self):
        """Test push/pop context management."""
        solver = Z3DirectSolver()
        solver.add_variable("x", "int")
        solver.add_constraint("x > 0")

        solver.push()
        solver.add_constraint("x < 0")
        result, _ = solver.check()
        assert result == "unsat"

        solver.pop()
        result, model = solver.check()
        assert result == "sat"

    def test_reset(self):
        """Test solver reset."""
        solver = Z3DirectSolver()
        solver.add_variable("x", "int")
        solver.add_constraint("x == 5")
        solver.reset()

        # After reset, variables should be cleared
        assert len(solver._variables) == 0
        assert len(solver._constraints) == 0


class TestSMTLibSolver:
    """Tests for SMTLibSolver class."""

    def test_basic_smtlib(self):
        """Test basic SMT-LIB solving."""
        solver = SMTLibSolver()
        smtlib_code = """
        (declare-const x Int)
        (declare-const y Int)
        (assert (= (+ x y) 10))
        (assert (= (- x y) 4))
        """
        result = solver.solve_smtlib(smtlib_code)
        assert "sat" in result

    def test_unsat_smtlib(self):
        """Test unsatisfiable SMT-LIB."""
        solver = SMTLibSolver()
        smtlib_code = """
        (declare-const x Int)
        (assert (> x 0))
        (assert (< x 0))
        """
        result = solver.solve_smtlib(smtlib_code)
        assert result == "unsat"


class TestLogicProgramSolver:
    """Tests for LogicProgramSolver class."""

    def test_parse_simple_program(self):
        """Test parsing a simple logic program."""
        solver = LogicProgramSolver()
        program = """
# Declarations
x = Int('x')
y = Int('y')

# Constraints
x + y == 10
x > 0
y > 0
"""
        solver.parse_logic_program(program)
        assert solver.flag is True
        assert len(solver.constraints) > 0


class TestSolveZ3Python:
    """Tests for solve_z3_python function."""

    def test_basic_execution(self):
        """Test basic Z3 Python execution."""
        code = """
x = Int('x')
y = Int('y')
solver = Solver()
solver.add(x + y == 10)
solver.add(x == 7)
if solver.check() == sat:
    print(solver.model())
"""
        result = solve_z3_python(code)
        assert "y = 3" in result
        assert "x = 7" in result

    def test_unsat_execution(self):
        """Test unsat result."""
        code = """
x = Int('x')
solver = Solver()
solver.add(x > 5)
solver.add(x < 3)
print(solver.check())
"""
        result = solve_z3_python(code)
        assert "unsat" in result

    def test_error_handling(self):
        """Test error handling for invalid code."""
        code = "invalid python code !!!"
        result = solve_z3_python(code)
        assert "error" in result.lower()


class TestVariableTypes:
    """Tests for different variable types."""

    def test_real_variables(self):
        """Test real number variables."""
        solver = Z3DirectSolver()
        solver.add_variable("x", "real")
        solver.add_constraint("x * x == 2")

        result, model = solver.check()
        assert result == "sat"

    def test_bool_variables(self):
        """Test boolean variables."""
        solver = Z3DirectSolver()
        solver.add_variable("p", "bool")
        solver.add_variable("q", "bool")
        solver.add_constraint("And(p, q)")

        result, model = solver.check()
        assert result == "sat"

    def test_bitvec_variables(self):
        """Test bit-vector variables."""
        solver = Z3DirectSolver()
        solver.add_variable("x", "bitvec", bits=8)
        solver.add_constraint("x * 3 == 21")

        result, model = solver.check()
        assert result == "sat"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
