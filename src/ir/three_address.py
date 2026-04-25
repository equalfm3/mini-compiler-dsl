"""Three-address code instruction definitions.

Defines the TAC instruction types and the Instruction dataclass used
as the intermediate representation between AST and bytecode.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any


class OpCode(Enum):
    """Three-address code operation types."""

    # Arithmetic: dest = left op right
    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()
    NEG = auto()  # dest = -src

    # Comparison: dest = left op right (result is 1 or 0)
    LT = auto()
    LE = auto()
    GT = auto()
    GE = auto()
    EQ = auto()
    NE = auto()

    # Data movement
    ASSIGN = auto()     # dest = src
    LOAD_CONST = auto() # dest = immediate value

    # Control flow
    LABEL = auto()      # label:
    JUMP = auto()       # goto label
    JUMP_IF_ZERO = auto()   # if src == 0 goto label
    JUMP_IF_NONZERO = auto() # if src != 0 goto label

    # Functions
    PARAM = auto()      # push parameter
    CALL = auto()       # dest = call func, nargs
    RETURN = auto()     # return src
    FUNC_BEGIN = auto() # function entry label
    FUNC_END = auto()   # function exit

    # I/O
    PRINT = auto()      # print src


# Map source operators to TAC opcodes
OPERATOR_TO_OPCODE: dict[str, OpCode] = {
    "+": OpCode.ADD,
    "-": OpCode.SUB,
    "*": OpCode.MUL,
    "/": OpCode.DIV,
    "<": OpCode.LT,
    "<=": OpCode.LE,
    ">": OpCode.GT,
    ">=": OpCode.GE,
    "==": OpCode.EQ,
    "!=": OpCode.NE,
}


@dataclass
class Instruction:
    """A single three-address code instruction.

    Attributes:
        op: The operation type.
        dest: Destination variable/temp (or label for LABEL/JUMP).
        src1: First source operand (variable, temp, or immediate).
        src2: Second source operand (for binary ops).
    """

    op: OpCode
    dest: str | None = None
    src1: Any = None
    src2: Any = None

    def __str__(self) -> str:
        if self.op == OpCode.LABEL:
            return f"{self.dest}:"
        if self.op == OpCode.JUMP:
            return f"  goto {self.dest}"
        if self.op == OpCode.JUMP_IF_ZERO:
            return f"  if {self.src1} == 0 goto {self.dest}"
        if self.op == OpCode.JUMP_IF_NONZERO:
            return f"  if {self.src1} != 0 goto {self.dest}"
        if self.op == OpCode.LOAD_CONST:
            return f"  {self.dest} = {self.src1}"
        if self.op == OpCode.ASSIGN:
            return f"  {self.dest} = {self.src1}"
        if self.op == OpCode.NEG:
            return f"  {self.dest} = -{self.src1}"
        if self.op == OpCode.PARAM:
            return f"  param {self.src1}"
        if self.op == OpCode.CALL:
            return f"  {self.dest} = call {self.src1}, {self.src2}"
        if self.op == OpCode.RETURN:
            return f"  return {self.src1 or ''}"
        if self.op == OpCode.FUNC_BEGIN:
            return f"func {self.dest}:"
        if self.op == OpCode.FUNC_END:
            return f"end func {self.dest}"
        if self.op == OpCode.PRINT:
            return f"  print {self.src1}"

        op_sym = {
            OpCode.ADD: "+", OpCode.SUB: "-",
            OpCode.MUL: "*", OpCode.DIV: "/",
            OpCode.LT: "<", OpCode.LE: "<=",
            OpCode.GT: ">", OpCode.GE: ">=",
            OpCode.EQ: "==", OpCode.NE: "!=",
        }.get(self.op, self.op.name)
        return f"  {self.dest} = {self.src1} {op_sym} {self.src2}"


if __name__ == "__main__":
    # Demo: show TAC for "let x = 2 + 3 * 4"
    instructions = [
        Instruction(OpCode.LOAD_CONST, "t1", 3),
        Instruction(OpCode.LOAD_CONST, "t2", 4),
        Instruction(OpCode.MUL, "t3", "t1", "t2"),
        Instruction(OpCode.LOAD_CONST, "t4", 2),
        Instruction(OpCode.ADD, "t5", "t4", "t3"),
        Instruction(OpCode.ASSIGN, "x", "t5"),
    ]
    print("=== Three-Address Code: let x = 2 + 3 * 4 ===")
    for instr in instructions:
        print(instr)
