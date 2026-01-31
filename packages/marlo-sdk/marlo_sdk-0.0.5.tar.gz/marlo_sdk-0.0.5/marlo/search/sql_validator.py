"""AST-based SQL query validator using sqlglot."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Sequence

try:
    import sqlglot
    from sqlglot import exp
    _SQLGLOT_ERROR = None
except ModuleNotFoundError as exc:
    sqlglot = None  # type: ignore[assignment]
    exp = None  # type: ignore[assignment]
    _SQLGLOT_ERROR = exc

logger = logging.getLogger(__name__)

ALLOWED_TABLES: frozenset[str] | None = None

MAX_LIMIT = 10000
MAX_QUERY_LENGTH = 4000


@dataclass
class ValidationResult:
    """Result of SQL validation."""

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def validate_sql(
    query: str,
    *,
    required_project_id_filter: bool = True,
    allowed_tables: Sequence[str] | None = None,
    max_limit: int = MAX_LIMIT,
) -> ValidationResult:
    """
    Validate a SQL query using AST parsing.

    Args:
        query: The SQL query string to validate
        required_project_id_filter: Whether project_id filter is required
        allowed_tables: Override the default allowed tables
        max_limit: Maximum allowed LIMIT value

    Returns:
        ValidationResult with is_valid, errors, and warnings
    """
    if sqlglot is None:
        return ValidationResult(
            is_valid=False,
            errors=["sqlglot is required for SQL validation"],
        )

    errors: list[str] = []
    warnings: list[str] = []

    if not query or not query.strip():
        return ValidationResult(is_valid=False, errors=["Empty query"])

    if len(query) > MAX_QUERY_LENGTH:
        return ValidationResult(
            is_valid=False,
            errors=[f"Query exceeds maximum length of {MAX_QUERY_LENGTH} characters"],
        )

    try:
        parsed = sqlglot.parse(query, dialect="postgres")
    except Exception as e:
        return ValidationResult(
            is_valid=False,
            errors=[f"SQL parse error: {str(e)}"],
        )

    if not parsed or not parsed[0]:
        return ValidationResult(is_valid=False, errors=["Failed to parse query"])

    if len(parsed) > 1:
        errors.append("Multiple statements not allowed")

    statement = parsed[0]

    if not _is_select_statement(statement):
        errors.append("Only SELECT statements are allowed")
        return ValidationResult(is_valid=False, errors=errors)

    tables_used = _extract_tables(statement)

    if allowed_tables is not None:
        effective_allowed = set(allowed_tables)
        for table in tables_used:
            if table.lower() not in {t.lower() for t in effective_allowed}:
                errors.append(f"Table '{table}' is not in allowed list: {sorted(effective_allowed)}")

    if required_project_id_filter:
        has_filter = _has_project_id_filter(statement)
        if not has_filter:
            has_filter = _has_project_id_filter_regex(query)
        if not has_filter:
            errors.append("Query must include a filter on project_id")

    limit_value = _extract_limit(statement)
    if limit_value is None:
        errors.append("Query must have a LIMIT clause")
    elif limit_value > max_limit:
        errors.append(f"LIMIT {limit_value} exceeds maximum allowed value of {max_limit}")

    if _has_write_operation(statement):
        errors.append("Write operations (INSERT, UPDATE, DELETE) are not allowed")

    if _has_subquery_write(statement):
        errors.append("Subqueries with write operations are not allowed")

    if _has_dangerous_functions(statement):
        errors.append("Dangerous functions are not allowed")

    if _has_system_tables(statement):
        errors.append("Access to system tables is not allowed")

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


def _is_select_statement(statement: exp.Expression) -> bool:
    """Check if statement is a SELECT statement (including UNION, CTE)."""
    if isinstance(statement, exp.Select):
        return True
    if isinstance(statement, (exp.Union, exp.Intersect, exp.Except)):
        return True
    if hasattr(statement, "this") and isinstance(statement.this, exp.Select):
        return True
    return False


def _extract_tables(statement: exp.Expression) -> set[str]:
    """Extract all table names referenced in the statement."""
    tables: set[str] = set()

    for table in statement.find_all(exp.Table):
        table_name = table.name
        if table_name:
            tables.add(table_name)

    return tables


def _has_project_id_filter(statement: exp.Expression) -> bool:
    """Check if statement has project_id filter in WHERE clause.

    Security requirements:
    - Must have project_id column compared against a parameter placeholder
    - Self-referential comparisons (project_id = project_id) are rejected
    - Hardcoded string values are rejected (must use parameterized query)
    """
    for where in statement.find_all(exp.Where):
        if _check_where_for_project_id(where):
            return True

    for join in statement.find_all(exp.Join):
        on_clause = join.args.get("on")
        if on_clause and _check_expression_for_project_id(on_clause):
            return True

    return False


def _check_where_for_project_id(where_clause: exp.Expression) -> bool:
    """Check WHERE clause for valid project_id filter."""
    return _check_expression_for_project_id(where_clause)


def _check_expression_for_project_id(node: exp.Expression) -> bool:
    """Recursively check an expression for project_id = $1 pattern."""
    for eq in node.find_all(exp.EQ):
        left = eq.left
        right = eq.right

        if left is None or right is None:
            continue

        left_is_project_id = _is_project_id_column(left)
        right_is_project_id = _is_project_id_column(right)

        if left_is_project_id and right_is_project_id:
            continue

        left_is_param = _is_parameter_placeholder(left)
        right_is_param = _is_parameter_placeholder(right)

        if left_is_project_id and right_is_param:
            return True
        if right_is_project_id and left_is_param:
            return True

    for in_expr in node.find_all(exp.In):
        column = in_expr.this
        if column is None:
            continue

        if _is_project_id_column(column):
            expressions = in_expr.expressions
            if expressions:
                for expr in expressions:
                    if _is_parameter_placeholder(expr):
                        return True
            query = in_expr.args.get("query")
            if query:
                return True

    return False


def _is_project_id_column(node: exp.Expression) -> bool:
    """Check if node is a project_id column (with or without table alias)."""
    if isinstance(node, exp.Column):
        col_name = node.name
        if col_name and col_name.lower() == "project_id":
            return True

    if hasattr(node, "this"):
        inner = node.this
        if isinstance(inner, str) and inner.lower() == "project_id":
            return True
        if isinstance(inner, exp.Column):
            return _is_project_id_column(inner)

    return False


def _is_parameter_placeholder(node: exp.Expression) -> bool:
    """Check if node is any valid parameter placeholder ($1, $2, :param, ?, etc.)."""
    if node is None:
        return False

    if isinstance(node, exp.Placeholder):
        return True

    if isinstance(node, exp.Parameter):
        return True

    node_type = type(node).__name__
    if "placeholder" in node_type.lower() or "parameter" in node_type.lower():
        return True

    if hasattr(node, "sql"):
        try:
            sql_str = node.sql()
            if sql_str and re.match(r"^\$\d+$", sql_str):
                return True
            if sql_str and re.match(r"^:\w+$", sql_str):
                return True
        except Exception:
            pass

    node_str = str(node)
    if re.match(r"^\$\d+$", node_str):
        return True

    return False


def _has_project_id_filter_regex(query: str) -> bool:
    """Fallback regex check for project_id = $1 pattern.

    This handles cases where AST parsing might miss the pattern.
    """
    query_normalized = " ".join(query.lower().split())

    patterns = [
        r"project_id\s*=\s*\$1\b",
        r"\bproject_id\s*=\s*\$1\b",
        r"\.project_id\s*=\s*\$1\b",
        r"project_id\s*=\s*\$\d+\b",
        r"\.project_id\s*=\s*\$\d+\b",
        r"project_id\s+in\s*\(\s*\$1",
        r"project_id\s*=\s*:\w+",
    ]

    for pattern in patterns:
        if re.search(pattern, query_normalized):
            return True

    return False


def _extract_limit(statement: exp.Expression) -> int | None:
    """Extract the LIMIT value from the statement."""
    limit_node = statement.find(exp.Limit)
    if limit_node is None:
        return None

    limit_expr = limit_node.expression
    if limit_expr is None:
        return None

    if isinstance(limit_expr, exp.Literal):
        try:
            return int(limit_expr.this)
        except (ValueError, TypeError):
            return None

    if hasattr(limit_expr, "this"):
        try:
            return int(limit_expr.this)
        except (ValueError, TypeError):
            pass

    return None


def _has_write_operation(statement: exp.Expression) -> bool:
    """Check if statement contains any write operations."""
    write_types = (
        exp.Insert,
        exp.Update,
        exp.Delete,
        exp.Drop,
        exp.Alter,
        exp.Create,
        exp.TruncateTable,
        exp.Merge,
    )
    return isinstance(statement, write_types)


def _has_subquery_write(statement: exp.Expression) -> bool:
    """Check if any subquery contains write operations."""
    write_types = (
        exp.Insert,
        exp.Update,
        exp.Delete,
        exp.Drop,
        exp.Alter,
        exp.Create,
        exp.TruncateTable,
        exp.Merge,
    )
    for subquery in statement.find_all(exp.Subquery):
        for child in subquery.walk():
            if isinstance(child, write_types):
                return True
    return False


def _has_dangerous_functions(statement: exp.Expression) -> bool:
    """Check for dangerous SQL functions that could be exploited."""
    dangerous_functions = {
        "pg_read_file",
        "pg_read_binary_file",
        "pg_ls_dir",
        "pg_stat_file",
        "lo_import",
        "lo_export",
        "dblink",
        "dblink_exec",
        "copy",
        "pg_execute_server_program",
        "pg_file_write",
        "pg_file_rename",
        "pg_file_unlink",
    }

    for func in statement.find_all(exp.Func):
        func_name = func.name.lower() if func.name else ""
        if func_name in dangerous_functions:
            return True

    for anon in statement.find_all(exp.Anonymous):
        func_name = anon.name.lower() if hasattr(anon, "name") and anon.name else ""
        if func_name in dangerous_functions:
            return True

    return False


def _has_system_tables(statement: exp.Expression) -> bool:
    """Check if query accesses PostgreSQL system tables."""
    system_prefixes = (
        "pg_",
        "information_schema.",
    )

    system_tables = {
        "pg_catalog",
        "pg_class",
        "pg_namespace",
        "pg_tables",
        "pg_views",
        "pg_indexes",
        "pg_stat",
        "pg_settings",
        "pg_roles",
        "pg_user",
        "pg_shadow",
        "pg_authid",
    }

    for table in statement.find_all(exp.Table):
        table_name = table.name.lower() if table.name else ""
        schema_name = table.db.lower() if table.db else ""

        full_name = f"{schema_name}.{table_name}" if schema_name else table_name

        if any(full_name.startswith(prefix) for prefix in system_prefixes):
            return True

        if table_name in system_tables or full_name in system_tables:
            return True

    return False
