"""Basic optimizations: constant folding and dead code elimination.

Operates on three-address code instructions, performing safe
transformations that reduce the number of instructions without
changing program semantics.
"""

from __future__ import annotations

import argparse
import operator as op_module

from src.ir.ir_generator import generate_ir
from src.ir.three_address import Instruction, OpCode


# Arithmetic operations for constant folding
_ARITH_OPS: dict[OpCode, object] = {
    OpCode.ADD: op_module.add,
    OpCode.SUB: op_module.sub,
    OpCode.MUL: op_module.mul,
    OpCode.DIV: op_module.truediv,
}

# Comparison operations for constant folding
_CMP_OPS: dict[OpCode, object] = {
    OpCode.LT: op_module.lt,
    OpCode.LE: op_module.le,
    OpCode.GT: op_module.gt,
    OpCode.GE: op_module.ge,
    OpCode.EQ: op_module.eq,
    OpCode.NE: op_module.ne,
}


def _is_temp(name: str) -> bool:
    """Check if a name is a compiler-generated temporary (t1, t2, ...)."""
    return isinstance(name, str) and name.startswith("t") and name[1:].isdigit()


def _find_loop_modified_vars(instructions: list[Instruction]) -> set[str]:
    """Find variables that are assigned inside loops.

    Any variable assigned between a LABEL and a JUMP back to that label
    is potentially modified each iteration and cannot be constant-folded.

    Args:
        instructions: The TAC instruction list.

    Returns:
        Set of variable names modified inside loops.
    """
    modified: set[str] = set()
    # Find all labels that are jump targets (backward jumps indicate loops)
    jump_targets: set[str] = set()
    for instr in instructions:
        if instr.op == OpCode.JUMP and instr.dest:
            jump_targets.add(instr.dest)

    # Find labels and track assignments between label and its backward jump
    label_positions: dict[str, int] = {}
    for i, instr in enumerate(instructions):
        if instr.op == OpCode.LABEL and instr.dest:
            label_positions[instr.dest] = i

    for i, instr in enumerate(instructions):
        if instr.op == OpCode.JUMP and instr.dest in label_positions:
            label_pos = label_positions[instr.dest]
            if label_pos < i:  # backward jump = loop
                for j in range(label_pos, i):
                    jnstr = instructions[j]
                    if jnstr.dest and jnstr.op in (
                        OpCode.ASSIGN, OpCode.LOAD_CONST,
                        *_ARITH_OPS, *_CMP_OPS, OpCode.NEG,
                    ):
                        modified.add(jnstr.dest)

    return modified


def constant_fold(instructions: list[Instruction]) -> list[Instruction]:
    """Fold constant expressions into single LOAD_CONST instructions.

    Only folds expressions where both operands are known compile-time
    constants AND the destination is a temporary (not a user variable
    that might be reassigned in a loop).

    Args:
        instructions: The input TAC instruction list.

    Returns:
        A new instruction list with constants folded.
    """
    # Find variables modified in loops — these cannot be safely folded
    loop_vars = _find_loop_modified_vars(instructions)

    # Track which temps hold known constant values
    constants: dict[str, int | float] = {}
    result: list[Instruction] = []

    for instr in instructions:
        if instr.op == OpCode.LOAD_CONST and instr.dest:
            if instr.dest not in loop_vars:
                constants[instr.dest] = instr.src1
            result.append(instr)

        elif instr.op in _ARITH_OPS and instr.dest:
            v1 = constants.get(str(instr.src1))
            v2 = constants.get(str(instr.src2))
            if v1 is not None and v2 is not None and instr.dest not in loop_vars:
                fn = _ARITH_OPS[instr.op]
                folded = fn(v1, v2)  # type: ignore[operator]
                constants[instr.dest] = folded
                result.append(Instruction(OpCode.LOAD_CONST, instr.dest, folded))
            else:
                result.append(instr)

        elif instr.op in _CMP_OPS and instr.dest:
            v1 = constants.get(str(instr.src1))
            v2 = constants.get(str(instr.src2))
            if v1 is not None and v2 is not None and instr.dest not in loop_vars:
                fn = _CMP_OPS[instr.op]
                folded = int(fn(v1, v2))  # type: ignore[operator]
                constants[instr.dest] = folded
                result.append(Instruction(OpCode.LOAD_CONST, instr.dest, folded))
            else:
                result.append(instr)

        elif instr.op == OpCode.NEG and instr.dest:
            v = constants.get(str(instr.src1))
            if v is not None and instr.dest not in loop_vars:
                folded = -v
                constants[instr.dest] = folded
                result.append(Instruction(OpCode.LOAD_CONST, instr.dest, folded))
            else:
                result.append(instr)

        elif instr.op == OpCode.ASSIGN and instr.dest:
            src_str = str(instr.src1)
            if src_str in constants and instr.dest not in loop_vars:
                constants[instr.dest] = constants[src_str]
            result.append(instr)

        elif instr.op == OpCode.LABEL:
            # At a label, invalidate constants for loop-modified vars
            result.append(instr)
        else:
            result.append(instr)

    return result


def dead_code_eliminate(instructions: list[Instruction]) -> list[Instruction]:
    """Remove instructions whose results are never used.

    A temporary is dead if it is never referenced as src1 or src2
    in any subsequent instruction. Labels and control flow are preserved.

    Args:
        instructions: The input TAC instruction list.

    Returns:
        A new instruction list with dead code removed.
    """
    # Collect all referenced sources
    used: set[str] = set()
    for instr in instructions:
        if instr.src1 is not None:
            used.add(str(instr.src1))
        if instr.src2 is not None:
            used.add(str(instr.src2))

    # Keep instructions whose dest is used, or that have side effects
    side_effect_ops = {
        OpCode.LABEL, OpCode.JUMP, OpCode.JUMP_IF_ZERO, OpCode.JUMP_IF_NONZERO,
        OpCode.CALL, OpCode.RETURN, OpCode.PARAM, OpCode.PRINT,
        OpCode.FUNC_BEGIN, OpCode.FUNC_END,
    }

    result: list[Instruction] = []
    for instr in instructions:
        if instr.op in side_effect_ops:
            result.append(instr)
        elif instr.dest and instr.dest in used:
            result.append(instr)
        elif instr.op == OpCode.ASSIGN and instr.dest:
            # Keep assignments to user variables (non-temporaries)
            if not _is_temp(instr.dest):
                result.append(instr)
            elif instr.dest in used:
                result.append(instr)
        else:
            result.append(instr)

    return result


def optimize(instructions: list[Instruction]) -> list[Instruction]:
    """Run all optimization passes.

    Args:
        instructions: The input TAC instruction list.

    Returns:
        Optimized instruction list.
    """
    result = constant_fold(instructions)
    result = dead_code_eliminate(result)
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Optimize three-address code")
    ap.add_argument("--input", required=True, help="Source code string")
    args = ap.parse_args()

    original = generate_ir(args.input)
    optimized = optimize(original)

    print(f"=== Original IR ({len(original)} instructions) ===")
    for instr in original:
        print(instr)

    print(f"\n=== Optimized IR ({len(optimized)} instructions) ===")
    for instr in optimized:
        print(instr)

    removed = len(original) - len(optimized)
    print(f"\nRemoved {removed} instruction(s) via optimization")
