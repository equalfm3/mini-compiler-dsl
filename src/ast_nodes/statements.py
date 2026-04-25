"""Statement AST nodes (Let, If, While, FunctionDef, Return, Print, ExprStmt).

Each statement node stores its child expressions/statements and source
position for error reporting.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from src.ast_nodes.expressions import Expression

if TYPE_CHECKING:
    from src.ast_nodes.visitor import ASTVisitor


@dataclass
class Statement:
    """Base class for all statement AST nodes."""

    line: int = 0
    column: int = 0

    def accept(self, visitor: ASTVisitor) -> Any:
        """Dispatch to the appropriate visitor method."""
        raise NotImplementedError


@dataclass
class LetStmt(Statement):
    """Variable binding: let name = value.

    Attributes:
        name: The variable name being bound.
        value: The expression being assigned.
    """

    name: str = ""
    value: Expression = field(default_factory=Expression)

    def accept(self, visitor: ASTVisitor) -> Any:
        return visitor.visit_let_stmt(self)


@dataclass
class IfStmt(Statement):
    """Conditional: if condition { then_body } else { else_body }.

    Attributes:
        condition: The boolean expression to test.
        then_body: Statements to execute when condition is truthy.
        else_body: Statements to execute when condition is falsy.
    """

    condition: Expression = field(default_factory=Expression)
    then_body: list[Statement] = field(default_factory=list)
    else_body: list[Statement] = field(default_factory=list)

    def accept(self, visitor: ASTVisitor) -> Any:
        return visitor.visit_if_stmt(self)


@dataclass
class WhileStmt(Statement):
    """Loop: while condition { body }.

    Attributes:
        condition: The loop condition expression.
        body: Statements to execute each iteration.
    """

    condition: Expression = field(default_factory=Expression)
    body: list[Statement] = field(default_factory=list)

    def accept(self, visitor: ASTVisitor) -> Any:
        return visitor.visit_while_stmt(self)


@dataclass
class FunctionDef(Statement):
    """Function definition: fn name(params) { body }.

    Attributes:
        name: The function name.
        params: List of parameter names.
        body: The function body statements.
    """

    name: str = ""
    params: list[str] = field(default_factory=list)
    body: list[Statement] = field(default_factory=list)

    def accept(self, visitor: ASTVisitor) -> Any:
        return visitor.visit_function_def(self)


@dataclass
class ReturnStmt(Statement):
    """Return statement: return expr.

    Attributes:
        value: The expression to return (None for bare return).
    """

    value: Expression | None = None

    def accept(self, visitor: ASTVisitor) -> Any:
        return visitor.visit_return_stmt(self)


@dataclass
class PrintStmt(Statement):
    """Print statement: print(expr).

    Attributes:
        value: The expression to print.
    """

    value: Expression = field(default_factory=Expression)

    def accept(self, visitor: ASTVisitor) -> Any:
        return visitor.visit_print_stmt(self)


@dataclass
class ExprStmt(Statement):
    """Expression used as a statement (e.g., a function call).

    Attributes:
        expression: The expression.
    """

    expression: Expression = field(default_factory=Expression)

    def accept(self, visitor: ASTVisitor) -> Any:
        return visitor.visit_expr_stmt(self)


if __name__ == "__main__":
    from src.ast_nodes.expressions import BinaryOp, Identifier, Literal

    # Demo: build a let statement AST
    stmt = LetStmt(
        name="x",
        value=BinaryOp(operator="+", left=Literal(value=2), right=Literal(value=3)),
    )
    print("=== Let Statement AST ===")
    print(f"  {stmt}")
    print(f"  Represents: let x = 2 + 3")
