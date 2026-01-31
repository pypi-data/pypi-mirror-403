"""Dynamic database schema introspection for copilot search."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ColumnInfo:
    """Information about a database column."""

    name: str
    data_type: str
    is_nullable: bool
    column_default: str | None = None
    description: str | None = None


@dataclass
class TableInfo:
    """Information about a database table."""

    name: str
    columns: list[ColumnInfo] = field(default_factory=list)
    primary_key: list[str] = field(default_factory=list)
    foreign_keys: list[dict[str, str]] = field(default_factory=list)
    row_count: int = 0
    sample_values: dict[str, list[Any]] = field(default_factory=dict)


@dataclass
class SchemaInfo:
    """Complete schema information for copilot."""

    tables: dict[str, TableInfo] = field(default_factory=dict)

    def to_prompt_context(self) -> str:
        """Convert schema info to a prompt-friendly format."""
        lines = ["## Database Schema (Auto-discovered from live database)\n"]
        lines.append("The following tables and columns are available. Use exact column names.\n")

        for table_name, table in sorted(self.tables.items()):
            lines.append(f"### {table_name}")
            if table.row_count > 0:
                lines.append(f"Approximate rows: {table.row_count}")
            lines.append("```sql")
            lines.append(f"CREATE TABLE {table_name} (")

            col_lines = []
            for col in table.columns:
                nullable = "" if col.is_nullable else " NOT NULL"
                col_line = f"    {col.name} {col.data_type}{nullable}"
                if col.description:
                    col_line += f"  -- {col.description}"
                col_lines.append(col_line)

            lines.append(",\n".join(col_lines))
            lines.append(");")
            lines.append("```")

            if table.sample_values:
                lines.append("\n**Actual values in database:**")
                for col_name, values in table.sample_values.items():
                    if values:
                        sample_str = ", ".join(repr(v) for v in values[:10])
                        lines.append(f"- `{col_name}`: {sample_str}")

            if table.foreign_keys:
                lines.append("\n**Relationships:**")
                for fk in table.foreign_keys:
                    lines.append(f"- `{fk['column']}` references `{fk['references']}`")

            lines.append("")

        return "\n".join(lines)

    def get_table_summary(self) -> str:
        """Get a brief summary of available tables."""
        lines = ["Available tables:"]
        for name, table in sorted(self.tables.items()):
            col_count = len(table.columns)
            lines.append(f"- {name} ({col_count} columns, ~{table.row_count} rows)")
        return "\n".join(lines)


class SchemaIntrospector:
    """Introspects database schema dynamically - discovers ALL tables."""

    def __init__(self, pool: Any):
        self.pool = pool
        self._cache: dict[str, SchemaInfo] = {}

    async def get_schema(
        self, project_id: str, force_refresh: bool = False
    ) -> SchemaInfo:
        """Get schema information for a project, using cache if available."""
        cache_key = project_id
        if cache_key in self._cache and not force_refresh:
            return self._cache[cache_key]

        schema = await self._introspect_schema(project_id)
        self._cache[cache_key] = schema
        return schema

    async def _introspect_schema(self, project_id: str) -> SchemaInfo:
        """Query the database to discover ALL tables and their schema."""
        schema = SchemaInfo()

        async with self.pool.acquire() as conn:
            tables = await self._discover_all_tables(conn)
            logger.info(f"Discovered {len(tables)} tables in database")

            for table_name in tables:
                table_info = await self._introspect_table(conn, table_name, project_id)
                if table_info:
                    schema.tables[table_name] = table_info

        return schema

    async def _discover_all_tables(self, conn: Any) -> list[str]:
        """Discover all user tables in the public schema."""
        query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """
        rows = await conn.fetch(query)
        return [row["table_name"] for row in rows]

    async def _introspect_table(
        self, conn: Any, table_name: str, project_id: str
    ) -> TableInfo | None:
        """Introspect a single table."""
        try:
            columns = await self._get_columns(conn, table_name)
            if not columns:
                return None

            table = TableInfo(name=table_name, columns=columns)

            table.primary_key = await self._get_primary_key(conn, table_name)
            table.foreign_keys = await self._get_foreign_keys(conn, table_name)

            has_project_id = any(c.name == "project_id" for c in columns)
            if has_project_id:
                table.row_count = await self._get_row_count(conn, table_name, project_id)
                table.sample_values = await self._get_sample_values(
                    conn, table_name, project_id, columns
                )
            else:
                table.row_count = await self._get_total_row_count(conn, table_name)

            return table
        except Exception as e:
            logger.warning(f"Failed to introspect table {table_name}: {e}")
            return None

    async def _get_columns(self, conn: Any, table_name: str) -> list[ColumnInfo]:
        """Get column information for a table."""
        query = """
            SELECT
                column_name,
                data_type,
                udt_name,
                is_nullable,
                column_default,
                col_description(
                    (quote_ident(table_schema) || '.' || quote_ident(table_name))::regclass,
                    ordinal_position
                ) as description
            FROM information_schema.columns
            WHERE table_name = $1 AND table_schema = 'public'
            ORDER BY ordinal_position
        """
        rows = await conn.fetch(query, table_name)
        return [
            ColumnInfo(
                name=row["column_name"],
                data_type=self._format_data_type(row["data_type"], row["udt_name"]),
                is_nullable=row["is_nullable"] == "YES",
                column_default=row["column_default"],
                description=row["description"],
            )
            for row in rows
        ]

    def _format_data_type(self, data_type: str, udt_name: str) -> str:
        """Format data type for display."""
        if data_type == "ARRAY":
            return f"{udt_name.lstrip('_')}[]"
        if data_type == "USER-DEFINED":
            return udt_name
        return data_type

    async def _get_primary_key(self, conn: Any, table_name: str) -> list[str]:
        """Get primary key columns for a table."""
        query = """
            SELECT a.attname
            FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
            WHERE i.indrelid = $1::regclass AND i.indisprimary
        """
        try:
            rows = await conn.fetch(query, table_name)
            return [row["attname"] for row in rows]
        except Exception:
            return []

    async def _get_foreign_keys(self, conn: Any, table_name: str) -> list[dict[str, str]]:
        """Get foreign key relationships for a table."""
        query = """
            SELECT
                kcu.column_name,
                ccu.table_name AS foreign_table,
                ccu.column_name AS foreign_column
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name = $1
                AND tc.table_schema = 'public'
        """
        try:
            rows = await conn.fetch(query, table_name)
            return [
                {
                    "column": row["column_name"],
                    "references": f"{row['foreign_table']}({row['foreign_column']})",
                }
                for row in rows
            ]
        except Exception:
            return []

    async def _get_row_count(self, conn: Any, table_name: str, project_id: str) -> int:
        """Get row count for a table filtered by project."""
        try:
            query = f'SELECT COUNT(*) FROM "{table_name}" WHERE project_id = $1'
            result = await conn.fetchval(query, project_id)
            return result or 0
        except Exception:
            return 0

    async def _get_total_row_count(self, conn: Any, table_name: str) -> int:
        """Get total row count for tables without project_id."""
        try:
            query = f'SELECT COUNT(*) FROM "{table_name}"'
            result = await conn.fetchval(query)
            return result or 0
        except Exception:
            return 0

    async def _get_sample_values(
        self,
        conn: Any,
        table_name: str,
        project_id: str,
        columns: list[ColumnInfo],
    ) -> dict[str, list[Any]]:
        """Get sample distinct values for columns that are useful for filtering."""
        interesting_types = {"text", "character varying", "varchar"}
        skip_columns = {
            "id", "created_at", "updated_at", "project_id", "org_id", "user_id",
            "session_id", "task_id", "event_id", "search_vector", "embedding",
        }

        samples: dict[str, list[Any]] = {}

        for col in columns:
            if col.name in skip_columns:
                continue
            if col.data_type.lower() not in interesting_types:
                continue

            try:
                query = f"""
                    SELECT DISTINCT "{col.name}"
                    FROM "{table_name}"
                    WHERE project_id = $1 AND "{col.name}" IS NOT NULL
                    LIMIT 15
                """
                rows = await conn.fetch(query, project_id)
                values = [row[col.name] for row in rows if row[col.name]]
                if values and len(values) <= 15:
                    samples[col.name] = values
            except Exception:
                pass

        return samples

    def clear_cache(self) -> None:
        """Clear the schema cache."""
        self._cache.clear()


_introspector: SchemaIntrospector | None = None


def get_schema_introspector(pool: Any) -> SchemaIntrospector:
    """Get or create the schema introspector singleton."""
    global _introspector
    if _introspector is None:
        _introspector = SchemaIntrospector(pool)
    return _introspector


def reset_schema_introspector() -> None:
    """Reset the schema introspector (for testing)."""
    global _introspector
    if _introspector:
        _introspector.clear_cache()
    _introspector = None
