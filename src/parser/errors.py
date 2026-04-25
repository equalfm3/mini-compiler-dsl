"""Parse error reporting with source location.

Provides structured error types for the parser, including the token
that caused the error and a human-readable message.
"""

from __future__ import annotations

from src.lexer.tokens import Token, TokenType


class ParseError(Exception):
    """Raised when the parser encounters an unexpected token.

    Attributes:
        message: Human-readable error description.
        token: The token that caused the error.
    """

    def __init__(self, message: str, token: Token) -> None:
        self.token = token
        loc = f"[{token.line}:{token.column}]"
        super().__init__(f"{loc} {message}")


def error_at_token(token: Token, message: str) -> ParseError:
    """Create a ParseError at the given token's location.

    Args:
        token: The offending token.
        message: Description of what went wrong.

    Returns:
        A ParseError with location information.
    """
    return ParseError(message, token)


def expected_token(expected: TokenType, got: Token) -> ParseError:
    """Create a ParseError for an unexpected token type.

    Args:
        expected: The token type that was expected.
        got: The token that was actually found.

    Returns:
        A ParseError describing the mismatch.
    """
    return ParseError(
        f"Expected {expected.name}, got {got.type.name} ({got.lexeme!r})", got
    )


if __name__ == "__main__":
    # Demo: show error formatting
    tok = Token(TokenType.NUMBER, "42", value=42, line=3, column=10)
    err = expected_token(TokenType.SEMICOLON, tok)
    print(f"=== Parse Error Demo ===")
    print(f"  {err}")

    err2 = error_at_token(tok, "Unexpected token in expression")
    print(f"  {err2}")
