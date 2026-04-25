"""Character-by-character source reader with position tracking.

Provides a stream interface over raw source text, tracking line and
column numbers for error reporting. Supports peek and advance operations.
"""

from __future__ import annotations


class SourceReader:
    """Reads source text one character at a time with position tracking.

    Attributes:
        source: The full source text.
        pos: Current index into the source string.
        line: Current 1-based line number.
        column: Current 1-based column number.
    """

    def __init__(self, source: str) -> None:
        """Initialize the reader with source text.

        Args:
            source: The raw source code string.
        """
        self.source = source
        self.pos: int = 0
        self.line: int = 1
        self.column: int = 1

    def is_at_end(self) -> bool:
        """Check if the reader has consumed all characters."""
        return self.pos >= len(self.source)

    def peek(self) -> str:
        """Return the current character without advancing.

        Returns:
            The current character, or '\\0' if at end.
        """
        if self.is_at_end():
            return "\0"
        return self.source[self.pos]

    def peek_next(self) -> str:
        """Return the character after the current one without advancing.

        Returns:
            The next character, or '\\0' if at end.
        """
        if self.pos + 1 >= len(self.source):
            return "\0"
        return self.source[self.pos + 1]

    def advance(self) -> str:
        """Consume and return the current character, updating position.

        Returns:
            The consumed character.
        """
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def match(self, expected: str) -> bool:
        """Consume the current character if it matches expected.

        Args:
            expected: The character to match.

        Returns:
            True if the character matched and was consumed.
        """
        if self.is_at_end() or self.source[self.pos] != expected:
            return False
        self.advance()
        return True

    def skip_whitespace(self) -> None:
        """Advance past whitespace and single-line comments (// ...)."""
        while not self.is_at_end():
            ch = self.peek()
            if ch in (" ", "\t", "\r", "\n"):
                self.advance()
            elif ch == "/" and self.peek_next() == "/":
                # Skip single-line comment
                while not self.is_at_end() and self.peek() != "\n":
                    self.advance()
            else:
                break


if __name__ == "__main__":
    source = "let x = 42\nlet y = x + 1  // add one\n"
    reader = SourceReader(source)

    print("=== Character-by-character read ===")
    while not reader.is_at_end():
        line, col = reader.line, reader.column
        ch = reader.advance()
        display = repr(ch) if ch in ("\n", "\t", "\r") else ch
        print(f"  [{line}:{col}] {display}")

    print(f"\nTotal characters read: {reader.pos}")
    print(f"Final position: line {reader.line}, column {reader.column}")
