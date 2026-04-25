"""Stack-based virtual machine with instruction set.

Defines the VM instruction set (bytecode opcodes) and the VMInstruction
dataclass. The VM uses a stack for operands and a separate store for
named variables.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any


class VMOp(Enum):
    """Stack-based VM instruction opcodes."""

    PUSH = auto()       # Push immediate value onto stack
    LOAD = auto()       # Push variable value onto stack
    STORE = auto()      # Pop stack top into variable
    POP = auto()        # Discard stack top

    # Arithmetic (pop 2, push result)
    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()
    NEG = auto()        # Pop 1, push negated

    # Comparison (pop 2, push 1 or 0)
    CMP_LT = auto()
    CMP_LE = auto()
    CMP_GT = auto()
    CMP_GE = auto()
    CMP_EQ = auto()
    CMP_NE = auto()

    # Control flow
    JMP = auto()        # Unconditional jump to address
    JZ = auto()         # Jump if top of stack is zero
    JNZ = auto()        # Jump if top of stack is non-zero
    LABEL = auto()      # Label marker (resolved before execution)

    # Functions
    CALL = auto()       # Call function (push frame)
    RET = auto()        # Return from function (pop frame)
    STORE_ARG = auto()  # Store argument in current frame

    # I/O
    PRINT = auto()      # Pop and print top of stack

    HALT = auto()       # Stop execution


@dataclass
class VMInstruction:
    """A single VM bytecode instruction.

    Attributes:
        op: The VM opcode.
        operand: Optional operand (value, variable name, or jump target).
    """

    op: VMOp
    operand: Any = None

    def __str__(self) -> str:
        if self.operand is not None:
            return f"{self.op.name:<10} {self.operand}"
        return self.op.name


if __name__ == "__main__":
    # Demo: show bytecode for "let x = 2 + 3 * 4"
    program = [
        VMInstruction(VMOp.PUSH, 3),
        VMInstruction(VMOp.PUSH, 4),
        VMInstruction(VMOp.MUL),
        VMInstruction(VMOp.PUSH, 2),
        VMInstruction(VMOp.ADD),
        VMInstruction(VMOp.STORE, "x"),
        VMInstruction(VMOp.HALT),
    ]
    print("=== VM Bytecode: let x = 2 + 3 * 4 ===")
    for i, instr in enumerate(program):
        print(f"  {i:>3}: {instr}")
