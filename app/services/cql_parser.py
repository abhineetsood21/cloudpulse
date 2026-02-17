"""
CloudPulse Query Language (CQL) Parser

A lightweight SQL-like filter language for querying cloud cost data,
modeled after Vantage's VQL (Vantage Query Language).

Syntax:
    costs.service = 'Amazon EC2'
    costs.provider = 'aws' AND costs.region = 'us-east-1'
    costs.service IN ('Amazon EC2', 'Amazon S3') AND costs.amount > 100
    costs.tag['environment'] = 'production'

Supported operators: =, !=, >, <, >=, <=, IN, NOT IN, LIKE, NOT LIKE
Logical operators: AND, OR, NOT
Supported fields: costs.*, resources.*, tags.*, financial_commitments.*
"""

import re
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class TokenType(Enum):
    FIELD = "FIELD"
    OPERATOR = "OPERATOR"
    VALUE = "VALUE"
    LOGICAL = "LOGICAL"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    IN = "IN"
    NOT = "NOT"
    LIKE = "LIKE"
    COMMA = "COMMA"
    EOF = "EOF"


@dataclass
class Token:
    type: TokenType
    value: Any


@dataclass
class Condition:
    field: str
    operator: str
    value: Any


@dataclass
class LogicalExpression:
    operator: str  # AND, OR
    left: Any  # Condition or LogicalExpression
    right: Any  # Condition or LogicalExpression


@dataclass
class NotExpression:
    expression: Any


@dataclass
class CQLQuery:
    """Parsed CQL query ready for execution."""
    raw: str
    expression: Any  # Condition, LogicalExpression, or NotExpression
    errors: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0


# Valid field prefixes and their allowed subfields
VALID_PREFIXES = {
    "costs": [
        "provider", "service", "region", "account_id", "category",
        "subcategory", "resource_id", "amount", "currency", "date",
        "tag", "charge_type",
    ],
    "resources": [
        "provider", "service", "region", "account_id", "resource_id",
        "name", "type", "state", "tag",
    ],
    "financial_commitments": [
        "provider", "commitment_id", "commitment_type", "service",
        "region", "account_id", "amount", "utilization",
    ],
    "tags": ["*"],  # Any tag key
    "network_flows": [
        "source_region", "destination_region", "source_vpc",
        "destination_vpc", "service", "amount",
    ],
}

COMPARISON_OPERATORS = {"=", "!=", ">", "<", ">=", "<="}
KEYWORDS = {"AND", "OR", "NOT", "IN", "LIKE", "NULL"}


