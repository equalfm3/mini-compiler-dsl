"""Expression AST nodes (BinaryOp, UnaryOp, Literal, Identifier, FunctionCall).

Each node stores source position for error reporting and accepts
visitors for traversal.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.ast_nodes.visitor import ASTVisitor


@dataclass
class Expression:
    """Base class for all expression AST nodes."""

    line: int = 0
    column: int = 0

    def accept(self, visitor: ASTVisitor) -> Any:
        """Dispatch to the appropriate visitor method."""
        raise NotImplementedError


@dataclass
class Literal(Expression):
    """A numeric literal.

    Attributes:
        value: The numeric value (int or float).
    """

    value: int | float = 0

    def accept(self, visitor: ASTVisitor) -> Any:
        return visitor.visit_literal(self)


@dataclass
class Identifier(Expression):
    """A variable reference.

    Attributes:
        name: The variable name.
    """

    name: str = ""

    def accept(self, visitor: ASTVisitor) -> Any:
        return visitor.visit_identifier(self)


@dataclass
class BinaryOp(Expression):
    """A binary operation (e.g., a + b, x * y, a < b).

    Attributes:
        operator: The operator string (+, -, *, /, <, <=, >, >=, ==, !=).
        left: The left operand expression.
        right: The right operand expression.
    """

    operator: str = ""
    left: Expression = field(default_factory=Expression)
    right: Expression = field(default_factory=Expression)

    def accept(self, visitor: ASTVisitor) -> Any:
        return visitor.visit_binary_op(self)


@dataclass
class UnaryOp(Expression):
    """A unary operation (e.g., -x).

    Attributes:
        operator: The operator string (currently only '-').
        operand: The operand expression.
    """

    operator: str = ""
    operand: Expression = field(default_factory=Expression)

    def accept(self, visitor: ASTVisitor) -> Any:
        return visitor.visit_unary_op(self)


@dataclass
class FunctionCall(Expression):
    """A function call expression (e.g., add(1, 2)).

    Attributes:
        name: The function name.
        arguments: List of argument expressions.
    """

    name: str = ""
    arguments: list[Expression] = field(default_factory=list)

    def accept(self, visitor: ASTVisitor) -> Any:
        return visitor.visit_function_call(self)


if __name__ == "__main__":
    # Demo: build a small AST by hand
    tree = BinaryOp(
        operator="+",
        left=Literal(value=2),
        right=BinaryOp(
            operator="*",
            left=Literal(value=3),
            right=Literal(value=4),
        ),
    )
    print("=== Manual AST ===")
    print(f"  {tree}")
    print(f"\n  Represents: 2 + 3 * 4")
