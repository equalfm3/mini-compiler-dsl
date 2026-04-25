"""AST-to-TAC lowering pass.

Walks the AST using the visitor pattern and emits three-address code
instructions. Manages temporary variables and labels for control flow.
"""

from __future__ import annotations

import argparse

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
from src.ir.three_address import Instruction, OpCode, OPERATOR_TO_OPCODE
from src.parser.recursive_descent import parse


class IRGenerator(ASTVisitor):
    """Lowers an AST into three-address code.

    Generates unique temporaries (t1, t2, ...) for intermediate values
    and unique labels (L1, L2, ...) for control flow.
    """

    def __init__(self) -> None:
        self.instructions: list[Instruction] = []
        self._temp_counter: int = 0
        self._label_counter: int = 0

    def generate(self, statements: list[Statement]) -> list[Instruction]:
        """Generate TAC for a list of statements.

        Args:
            statements: The top-level AST statements.

        Returns:
            The list of three-address code instructions.
        """
        for stmt in statements:
            stmt.accept(self)
        return self.instructions

    def _new_temp(self) -> str:
        """Allocate a fresh temporary variable name."""
        self._temp_counter += 1
        return f"t{self._temp_counter}"

    def _new_label(self) -> str:
        """Allocate a fresh label name."""
        self._label_counter += 1
        return f"L{self._label_counter}"

    def _emit(self, op: OpCode, dest: str | None = None,
              src1: object = None, src2: object = None) -> None:
        """Append an instruction to the output."""
        self.instructions.append(Instruction(op, dest, src1, src2))

    # ── Expression visitors (return the temp holding the result) ──

    def visit_literal(self, node: Literal) -> str:
        temp = self._new_temp()
        self._emit(OpCode.LOAD_CONST, temp, node.value)
        return temp

    def visit_identifier(self, node: Identifier) -> str:
        return node.name

    def visit_binary_op(self, node: BinaryOp) -> str:
        left = node.left.accept(self)
        right = node.right.accept(self)
        dest = self._new_temp()
        opcode = OPERATOR_TO_OPCODE[node.operator]
        self._emit(opcode, dest, left, right)
        return dest

    def visit_unary_op(self, node: UnaryOp) -> str:
        operand = node.operand.accept(self)
        dest = self._new_temp()
        self._emit(OpCode.NEG, dest, operand)
        return dest

    def visit_function_call(self, node: FunctionCall) -> str:
        arg_temps: list[str] = []
        for arg in node.arguments:
            arg_temps.append(arg.accept(self))
        for at in arg_temps:
            self._emit(OpCode.PARAM, src1=at)
        dest = self._new_temp()
        self._emit(OpCode.CALL, dest, node.name, len(node.arguments))
        return dest

    # ── Statement visitors ─────────────────────────────────────

    def visit_let_stmt(self, node: LetStmt) -> None:
        src = node.value.accept(self)
        self._emit(OpCode.ASSIGN, node.name, src)

    def visit_if_stmt(self, node: IfStmt) -> None:
        cond = node.condition.accept(self)
        else_label = self._new_label()
        end_label = self._new_label()

        if node.else_body:
            self._emit(OpCode.JUMP_IF_ZERO, else_label, cond)
            for stmt in node.then_body:
                stmt.accept(self)
            self._emit(OpCode.JUMP, end_label)
            self._emit(OpCode.LABEL, else_label)
            for stmt in node.else_body:
                stmt.accept(self)
            self._emit(OpCode.LABEL, end_label)
        else:
            self._emit(OpCode.JUMP_IF_ZERO, end_label, cond)
            for stmt in node.then_body:
                stmt.accept(self)
            self._emit(OpCode.LABEL, end_label)

    def visit_while_stmt(self, node: WhileStmt) -> None:
        loop_label = self._new_label()
        end_label = self._new_label()

        self._emit(OpCode.LABEL, loop_label)
        cond = node.condition.accept(self)
        self._emit(OpCode.JUMP_IF_ZERO, end_label, cond)
        for stmt in node.body:
            stmt.accept(self)
        self._emit(OpCode.JUMP, loop_label)
        self._emit(OpCode.LABEL, end_label)

    def visit_function_def(self, node: FunctionDef) -> None:
        self._emit(OpCode.FUNC_BEGIN, node.name)
        # Assign parameters from the call stack
        for i, param in enumerate(node.params):
            self._emit(OpCode.ASSIGN, param, f"__param_{i}")
        for stmt in node.body:
            stmt.accept(self)
        self._emit(OpCode.FUNC_END, node.name)

    def visit_return_stmt(self, node: ReturnStmt) -> None:
        if node.value:
            src = node.value.accept(self)
            self._emit(OpCode.RETURN, src1=src)
        else:
            self._emit(OpCode.RETURN)

    def visit_print_stmt(self, node: PrintStmt) -> None:
        src = node.value.accept(self)
        self._emit(OpCode.PRINT, src1=src)

    def visit_expr_stmt(self, node: ExprStmt) -> None:
        node.expression.accept(self)


def generate_ir(source: str) -> list[Instruction]:
    """Convenience: parse source and generate TAC.

    Args:
        source: The raw source code.

    Returns:
        List of three-address code instructions.
    """
    statements = parse(source)
    gen = IRGenerator()
    return gen.generate(statements)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Generate three-address code IR")
    ap.add_argument("--input", required=True, help="Source code string")
    ap.add_argument("--print-ir", action="store_true", help="Print the IR")
    args = ap.parse_args()

    instructions = generate_ir(args.input)
    print(f"=== Three-Address Code ({len(instructions)} instructions) ===")
    for instr in instructions:
        print(instr)
