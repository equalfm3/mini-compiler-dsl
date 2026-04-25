"""VM execution engine with trace output.

Executes stack-based VM bytecode, maintaining a value stack, variable
store, and call stack. Supports optional trace mode that prints each
instruction as it executes.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from typing import Any

from src.ast_nodes.printer import ASTPrinter
from src.codegen.emitter import compile_to_bytecode
from src.codegen.stack_vm import VMInstruction, VMOp
from src.ir.ir_generator import generate_ir
from src.ir.optimizer import optimize
from src.lexer.tokenizer import tokenize
from src.parser.recursive_descent import parse


@dataclass
class CallFrame:
    """A single call frame on the VM call stack.

    Attributes:
        return_address: Instruction pointer to return to.
        locals: Local variable store for this frame.
    """

    return_address: int = 0
    locals: dict[str, Any] = field(default_factory=dict)


class VMRunner:
    """Executes VM bytecode on a stack machine.

    Maintains:
    - A value stack for operands and intermediate results.
    - A global variable store.
    - A call stack with frames for function calls.

    Attributes:
        bytecode: The program to execute.
        trace: Whether to print each instruction during execution.
    """

    def __init__(self, bytecode: list[VMInstruction], trace: bool = False) -> None:
        """Initialize the VM with bytecode.

        Args:
            bytecode: The compiled VM instructions.
            trace: Enable instruction-level tracing.
        """
        self.bytecode = bytecode
        self.trace = trace
        self.stack: list[Any] = []
        self.globals: dict[str, Any] = {}
        self.call_stack: list[CallFrame] = [CallFrame()]
        self.ip: int = 0
        self.output: list[str] = []

    @property
    def _locals(self) -> dict[str, Any]:
        """Current frame's local variables."""
        return self.call_stack[-1].locals

    def run(self) -> dict[str, Any]:
        """Execute the bytecode program.

        Returns:
            The final variable store (globals merged with top-frame locals).
        """
        max_steps = 100_000
        steps = 0

        while self.ip < len(self.bytecode) and steps < max_steps:
            instr = self.bytecode[self.ip]
            steps += 1

            if self.trace:
                stack_preview = self.stack[-5:] if self.stack else []
                print(f"  [{self.ip:>3}] {str(instr):<20}  stack={stack_preview}")

            if instr.op == VMOp.HALT:
                break

            self._execute(instr)

        # Merge locals into globals for final state
        result = dict(self.globals)
        result.update(self._locals)
        return result

    def _execute(self, instr: VMInstruction) -> None:
        """Execute a single VM instruction."""
        op = instr.op

        if op == VMOp.PUSH:
            self.stack.append(instr.operand)
            self.ip += 1

        elif op == VMOp.LOAD:
            name = instr.operand
            if name in self._locals:
                self.stack.append(self._locals[name])
            elif name in self.globals:
                self.stack.append(self.globals[name])
            else:
                raise RuntimeError(f"Undefined variable: {name}")
            self.ip += 1

        elif op == VMOp.STORE:
            value = self.stack.pop()
            self._locals[instr.operand] = value
            self.globals[instr.operand] = value
            self.ip += 1

        elif op == VMOp.POP:
            self.stack.pop()
            self.ip += 1

        elif op == VMOp.ADD:
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.append(a + b)
            self.ip += 1

        elif op == VMOp.SUB:
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.append(a - b)
            self.ip += 1

        elif op == VMOp.MUL:
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.append(a * b)
            self.ip += 1

        elif op == VMOp.DIV:
            b, a = self.stack.pop(), self.stack.pop()
            if b == 0:
                raise RuntimeError("Division by zero")
            self.stack.append(a / b if isinstance(a, float) or isinstance(b, float) else a // b)
            self.ip += 1

        elif op == VMOp.NEG:
            self.stack.append(-self.stack.pop())
            self.ip += 1

        elif op == VMOp.CMP_LT:
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.append(1 if a < b else 0)
            self.ip += 1

        elif op == VMOp.CMP_LE:
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.append(1 if a <= b else 0)
            self.ip += 1

        elif op == VMOp.CMP_GT:
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.append(1 if a > b else 0)
            self.ip += 1

        elif op == VMOp.CMP_GE:
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.append(1 if a >= b else 0)
            self.ip += 1

        elif op == VMOp.CMP_EQ:
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.append(1 if a == b else 0)
            self.ip += 1

        elif op == VMOp.CMP_NE:
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.append(1 if a != b else 0)
            self.ip += 1

        elif op == VMOp.JMP:
            self.ip = instr.operand

        elif op == VMOp.JZ:
            val = self.stack.pop()
            self.ip = instr.operand if val == 0 else self.ip + 1

        elif op == VMOp.JNZ:
            val = self.stack.pop()
            self.ip = instr.operand if val != 0 else self.ip + 1

        elif op == VMOp.CALL:
            frame = CallFrame(return_address=self.ip + 1)
            self.call_stack.append(frame)
            self.ip = instr.operand

        elif op == VMOp.RET:
            frame = self.call_stack.pop()
            self.ip = frame.return_address

        elif op == VMOp.LABEL:
            self.ip += 1

        elif op == VMOp.PRINT:
            val = self.stack.pop()
            self.output.append(str(val))
            print(val)
            self.ip += 1

        elif op == VMOp.STORE_ARG:
            val = self.stack.pop()
            self._locals[instr.operand] = val
            self.ip += 1

        else:
            raise RuntimeError(f"Unknown opcode: {op}")


def run_program(source: str, trace: bool = False,
                verbose: bool = False) -> dict[str, Any]:
    """Compile and execute a DSL program.

    Args:
        source: The raw source code.
        trace: Enable VM instruction tracing.
        verbose: Print all intermediate representations.

    Returns:
        The final variable store.
    """
    if verbose:
        # Show tokens
        tokens = tokenize(source)
        print("=== Tokens ===")
        for tok in tokens:
            print(f"  {tok}")

        # Show AST
        statements = parse(source)
        printer = ASTPrinter()
        print(f"\n=== AST ===")
        print(printer.print_program(statements))

        # Show IR
        ir = generate_ir(source)
        print(f"\n=== Three-Address Code (before optimization) ===")
        for instr in ir:
            print(instr)

        ir_opt = optimize(ir)
        print(f"\n=== Three-Address Code (after optimization) ===")
        for instr in ir_opt:
            print(instr)

    bytecode = compile_to_bytecode(source)

    if verbose:
        print(f"\n=== VM Bytecode ({len(bytecode)} instructions) ===")
        for i, instr in enumerate(bytecode):
            print(f"  {i:>3}: {instr}")
        print()

    if trace or verbose:
        print("=== Execution Trace ===")

    vm = VMRunner(bytecode, trace=trace or verbose)
    result = vm.run()

    if verbose or trace:
        print(f"\n=== Final Variables ===")
        # Filter out temporaries for cleaner output
        user_vars = {k: v for k, v in result.items()
                     if not k.startswith("t") or not k[1:].isdigit()}
        for name, val in sorted(user_vars.items()):
            print(f"  {name} = {val}")

    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Compile and run DSL programs")
    ap.add_argument("--input", required=True, help="Source code string")
    ap.add_argument("--trace", action="store_true", help="Trace VM execution")
    ap.add_argument("--verbose", action="store_true", help="Show all phases")
    ap.add_argument("--all-phases", action="store_true", help="Alias for --verbose")
    args = ap.parse_args()

    verbose = args.verbose or args.all_phases
    result = run_program(args.input, trace=args.trace, verbose=verbose)

    if not args.trace and not verbose:
        user_vars = {k: v for k, v in result.items()
                     if not k.startswith("t") or not k[1:].isdigit()}
        print("=== Result ===")
        for name, val in sorted(user_vars.items()):
            print(f"  {name} = {val}")
