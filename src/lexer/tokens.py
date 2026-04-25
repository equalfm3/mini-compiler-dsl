"""Token types and token dataclass definitions.

Defines the TokenType enum for all lexical categories and the Token
dataclass that carries type, lexeme, value, and source position.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any


class TokenType(Enum):
    """All lexical token categories for the DSL."""

    # Literals
    NUMBER = auto()
    IDENTIFIER = auto()

    # Keywords
    LET = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    FN = auto()
    RETURN = auto()
    PRINT = auto()

    # Arithmetic operators
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()

    # Comparison operators
    LESS = auto()
    LESS_EQUAL = auto()
    GREATER = auto()
    GREATER_EQUAL = auto()
    EQUAL_EQUAL = auto()
    BANG_EQUAL = auto()

    # Assignment
    EQUAL = auto()

    # Punctuation
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    COMMA = auto()
    SEMICOLON = auto()

    # Special
    EOF = auto()


# Map keyword strings to their token types
KEYWORDS: dict[str, TokenType] = {
    "let": TokenType.LET,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "while": TokenType.WHILE,
    "fn": TokenType.FN,
    "return": TokenType.RETURN,
    "print": TokenType.PRINT,
}


@dataclass(frozen=True)
class Token:
    """A single lexical token with source position.

    Attributes:
        type: The category of this token.
        lexeme: The raw text that produced this token.
        value: Parsed value for literals (int/float for numbers, None otherwise).
        line: 1-based line number in source.
        column: 1-based column number in source.
    """

    type: TokenType
    lexeme: str
    value: Any = None
    line: int = 1
    column: int = 1

    def __repr__(self) -> str:
        if self.value is not None:
            return f"Token({self.type.name}, {self.lexeme!r}, {self.value!r})"
        return f"Token({self.type.name}, {self.lexeme!r})"


if __name__ == "__main__":
    # Demo: show all token types and a sample token
    print("=== Token Types ===")
    for tt in TokenType:
        print(f"  {tt.name}")

    print("\n=== Sample Tokens ===")
    samples = [
        Token(TokenType.LET, "let", line=1, column=1),
        Token(TokenType.IDENTIFIER, "x", line=1, column=5),
        Token(TokenType.EQUAL, "=", line=1, column=7),
        Token(TokenType.NUMBER, "42", value=42, line=1, column=9),
        Token(TokenType.PLUS, "+", line=1, column=12),
        Token(TokenType.NUMBER, "3.14", value=3.14, line=1, column=14),
        Token(TokenType.LESS_EQUAL, "<=", line=1, column=19),
    ]
    for tok in samples:
        print(f"  {tok}")

    print(f"\n=== Keywords ===")
    for kw, tt in KEYWORDS.items():
        print(f"  {kw!r} -> {tt.name}")
