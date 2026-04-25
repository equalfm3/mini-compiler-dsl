"""Grammar rule definitions and first/follow sets.

Documents the DSL grammar and provides lookup tables for the parser
to decide which production rule to apply based on the current token.
"""

from __future__ import annotations

from src.lexer.tokens import TokenType

# ============================================================
# Grammar (LL(1) recursive descent)
# ============================================================
#
# program      -> statement*
# statement    -> let_stmt | if_stmt | while_stmt | fn_def
#               | return_stmt | print_stmt | expr_stmt
# let_stmt     -> 'let' IDENT '=' expr
# if_stmt      -> 'if' expr '{' statement* '}' ('else' '{' statement* '}')?
# while_stmt   -> 'while' expr '{' statement* '}'
# fn_def       -> 'fn' IDENT '(' params? ')' '{' statement* '}'
# return_stmt  -> 'return' expr?
# print_stmt   -> 'print' '(' expr ')'
# expr_stmt    -> expr
#
# expr         -> comparison
# comparison   -> addition (('<' | '<=' | '>' | '>=' | '==' | '!=') addition)*
# addition     -> term (('+' | '-') term)*
# term         -> unary (('*' | '/') unary)*
# unary        -> '-' unary | call
# call         -> primary ('(' arguments? ')')?
# primary      -> NUMBER | IDENT | '(' expr ')'
# params       -> IDENT (',' IDENT)*
# arguments    -> expr (',' expr)*
# ============================================================

# FIRST sets: tokens that can start each non-terminal
FIRST_STATEMENT: set[TokenType] = {
    TokenType.LET,
    TokenType.IF,
    TokenType.WHILE,
    TokenType.FN,
    TokenType.RETURN,
    TokenType.PRINT,
    TokenType.NUMBER,
    TokenType.IDENTIFIER,
    TokenType.LPAREN,
    TokenType.MINUS,
}

FIRST_EXPRESSION: set[TokenType] = {
    TokenType.NUMBER,
    TokenType.IDENTIFIER,
    TokenType.LPAREN,
    TokenType.MINUS,
}

# FOLLOW sets: tokens that can appear after each non-terminal
FOLLOW_STATEMENT: set[TokenType] = {
    TokenType.RBRACE,
    TokenType.EOF,
} | FIRST_STATEMENT

COMPARISON_OPS: set[TokenType] = {
    TokenType.LESS,
    TokenType.LESS_EQUAL,
    TokenType.GREATER,
    TokenType.GREATER_EQUAL,
    TokenType.EQUAL_EQUAL,
    TokenType.BANG_EQUAL,
}

ADDITIVE_OPS: set[TokenType] = {
    TokenType.PLUS,
    TokenType.MINUS,
}

MULTIPLICATIVE_OPS: set[TokenType] = {
    TokenType.STAR,
    TokenType.SLASH,
}


def can_start_statement(token_type: TokenType) -> bool:
    """Check if a token type can begin a statement.

    Args:
        token_type: The token type to check.

    Returns:
        True if this token can start a statement.
    """
    return token_type in FIRST_STATEMENT


def can_start_expression(token_type: TokenType) -> bool:
    """Check if a token type can begin an expression.

    Args:
        token_type: The token type to check.

    Returns:
        True if this token can start an expression.
    """
    return token_type in FIRST_EXPRESSION


if __name__ == "__main__":
    print("=== DSL Grammar ===\n")
    print("Statement starters:")
    for tt in sorted(FIRST_STATEMENT, key=lambda t: t.name):
        print(f"  {tt.name}")

    print("\nExpression starters:")
    for tt in sorted(FIRST_EXPRESSION, key=lambda t: t.name):
        print(f"  {tt.name}")

    print("\nComparison operators:")
    for tt in sorted(COMPARISON_OPS, key=lambda t: t.name):
        print(f"  {tt.name}")

    print("\nPrecedence (low to high):")
    print("  1. Comparison  (<, <=, >, >=, ==, !=)")
    print("  2. Addition    (+, -)")
    print("  3. Term        (*, /)")
    print("  4. Unary       (-)")
    print("  5. Call        (function call)")
    print("  6. Primary     (literals, identifiers, grouping)")
