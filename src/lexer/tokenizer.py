"""Finite automaton tokenizer with maximal munch.

Scans source text into a stream of tokens, handling multi-character
operators, keywords vs identifiers, integer and float literals,
and single-line comments.
"""

from __future__ import annotations

import argparse

from src.lexer.source_reader import SourceReader
from src.lexer.tokens import KEYWORDS, Token, TokenType


class LexerError(Exception):
    """Raised when the lexer encounters an invalid character."""

    def __init__(self, message: str, line: int, column: int) -> None:
        self.line = line
        self.column = column
        super().__init__(f"[{line}:{column}] {message}")


class Lexer:
    """Tokenizes source text using a finite automaton approach.

    Uses maximal munch: always matches the longest possible token at
    each position. Handles multi-character operators like <=, >=, ==, !=.
    """

    def __init__(self, source: str) -> None:
        """Initialize the lexer with source text.

        Args:
            source: The raw source code to tokenize.
        """
        self.reader = SourceReader(source)
        self.tokens: list[Token] = []

    def tokenize(self) -> list[Token]:
        """Scan the entire source and return the token list.

        Returns:
            List of tokens ending with an EOF token.

        Raises:
            LexerError: If an unexpected character is encountered.
        """
        while not self.reader.is_at_end():
            self.reader.skip_whitespace()
            if self.reader.is_at_end():
                break
            self._scan_token()

        self.tokens.append(
            Token(TokenType.EOF, "", line=self.reader.line, column=self.reader.column)
        )
        return self.tokens

    def _scan_token(self) -> None:
        """Scan a single token from the current position."""
        line, col = self.reader.line, self.reader.column
        ch = self.reader.advance()

        # Single-character tokens
        simple: dict[str, TokenType] = {
            "(": TokenType.LPAREN,
            ")": TokenType.RPAREN,
            "{": TokenType.LBRACE,
            "}": TokenType.RBRACE,
            ",": TokenType.COMMA,
            ";": TokenType.SEMICOLON,
            "+": TokenType.PLUS,
            "-": TokenType.MINUS,
            "*": TokenType.STAR,
            "/": TokenType.SLASH,
        }

        if ch in simple:
            self.tokens.append(Token(simple[ch], ch, line=line, column=col))
        elif ch == "=":
            if self.reader.match("="):
                self.tokens.append(Token(TokenType.EQUAL_EQUAL, "==", line=line, column=col))
            else:
                self.tokens.append(Token(TokenType.EQUAL, "=", line=line, column=col))
        elif ch == "<":
            if self.reader.match("="):
                self.tokens.append(Token(TokenType.LESS_EQUAL, "<=", line=line, column=col))
            else:
                self.tokens.append(Token(TokenType.LESS, "<", line=line, column=col))
        elif ch == ">":
            if self.reader.match("="):
                self.tokens.append(Token(TokenType.GREATER_EQUAL, ">=", line=line, column=col))
            else:
                self.tokens.append(Token(TokenType.GREATER, ">", line=line, column=col))
        elif ch == "!":
            if self.reader.match("="):
                self.tokens.append(Token(TokenType.BANG_EQUAL, "!=", line=line, column=col))
            else:
                raise LexerError(f"Unexpected character '!'", line, col)
        elif ch.isdigit():
            self._scan_number(ch, line, col)
        elif ch.isalpha() or ch == "_":
            self._scan_identifier(ch, line, col)
        else:
            raise LexerError(f"Unexpected character {ch!r}", line, col)

    def _scan_number(self, first: str, line: int, col: int) -> None:
        """Scan an integer or float literal.

        Args:
            first: The first digit character already consumed.
            line: Line where the number starts.
            col: Column where the number starts.
        """
        text = first
        while not self.reader.is_at_end() and self.reader.peek().isdigit():
            text += self.reader.advance()

        # Check for decimal point
        if self.reader.peek() == "." and self.reader.peek_next().isdigit():
            text += self.reader.advance()  # consume '.'
            while not self.reader.is_at_end() and self.reader.peek().isdigit():
                text += self.reader.advance()
            value: int | float = float(text)
        else:
            value = int(text)

        self.tokens.append(Token(TokenType.NUMBER, text, value=value, line=line, column=col))

    def _scan_identifier(self, first: str, line: int, col: int) -> None:
        """Scan an identifier or keyword.

        Args:
            first: The first character already consumed.
            line: Line where the identifier starts.
            col: Column where the identifier starts.
        """
        text = first
        while not self.reader.is_at_end() and (
            self.reader.peek().isalnum() or self.reader.peek() == "_"
        ):
            text += self.reader.advance()

        token_type = KEYWORDS.get(text, TokenType.IDENTIFIER)
        self.tokens.append(Token(token_type, text, line=line, column=col))


def tokenize(source: str) -> list[Token]:
    """Convenience function to tokenize source text.

    Args:
        source: The raw source code.

    Returns:
        List of tokens.
    """
    return Lexer(source).tokenize()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tokenize DSL source code")
    parser.add_argument("--input", required=True, help="Source code string to tokenize")
    args = parser.parse_args()

    print(f"Source: {args.input!r}\n")
    print("=== Token Stream ===")
    tokens = tokenize(args.input)
    for tok in tokens:
        print(f"  [{tok.line}:{tok.column:>2}] {tok.type.name:<16} {tok.lexeme!r}")