class CQLTokenizer:
    """Tokenizes a CQL query string."""

    def __init__(self, query: str):
        self.query = query
        self.pos = 0
        self.tokens: list[Token] = []

    def tokenize(self) -> list[Token]:
        while self.pos < len(self.query):
            self._skip_whitespace()
            if self.pos >= len(self.query):
                break

            char = self.query[self.pos]

            if char == "(":
                self.tokens.append(Token(TokenType.LPAREN, "("))
                self.pos += 1
            elif char == ")":
                self.tokens.append(Token(TokenType.RPAREN, ")"))
                self.pos += 1
            elif char == ",":
                self.tokens.append(Token(TokenType.COMMA, ","))
                self.pos += 1
            elif char == "'":
                self.tokens.append(self._read_string())
            elif char in "!=<>":
                self.tokens.append(self._read_operator())
            elif char.isdigit() or (char == "-" and self._peek_digit()):
                self.tokens.append(self._read_number())
            elif char.isalpha() or char == "_":
                self.tokens.append(self._read_identifier())
            else:
                self.pos += 1  # Skip unknown chars

        self.tokens.append(Token(TokenType.EOF, None))
        return self.tokens

    def _skip_whitespace(self):
        while self.pos < len(self.query) and self.query[self.pos].isspace():
            self.pos += 1

    def _peek_digit(self) -> bool:
        return (self.pos + 1 < len(self.query) and
                self.query[self.pos + 1].isdigit())

    def _read_string(self) -> Token:
        self.pos += 1  # skip opening quote
        start = self.pos
        while self.pos < len(self.query) and self.query[self.pos] != "'":
            if self.query[self.pos] == "\\" and self.pos + 1 < len(self.query):
                self.pos += 2  # skip escaped char
            else:
                self.pos += 1
        value = self.query[start:self.pos]
        if self.pos < len(self.query):
            self.pos += 1  # skip closing quote
        return Token(TokenType.VALUE, value)

    def _read_operator(self) -> Token:
        start = self.pos
        if self.query[self.pos:self.pos + 2] in ("!=", ">=", "<="):
            self.pos += 2
        else:
            self.pos += 1
        return Token(TokenType.OPERATOR, self.query[start:self.pos])

    def _read_number(self) -> Token:
        start = self.pos
        if self.query[self.pos] == "-":
            self.pos += 1
        while self.pos < len(self.query) and (
            self.query[self.pos].isdigit() or self.query[self.pos] == "."
        ):
            self.pos += 1
        value = self.query[start:self.pos]
        return Token(TokenType.VALUE, float(value) if "." in value else int(value))

    def _read_identifier(self) -> Token:
        start = self.pos
        while self.pos < len(self.query) and (
            self.query[self.pos].isalnum()
            or self.query[self.pos] in "_.[]'"
        ):
            # Handle tag bracket syntax: costs.tag['key']
            if self.query[self.pos] == "[":
                while self.pos < len(self.query) and self.query[self.pos] != "]":
                    self.pos += 1
                if self.pos < len(self.query):
                    self.pos += 1  # skip ]
            else:
                self.pos += 1

        word = self.query[start:self.pos]
        upper = word.upper()

        if upper in ("AND", "OR"):
            return Token(TokenType.LOGICAL, upper)
        elif upper == "NOT":
            return Token(TokenType.NOT, "NOT")
        elif upper == "IN":
            return Token(TokenType.IN, "IN")
        elif upper == "LIKE":
            return Token(TokenType.LIKE, "LIKE")
        elif upper in ("TRUE", "FALSE"):
            return Token(TokenType.VALUE, upper == "TRUE")
        elif upper == "NULL":
            return Token(TokenType.VALUE, None)
        elif "." in word:
            return Token(TokenType.FIELD, word)
        else:
            return Token(TokenType.VALUE, word)


