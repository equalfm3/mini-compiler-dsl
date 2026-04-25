"""Recursive descent parser for the DSL grammar.

Consumes a token stream and produces an AST. Each grammar rule maps
to a method that returns the corresponding AST node.
"""

from __future__ import annotations

import argparse

from src.ast_nodes.expressions import (
    BinaryOp, Expression, FunctionCall, Identifier, Literal, UnaryOp,
)
from src.ast_nodes.printer import ASTPrinter
from src.ast_nodes.statements import (
    ExprStmt, FunctionDef, IfStmt, LetStmt, PrintStmt, ReturnStmt,
    Statement, WhileStmt,
)
from src.lexer.tokenizer import tokenize
from src.lexer.tokens import Token, TokenType
from src.parser.errors import error_at_token, expected_token
from src.parser.grammar import ADDITIVE_OPS, COMPARISON_OPS, MULTIPLICATIVE_OPS


class Parser:
    """Recursive descent parser that builds an AST from tokens.

    Implements the LL(1) grammar defined in grammar.py.
    """

    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.pos: int = 0

    def parse(self) -> list[Statement]:
        """Parse the full program into a statement list."""
        statements: list[Statement] = []
        while not self._check(TokenType.EOF):
            statements.append(self._parse_statement())
        return statements

    def _current(self) -> Token:
        return self.tokens[self.pos]

    def _check(self, tt: TokenType) -> bool:
        return self._current().type == tt

    def _advance(self) -> Token:
        tok = self.tokens[self.pos]
        if tok.type != TokenType.EOF:
            self.pos += 1
        return tok

    def _expect(self, tt: TokenType) -> Token:
        """Consume the current token if it matches, else raise ParseError."""
        if self._check(tt):
            return self._advance()
        raise expected_token(tt, self._current())

    def _match(self, *types: TokenType) -> Token | None:
        """Consume the current token if it matches any of the given types."""
        for tt in types:
            if self._check(tt):
                return self._advance()
        return None

    # ── Statement parsing ──────────────────────────────────────

    def _parse_statement(self) -> Statement:
        if self._check(TokenType.LET):
            return self._parse_let()
        if self._check(TokenType.IF):
            return self._parse_if()
        if self._check(TokenType.WHILE):
            return self._parse_while()
        if self._check(TokenType.FN):
            return self._parse_function_def()
        if self._check(TokenType.RETURN):
            return self._parse_return()
        if self._check(TokenType.PRINT):
            return self._parse_print()
        return self._parse_expr_stmt()

    def _parse_let(self) -> LetStmt:
        """Parse: let IDENT = expr."""
        tok = self._expect(TokenType.LET)
        name_tok = self._expect(TokenType.IDENTIFIER)
        self._expect(TokenType.EQUAL)
        value = self._parse_expression()
        return LetStmt(name=name_tok.lexeme, value=value, line=tok.line, column=tok.column)

    def _parse_if(self) -> IfStmt:
        """Parse: if expr { stmts } (else { stmts })?."""
        tok = self._expect(TokenType.IF)
        condition = self._parse_expression()
        self._expect(TokenType.LBRACE)
        then_body = self._parse_block()
        self._expect(TokenType.RBRACE)
        else_body: list[Statement] = []
        if self._match(TokenType.ELSE):
            self._expect(TokenType.LBRACE)
            else_body = self._parse_block()
            self._expect(TokenType.RBRACE)
        return IfStmt(condition=condition, then_body=then_body,
                      else_body=else_body, line=tok.line, column=tok.column)

    def _parse_while(self) -> WhileStmt:
        """Parse: while expr { stmts }."""
        tok = self._expect(TokenType.WHILE)
        condition = self._parse_expression()
        self._expect(TokenType.LBRACE)
        body = self._parse_block()
        self._expect(TokenType.RBRACE)
        return WhileStmt(condition=condition, body=body, line=tok.line, column=tok.column)

    def _parse_function_def(self) -> FunctionDef:
        """Parse: fn IDENT ( params? ) { stmts }."""
        tok = self._expect(TokenType.FN)
        name_tok = self._expect(TokenType.IDENTIFIER)
        self._expect(TokenType.LPAREN)
        params: list[str] = []
        if not self._check(TokenType.RPAREN):
            params.append(self._expect(TokenType.IDENTIFIER).lexeme)
            while self._match(TokenType.COMMA):
                params.append(self._expect(TokenType.IDENTIFIER).lexeme)
        self._expect(TokenType.RPAREN)
        self._expect(TokenType.LBRACE)
        body = self._parse_block()
        self._expect(TokenType.RBRACE)
        return FunctionDef(name=name_tok.lexeme, params=params, body=body,
                           line=tok.line, column=tok.column)

    def _parse_return(self) -> ReturnStmt:
        """Parse: return expr?."""
        tok = self._expect(TokenType.RETURN)
        value: Expression | None = None
        if not self._check(TokenType.RBRACE) and not self._check(TokenType.EOF):
            value = self._parse_expression()
        return ReturnStmt(value=value, line=tok.line, column=tok.column)

    def _parse_print(self) -> PrintStmt:
        """Parse: print( expr )."""
        tok = self._expect(TokenType.PRINT)
        self._expect(TokenType.LPAREN)
        value = self._parse_expression()
        self._expect(TokenType.RPAREN)
        return PrintStmt(value=value, line=tok.line, column=tok.column)

    def _parse_expr_stmt(self) -> ExprStmt:
        expr = self._parse_expression()
        return ExprStmt(expression=expr, line=expr.line, column=expr.column)

    def _parse_block(self) -> list[Statement]:
        """Parse statements until a closing brace."""
        stmts: list[Statement] = []
        while not self._check(TokenType.RBRACE) and not self._check(TokenType.EOF):
            stmts.append(self._parse_statement())
        return stmts

    # ── Expression parsing (precedence climbing) ───────────────

    def _parse_expression(self) -> Expression:
        return self._parse_comparison()

    def _parse_comparison(self) -> Expression:
        """Parse: addition (comp_op addition)*."""
        left = self._parse_addition()
        while self._current().type in COMPARISON_OPS:
            op_tok = self._advance()
            right = self._parse_addition()
            left = BinaryOp(operator=op_tok.lexeme, left=left, right=right,
                            line=op_tok.line, column=op_tok.column)
        return left

    def _parse_addition(self) -> Expression:
        """Parse: term (('+' | '-') term)*."""
        left = self._parse_term()
        while self._current().type in ADDITIVE_OPS:
            op_tok = self._advance()
            right = self._parse_term()
            left = BinaryOp(operator=op_tok.lexeme, left=left, right=right,
                            line=op_tok.line, column=op_tok.column)
        return left

    def _parse_term(self) -> Expression:
        """Parse: unary (('*' | '/') unary)*."""
        left = self._parse_unary()
        while self._current().type in MULTIPLICATIVE_OPS:
            op_tok = self._advance()
            right = self._parse_unary()
            left = BinaryOp(operator=op_tok.lexeme, left=left, right=right,
                            line=op_tok.line, column=op_tok.column)
        return left

    def _parse_unary(self) -> Expression:
        """Parse: '-' unary | call."""
        if self._check(TokenType.MINUS):
            op_tok = self._advance()
            operand = self._parse_unary()
            return UnaryOp(operator="-", operand=operand,
                           line=op_tok.line, column=op_tok.column)
        return self._parse_call()

    def _parse_call(self) -> Expression:
        """Parse: primary ('(' arguments? ')')?."""
        expr = self._parse_primary()
        if isinstance(expr, Identifier) and self._check(TokenType.LPAREN):
            self._advance()
            args: list[Expression] = []
            if not self._check(TokenType.RPAREN):
                args.append(self._parse_expression())
                while self._match(TokenType.COMMA):
                    args.append(self._parse_expression())
            self._expect(TokenType.RPAREN)
            return FunctionCall(name=expr.name, arguments=args,
                                line=expr.line, column=expr.column)
        return expr

    def _parse_primary(self) -> Expression:
        """Parse: NUMBER | IDENT | '(' expr ')'."""
        tok = self._current()
        if self._match(TokenType.NUMBER):
            return Literal(value=tok.value, line=tok.line, column=tok.column)
        if self._match(TokenType.IDENTIFIER):
            return Identifier(name=tok.lexeme, line=tok.line, column=tok.column)
        if self._match(TokenType.LPAREN):
            expr = self._parse_expression()
            self._expect(TokenType.RPAREN)
            return expr
        raise error_at_token(tok, f"Expected expression, got {tok.type.name} ({tok.lexeme!r})")


def parse(source: str) -> list[Statement]:
    """Convenience function: tokenize and parse source code.

    Args:
        source: The raw source code.

    Returns:
        List of top-level AST statements.
    """
    tokens = tokenize(source)
    return Parser(tokens).parse()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Parse DSL source and print AST")
    ap.add_argument("--input", required=True, help="Source code string")
    ap.add_argument("--print-ast", action="store_true", help="Pretty-print the AST")
    args = ap.parse_args()

    statements = parse(args.input)
    printer = ASTPrinter()
    if args.print_ast:
        print(printer.print_program(statements))
    else:
        print(f"Parsed {len(statements)} statement(s)")
        print(printer.print_program(statements))
