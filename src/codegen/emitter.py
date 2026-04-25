"""TAC-to-bytecode code emitter.

Translates three-address code instructions into stack-based VM
bytecode. Resolves labels to instruction addresses in a two-pass
approach: first emit with symbolic labels, then resolve to addresses.
"""

from __future__ import annotations

import argparse

from src.codegen.stack_vm import VMInstruction, VMOp
from src.ir.ir_generator import generate_ir
from src.ir.optimizer import optimize
from src.ir.three_address import Instruction, OpCode


# Map TAC opcodes to VM arithmetic/comparison opcodes
_TAC_TO_VM_ARITH: dict[OpCode, VMOp] = {
    OpCode.ADD: VMOp.ADD,
    OpCode.SUB: VMOp.SUB,
    OpCode.MUL: VMOp.MUL,
    OpCode.DIV: VMOp.DIV,
}

_TAC_TO_VM_CMP: dict[OpCode, VMOp] = {
    OpCode.LT: VMOp.CMP_LT,
    OpCode.LE: VMOp.CMP_LE,
    OpCode.GT: VMOp.CMP_GT,
    OpCode.GE: VMOp.CMP_GE,
    OpCode.EQ: VMOp.CMP_EQ,
    OpCode.NE: VMOp.CMP_NE,
}


class Emitter:
    """Translates TAC instructions into VM bytecode.

    Uses a two-pass approach:
    1. Emit bytecode with symbolic label references.
    2. Resolve labels to concrete instruction addresses.
    """

    def __init__(self) -> None:
        self.bytecode: list[VMInstruction] = []
        self._label_addresses: dict[str, int] = {}
        self._func_addresses: dict[str, int] = {}

    def emit(self, instructions: list[Instruction]) -> list[VMInstruction]:
        """Translate TAC to VM bytecode.

        Args:
            instructions: The three-address code instructions.

        Returns:
            List of VM bytecode instructions.
        """
        # Pass 1: emit bytecode, record label positions
        for instr in instructions:
            self._emit_instruction(instr)
        self.bytecode.append(VMInstruction(VMOp.HALT))

        # Pass 2: resolve label references
        self._resolve_labels()
        return self.bytecode

    def _emit_instruction(self, instr: Instruction) -> None:
        """Emit VM instructions for a single TAC instruction."""
        if instr.op == OpCode.LOAD_CONST:
            self.bytecode.append(VMInstruction(VMOp.PUSH, instr.src1))
            self.bytecode.append(VMInstruction(VMOp.STORE, instr.dest))

        elif instr.op == OpCode.ASSIGN:
            self.bytecode.append(VMInstruction(VMOp.LOAD, instr.src1))
            self.bytecode.append(VMInstruction(VMOp.STORE, instr.dest))

        elif instr.op in _TAC_TO_VM_ARITH:
            self.bytecode.append(VMInstruction(VMOp.LOAD, instr.src1))
            self.bytecode.append(VMInstruction(VMOp.LOAD, instr.src2))
            self.bytecode.append(VMInstruction(_TAC_TO_VM_ARITH[instr.op]))
            self.bytecode.append(VMInstruction(VMOp.STORE, instr.dest))

        elif instr.op in _TAC_TO_VM_CMP:
            self.bytecode.append(VMInstruction(VMOp.LOAD, instr.src1))
            self.bytecode.append(VMInstruction(VMOp.LOAD, instr.src2))
            self.bytecode.append(VMInstruction(_TAC_TO_VM_CMP[instr.op]))
            self.bytecode.append(VMInstruction(VMOp.STORE, instr.dest))

        elif instr.op == OpCode.NEG:
            self.bytecode.append(VMInstruction(VMOp.LOAD, instr.src1))
            self.bytecode.append(VMInstruction(VMOp.NEG))
            self.bytecode.append(VMInstruction(VMOp.STORE, instr.dest))

        elif instr.op == OpCode.LABEL:
            self._label_addresses[instr.dest or ""] = len(self.bytecode)
            self.bytecode.append(VMInstruction(VMOp.LABEL, instr.dest))

        elif instr.op == OpCode.JUMP:
            self.bytecode.append(VMInstruction(VMOp.JMP, instr.dest))

        elif instr.op == OpCode.JUMP_IF_ZERO:
            self.bytecode.append(VMInstruction(VMOp.LOAD, instr.src1))
            self.bytecode.append(VMInstruction(VMOp.JZ, instr.dest))

        elif instr.op == OpCode.JUMP_IF_NONZERO:
            self.bytecode.append(VMInstruction(VMOp.LOAD, instr.src1))
            self.bytecode.append(VMInstruction(VMOp.JNZ, instr.dest))

        elif instr.op == OpCode.PARAM:
            self.bytecode.append(VMInstruction(VMOp.LOAD, instr.src1))

        elif instr.op == OpCode.CALL:
            self.bytecode.append(VMInstruction(VMOp.CALL, instr.src1))
            self.bytecode.append(VMInstruction(VMOp.STORE, instr.dest))

        elif instr.op == OpCode.RETURN:
            if instr.src1:
                self.bytecode.append(VMInstruction(VMOp.LOAD, instr.src1))
            self.bytecode.append(VMInstruction(VMOp.RET))

        elif instr.op == OpCode.FUNC_BEGIN:
            self._func_addresses[instr.dest or ""] = len(self.bytecode)
            self.bytecode.append(VMInstruction(VMOp.LABEL, f"func_{instr.dest}"))

        elif instr.op == OpCode.FUNC_END:
            # Implicit return at end of function
            self.bytecode.append(VMInstruction(VMOp.RET))

        elif instr.op == OpCode.PRINT:
            self.bytecode.append(VMInstruction(VMOp.LOAD, instr.src1))
            self.bytecode.append(VMInstruction(VMOp.PRINT))

    def _resolve_labels(self) -> None:
        """Replace symbolic label references with instruction addresses."""
        for i, instr in enumerate(self.bytecode):
            if instr.op in (VMOp.JMP, VMOp.JZ, VMOp.JNZ):
                label = instr.operand
                if label in self._label_addresses:
                    self.bytecode[i] = VMInstruction(instr.op, self._label_addresses[label])
            elif instr.op == VMOp.CALL:
                func_name = instr.operand
                func_label = f"func_{func_name}"
                # Look up in label addresses (func labels are stored with func_ prefix)
                for lbl, addr in self._label_addresses.items():
                    if lbl == func_label:
                        self.bytecode[i] = VMInstruction(VMOp.CALL, addr)
                        break
                else:
                    if func_name in self._func_addresses:
                        self.bytecode[i] = VMInstruction(VMOp.CALL, self._func_addresses[func_name])


def compile_to_bytecode(source: str, optimize_ir: bool = True) -> list[VMInstruction]:
    """Compile source code to VM bytecode.

    Args:
        source: The raw source code.
        optimize_ir: Whether to run IR optimizations.

    Returns:
        List of VM bytecode instructions.
    """
    ir = generate_ir(source)
    if optimize_ir:
        ir = optimize(ir)
    emitter = Emitter()
    return emitter.emit(ir)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Compile DSL to VM bytecode")
    ap.add_argument("--input", required=True, help="Source code string")
    ap.add_argument("--no-optimize", action="store_true", help="Skip IR optimization")
    args = ap.parse_args()

    bytecode = compile_to_bytecode(args.input, optimize_ir=not args.no_optimize)
    print(f"=== VM Bytecode ({len(bytecode)} instructions) ===")
    for i, instr in enumerate(bytecode):
        print(f"  {i:>3}: {instr}")