class CQLParser:
    """Parses tokenized CQL into an AST."""

    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0
        self.errors: list[str] = []

    def parse(self) -> Any:
        if not self.tokens or self.tokens[0].type == TokenType.EOF:
            return None
        expr = self._parse_or()
        if self.current().type != TokenType.EOF:
            self.errors.append(
                f"Unexpected token: {self.current().value}"
            )
        return expr

    def current(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return Token(TokenType.EOF, None)

    def advance(self) -> Token:
        token = self.current()
        self.pos += 1
        return token

    def _parse_or(self) -> Any:
        left = self._parse_and()
        while (self.current().type == TokenType.LOGICAL
               and self.current().value == "OR"):
            self.advance()
            right = self._parse_and()
            left = LogicalExpression("OR", left, right)
        return left

    def _parse_and(self) -> Any:
        left = self._parse_not()
        while (self.current().type == TokenType.LOGICAL
               and self.current().value == "AND"):
            self.advance()
            right = self._parse_not()
            left = LogicalExpression("AND", left, right)
        return left

    def _parse_not(self) -> Any:
        if self.current().type == TokenType.NOT:
            self.advance()
            expr = self._parse_primary()
            return NotExpression(expr)
        return self._parse_primary()

    def _parse_primary(self) -> Any:
        if self.current().type == TokenType.LPAREN:
            self.advance()  # skip (
            expr = self._parse_or()
            if self.current().type == TokenType.RPAREN:
                self.advance()  # skip )
            else:
                self.errors.append("Expected closing parenthesis")
            return expr

        return self._parse_condition()

    def _parse_condition(self) -> Condition:
        # Expect: field operator value
        if self.current().type != TokenType.FIELD:
            self.errors.append(
                f"Expected field name, got: {self.current().value}"
            )
            self.advance()
            return Condition("unknown", "=", None)

        field_token = self.advance()
        field_name = field_token.value

        # Handle NOT IN, NOT LIKE
        negate = False
        if self.current().type == TokenType.NOT:
            negate = True
            self.advance()

        # Handle IN
        if self.current().type == TokenType.IN:
            self.advance()
            values = self._parse_value_list()
            op = "NOT IN" if negate else "IN"
            return Condition(field_name, op, values)

        # Handle LIKE
        if self.current().type == TokenType.LIKE:
            self.advance()
            value = self.advance().value
            op = "NOT LIKE" if negate else "LIKE"
            return Condition(field_name, op, value)

        # Handle comparison operators
        if self.current().type == TokenType.OPERATOR:
            op_token = self.advance()
            value = self.advance().value
            return Condition(field_name, op_token.value, value)

        self.errors.append(f"Expected operator after field '{field_name}'")
        return Condition(field_name, "=", None)

    def _parse_value_list(self) -> list:
        values = []
        if self.current().type == TokenType.LPAREN:
            self.advance()  # skip (
            while self.current().type != TokenType.RPAREN:
                if self.current().type == TokenType.EOF:
                    self.errors.append("Unclosed value list")
                    break
                if self.current().type == TokenType.COMMA:
                    self.advance()
                    continue
                values.append(self.advance().value)
            if self.current().type == TokenType.RPAREN:
                self.advance()  # skip )
        return values


def parse_cql(query: str) -> CQLQuery:
    """
    Parse a CQL query string into a structured CQLQuery object.

    Examples:
        >>> q = parse_cql("costs.service = 'Amazon EC2'")
        >>> q.is_valid
        True

        >>> q = parse_cql("costs.provider = 'aws' AND costs.region IN ('us-east-1', 'us-west-2')")
        >>> q.is_valid
        True
    """
    if not query or not query.strip():
        return CQLQuery(raw=query or "", expression=None, errors=["Empty query"])

    try:
        tokenizer = CQLTokenizer(query.strip())
        tokens = tokenizer.tokenize()
        parser = CQLParser(tokens)
        expression = parser.parse()
        return CQLQuery(
            raw=query,
            expression=expression,
            errors=parser.errors,
        )
    except Exception as e:
        logger.error(f"CQL parse error: {e}")
        return CQLQuery(raw=query, expression=None, errors=[str(e)])


def validate_cql(query: str) -> tuple[bool, list[str]]:
    """Validate a CQL query and return (is_valid, errors)."""
    result = parse_cql(query)
    return result.is_valid, result.errors


def cql_to_sql_where(query: str, table_alias: str = "c") -> tuple[str, list]:
    """
    Convert a CQL query to a SQL WHERE clause fragment.
    Returns (sql_fragment, params) for use with SQLAlchemy.
    """
    parsed = parse_cql(query)
    if not parsed.is_valid or parsed.expression is None:
        return "1=1", []

    params = []
    sql = _expr_to_sql(parsed.expression, table_alias, params)
    return sql, params


def _expr_to_sql(expr: Any, alias: str, params: list) -> str:
    if isinstance(expr, Condition):
        col = _field_to_column(expr.field, alias)
        if expr.operator == "IN":
            placeholders = ", ".join([":p%d" % (len(params) + i) for i in range(len(expr.value))])
            params.extend(expr.value)
            return f"{col} IN ({placeholders})"
        elif expr.operator == "NOT IN":
            placeholders = ", ".join([":p%d" % (len(params) + i) for i in range(len(expr.value))])
            params.extend(expr.value)
            return f"{col} NOT IN ({placeholders})"
        elif expr.operator == "LIKE":
            params.append(expr.value)
            return f"{col} LIKE :p{len(params) - 1}"
        elif expr.operator == "NOT LIKE":
            params.append(expr.value)
            return f"{col} NOT LIKE :p{len(params) - 1}"
        else:
            params.append(expr.value)
            return f"{col} {expr.operator} :p{len(params) - 1}"
    elif isinstance(expr, LogicalExpression):
        left = _expr_to_sql(expr.left, alias, params)
        right = _expr_to_sql(expr.right, alias, params)
        return f"({left} {expr.operator} {right})"
    elif isinstance(expr, NotExpression):
        inner = _expr_to_sql(expr.expression, alias, params)
        return f"NOT ({inner})"
    return "1=1"


def _field_to_column(field: str, alias: str) -> str:
    """Map CQL field names to actual database columns."""
    mapping = {
        "costs.service": f"{alias}.service",
        "costs.region": f"{alias}.region",
        "costs.provider": f"{alias}.provider",
        "costs.account_id": f"{alias}.account_id",
        "costs.amount": f"{alias}.amount",
        "costs.currency": f"{alias}.currency",
        "costs.date": f"{alias}.date",
        "costs.resource_id": f"{alias}.resource_id",
        "costs.category": f"{alias}.category",
        "costs.charge_type": f"{alias}.charge_type",
    }
    return mapping.get(field, f"{alias}.{field.split('.')[-1]}")


# --- DuckDB SQL Generation (for FOCUS-schema Parquet data) ---

# Map CQL fields to FOCUS schema columns in DuckDB
FOCUS_FIELD_MAP = {
    "costs.service": "service",
    "costs.region": "region",
    "costs.provider": "provider",
    "costs.account_id": "account_id",
    "costs.amount": "amount",
    "costs.currency": "currency",
    "costs.date": "usage_date",
    "costs.resource_id": "resource_id",
    "costs.charge_type": "charge_type",
    "resources.resource_id": "resource_id",
    "resources.service": "service",
    "resources.region": "region",
    "resources.provider": "provider",
    "resources.account_id": "account_id",
}


def cql_to_duckdb_sql(query: str) -> tuple[str, list]:
    """
    Convert a CQL query to a DuckDB SQL WHERE clause.

    Returns (sql_fragment, params) for use with DuckDB parameterized queries.
    Uses $1, $2 style positional params.

    Example:
        >>> sql, params = cql_to_duckdb_sql("costs.service = 'Amazon EC2'")
        >>> sql
        "service = $1"
        >>> params
        ['Amazon EC2']
    """
    parsed = parse_cql(query)
    if not parsed.is_valid or parsed.expression is None:
        return "1=1", []

    params = []
    sql = _expr_to_duckdb(parsed.expression, params)
    return sql, params


def _expr_to_duckdb(expr: Any, params: list) -> str:
    """Recursively convert CQL AST to DuckDB SQL."""
    if isinstance(expr, Condition):
        col = _focus_field(expr.field)

        # Handle tag lookups: costs.tag['env'] -> json_extract_string(tags, '$.env')
        if "tag[" in expr.field:
            tag_key = _extract_tag_key(expr.field)
            col = f"json_extract_string(tags, '$.{tag_key}')"

        if expr.operator == "IN":
            placeholders = ", ".join(
                [f"${len(params) + i + 1}" for i in range(len(expr.value))]
            )
            params.extend(expr.value)
            return f"{col} IN ({placeholders})"
        elif expr.operator == "NOT IN":
            placeholders = ", ".join(
                [f"${len(params) + i + 1}" for i in range(len(expr.value))]
            )
            params.extend(expr.value)
            return f"{col} NOT IN ({placeholders})"
        elif expr.operator == "LIKE":
            params.append(expr.value)
            return f"{col} LIKE ${len(params)}"
        elif expr.operator == "NOT LIKE":
            params.append(expr.value)
            return f"{col} NOT LIKE ${len(params)}"
        else:
            params.append(expr.value)
            return f"{col} {expr.operator} ${len(params)}"

    elif isinstance(expr, LogicalExpression):
        left = _expr_to_duckdb(expr.left, params)
        right = _expr_to_duckdb(expr.right, params)
        return f"({left} {expr.operator} {right})"

    elif isinstance(expr, NotExpression):
        inner = _expr_to_duckdb(expr.expression, params)
        return f"NOT ({inner})"

    return "1=1"


def _focus_field(field: str) -> str:
    """Map a CQL field name to a FOCUS schema column."""
    return FOCUS_FIELD_MAP.get(field, field.split(".")[-1])


def _extract_tag_key(field: str) -> str:
    """Extract tag key from CQL field like costs.tag['environment']."""
    match = re.search(r"tag\['([^']+)'\]", field)
    if match:
        return match.group(1)
    match = re.search(r"tag\[([^\]]+)\]", field)
    if match:
        return match.group(1)
    return "unknown"
