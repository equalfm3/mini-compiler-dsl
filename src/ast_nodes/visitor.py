"""Visitor pattern base class for AST traversal.

Provides a default visitor that raises NotImplementedError for each
node type, ensuring subclasses handle all cases they care about.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.ast_nodes.expressions import (
        BinaryOp,
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
        WhileStmt,
    )


class ASTVisitor:
    """Base visitor for AST traversal.

    Subclass and override the visit_* methods you need. Unhandled
    node types raise NotImplementedError.
    """

    def visit_literal(self, node: Literal) -> Any:
        """Visit a numeric literal."""
        raise NotImplementedError(f"visit_literal not implemented")

    def visit_identifier(self, node: Identifier) -> Any:
        """Visit a variable reference."""
        raise NotImplementedError(f"visit_identifier not implemented")

    def visit_binary_op(self, node: BinaryOp) -> Any:
        """Visit a binary operation."""
        raise NotImplementedError(f"visit_binary_op not implemented")

    def visit_unary_op(self, node: UnaryOp) -> Any:
        """Visit a unary operation."""
        raise NotImplementedError(f"visit_unary_op not implemented")

    def visit_function_call(self, node: FunctionCall) -> Any:
        """Visit a function call expression."""
        raise NotImplementedError(f"visit_function_call not implemented")

    def visit_let_stmt(self, node: LetStmt) -> Any:
        """Visit a let binding statement."""
        raise NotImplementedError(f"visit_let_stmt not implemented")

    def visit_if_stmt(self, node: IfStmt) -> Any:
        """Visit an if/else statement."""
        raise NotImplementedError(f"visit_if_stmt not implemented")

    def visit_while_stmt(self, node: WhileStmt) -> Any:
        """Visit a while loop statement."""
        raise NotImplementedError(f"visit_while_stmt not implemented")

    def visit_function_def(self, node: FunctionDef) -> Any:
        """Visit a function definition."""
        raise NotImplementedError(f"visit_function_def not implemented")

    def visit_return_stmt(self, node: ReturnStmt) -> Any:
        """Visit a return statement."""
        raise NotImplementedError(f"visit_return_stmt not implemented")

    def visit_print_stmt(self, node: PrintStmt) -> Any:
        """Visit a print statement."""
        raise NotImplementedError(f"visit_print_stmt not implemented")

    def visit_expr_stmt(self, node: ExprStmt) -> Any:
        """Visit an expression statement."""
        raise NotImplementedError(f"visit_expr_stmt not implemented")


if __name__ == "__main__":
    print("=== ASTVisitor Methods ===")
    for name in sorted(dir(ASTVisitor)):
        if name.startswith("visit_"):
            print(f"  {name}")
