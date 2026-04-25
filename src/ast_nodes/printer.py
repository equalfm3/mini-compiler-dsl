"""AST pretty-printer for debugging.

Renders an AST as an indented tree, showing node types and values
in a human-readable format.
"""

from __future__ import annotations

from src.ast_nodes.expressions import (
    BinaryOp,
    Expression,
    FunctionCall,
    Identifier,
    Literal,
    UnaryOp,
)
from src.ast_nodes.statements import (
    ExprStmt,
    FunctionDef,
    IfStmt,
    LetStmt,
    PrintStmt,
    ReturnStmt,
    Statement,
    WhileStmt,
)
from src.ast_nodes.visitor import ASTVisitor


class ASTPrinter(ASTVisitor):
    """Renders an AST as an indented tree string.

    Usage:
        printer = ASTPrinter()
        output = printer.print(node)
    """

    def __init__(self) -> None:
        self._indent: int = 0
        self._lines: list[str] = []

    def print(self, node: Expression | Statement) -> str:
        """Render the AST rooted at node as a string.

        Args:
            node: The root AST node to print.

        Returns:
            A multi-line indented string representation.
        """
        self._indent = 0
        self._lines = []
        node.accept(self)
        return "\n".join(self._lines)

    def print_program(self, statements: list[Statement]) -> str:
        """Render a list of statements as a program.

        Args:
            statements: The top-level statements.

        Returns:
            A multi-line indented string representation.
        """
        self._indent = 0
        self._lines = []
        self._emit("Program")
        self._indent += 1
        for stmt in statements:
            stmt.accept(self)
        self._indent -= 1
        return "\n".join(self._lines)

    def _emit(self, text: str) -> None:
        """Add an indented line to the output."""
        prefix = "  " * self._indent
        self._lines.append(f"{prefix}{text}")

    def visit_literal(self, node: Literal) -> None:
        self._emit(f"Literal({node.value})")

    def visit_identifier(self, node: Identifier) -> None:
        self._emit(f"Identifier({node.name})")

    def visit_binary_op(self, node: BinaryOp) -> None:
        self._emit(f"BinaryOp({node.operator})")
        self._indent += 1
        node.left.accept(self)
        node.right.accept(self)
        self._indent -= 1

    def visit_unary_op(self, node: UnaryOp) -> None:
        self._emit(f"UnaryOp({node.operator})")
        self._indent += 1
        node.operand.accept(self)
        self._indent -= 1

    def visit_function_call(self, node: FunctionCall) -> None:
        self._emit(f"FunctionCall({node.name})")
        self._indent += 1
        for arg in node.arguments:
            arg.accept(self)
        self._indent -= 1

    def visit_let_stmt(self, node: LetStmt) -> None:
        self._emit(f"LetStmt({node.name})")
        self._indent += 1
        node.value.accept(self)
        self._indent -= 1

    def visit_if_stmt(self, node: IfStmt) -> None:
        self._emit("IfStmt")
        self._indent += 1
        self._emit("Condition:")
        self._indent += 1
        node.condition.accept(self)
        self._indent -= 1
        self._emit("Then:")
        self._indent += 1
        for stmt in node.then_body:
            stmt.accept(self)
        self._indent -= 1
        if node.else_body:
            self._emit("Else:")
            self._indent += 1
            for stmt in node.else_body:
                stmt.accept(self)
            self._indent -= 1
        self._indent -= 1

    def visit_while_stmt(self, node: WhileStmt) -> None:
        self._emit("WhileStmt")
        self._indent += 1
        self._emit("Condition:")
        self._indent += 1
        node.condition.accept(self)
        self._indent -= 1
        self._emit("Body:")
        self._indent += 1
        for stmt in node.body:
            stmt.accept(self)
        self._indent -= 1
        self._indent -= 1

    def visit_function_def(self, node: FunctionDef) -> None:
        params = ", ".join(node.params)
        self._emit(f"FunctionDef({node.name}({params}))")
        self._indent += 1
        for stmt in node.body:
            stmt.accept(self)
        self._indent -= 1

    def visit_return_stmt(self, node: ReturnStmt) -> None:
        self._emit("ReturnStmt")
        if node.value:
            self._indent += 1
            node.value.accept(self)
            self._indent -= 1

    def visit_print_stmt(self, node: PrintStmt) -> None:
        self._emit("PrintStmt")
        self._indent += 1
        node.value.accept(self)
        self._indent -= 1

    def visit_expr_stmt(self, node: ExprStmt) -> None:
        self._emit("ExprStmt")
        self._indent += 1
        node.expression.accept(self)
        self._indent -= 1


if __name__ == "__main__":
    # Demo: pretty-print a hand-built AST
    tree = LetStmt(
        name="result",
        value=BinaryOp(
            operator="+",
            left=Literal(value=2),
            right=BinaryOp(operator="*", left=Literal(value=3), right=Literal(value=4)),
        ),
    )
    printer = ASTPrinter()
    print("=== AST Pretty Print ===")
    print(printer.print(tree))
