"""Capture PostgreSQL settings and configuration"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import psycopg

logger = logging.getLogger(__name__)


@dataclass
class PostgreSQLSettings:
    """Container for PostgreSQL settings"""

    version: str
    server_version_num: int
    database_name: str
    current_user: str
    superuser: bool
    extensions: List[Dict[str, str]]
    runtime_settings: Dict[str, str]
    configuration_files: Dict[str, str]
    databases: List[Dict[str, Any]]
    tables_count: int
    indexes_count: int
    total_size_bytes: int
    cache_info: Dict[str, str]


class SettingsCapture:
    """Capture comprehensive PostgreSQL settings"""

    def __init__(self, connection_string: str):
        """Initialize with connection string"""
        self.connection_string = connection_string
        self.conn: Optional[psycopg.Connection] = None

    def connect(self) -> None:
        """Establish database connection"""
        self.conn = psycopg.connect(self.connection_string)

    def disconnect(self) -> None:
        """Close connection"""
        if self.conn:
            self.conn.close()

    def capture_all(self) -> PostgreSQLSettings:
        """Capture all PostgreSQL settings"""
        if not self.conn:
            self.connect()

        try:
            return PostgreSQLSettings(
                version=self._get_version(),
                server_version_num=self._get_server_version_num(),
                database_name=self._get_current_database(),
                current_user=self._get_current_user(),
                superuser=self._is_superuser(),
                extensions=self._get_extensions(),
                runtime_settings=self._get_runtime_settings(),
                configuration_files=self._get_configuration_files(),
                databases=self._get_databases(),
                tables_count=self._get_tables_count(),
                indexes_count=self._get_indexes_count(),
                total_size_bytes=self._get_total_size(),
                cache_info=self._get_cache_info(),
            )
        finally:
            self.disconnect()

    def _execute_query(
        self, query: str, params: Tuple | None = None
    ) -> List[Dict[str, Any]]:
        """Execute query and return results as list of dicts"""
        if not self.conn:
            return []
        with self.conn.cursor() as cur:
            if params is not None:
                cur.execute(query, params)
            else:
                cur.execute(query)
            if not cur.description:
                return []
            colnames = [desc[0] for desc in cur.description]
            return [dict(zip(colnames, row)) for row in cur.fetchall()]

    def _execute_scalar(self, query: str) -> Any:
        """Execute query and return single scalar value"""
        if not self.conn:
            return ""
        with self.conn.cursor() as cur:
            cur.execute(query)
            result = cur.fetchone()
            return str(result[0]) if result else ""

    def _get_version(self) -> str:
        """Get PostgreSQL version"""
        result = self._execute_scalar("SELECT version()")
        return str(result) if result else ""

    def _get_server_version_num(self) -> int:
        """Get server version number"""
        result = self._execute_scalar(
            "SELECT setting FROM pg_settings WHERE name = 'server_version_num'"
        )
        return int(result) if result else 0

    def _get_current_database(self) -> str:
        """Get current database name"""
        result = self._execute_scalar("SELECT current_database()")
        return str(result) if result else ""

    def _get_current_user(self) -> str:
        """Get current user"""
        result = self._execute_scalar("SELECT current_user")
        return str(result) if result else ""

    def _is_superuser(self) -> bool:
        """Check if current user is superuser"""
        result = self._execute_scalar(
            "SELECT usesuper FROM pg_user WHERE usename = current_user"
        )
        return bool(result) if result is not None else False

    def _get_extensions(self) -> List[Dict[str, str]]:
        """Get installed extensions"""
        results = self._execute_query(
            """
            SELECT 
                extname as name,
                extversion as version,
                extschema::regnamespace::text as schema
            FROM pg_extension
            ORDER BY extname
            """
        )
        return [dict(r) for r in results]

    def _get_runtime_settings(self) -> Dict[str, str]:
        """Get important runtime settings"""
        important_settings = [
            "max_connections",
            "shared_buffers",
            "effective_cache_size",
            "work_mem",
            "maintenance_work_mem",
            "random_page_cost",
            "effective_io_concurrency",
            "wal_buffers",
            "min_wal_size",
            "max_wal_size",
            "checkpoint_completion_target",
            "wal_compression",
            "max_worker_processes",
            "max_parallel_workers_per_gather",
            "max_parallel_workers",
            "max_parallel_maintenance_workers",
            "max_connections",
            "superuser_reserved_connections",
            "log_min_duration_statement",
            "log_statement",
            "log_connections",
            "log_disconnections",
            "shared_preload_libraries",
            "jit",
            "jit_above_cost",
            "jit_inline_above_cost",
            "jit_optimize_above_cost",
            "enable_partitionwise_join",
            "enable_partitionwise_aggregate",
            "tcp_keepalives_idle",
            "tcp_keepalives_interval",
            "tcp_keepalives_count",
            "idle_in_transaction_session_timeout",
            "statement_timeout",
            "lock_timeout",
        ]

        results = self._execute_query(
            """
            SELECT 
                name,
                setting,
                unit,
                category
            FROM pg_settings
            WHERE name = ANY(%s)
            ORDER BY category, name
            """,
            (important_settings,),
        )
        # Return as dict of name -> setting
        return {r["name"]: f"{r['setting']} {r['unit'] or ''}".strip() for r in results}

    def _get_configuration_files(self) -> Dict[str, str]:
        """Get configuration file locations"""
        results = self._execute_query(
            """
            SELECT name, setting 
            FROM pg_settings 
            WHERE name IN ('config_file', 'hba_file', 'ident_file')
            """
        )
        return {r["name"]: r["setting"] for r in results}

    def _get_databases(self) -> List[Dict[str, Any]]:
        """Get all databases info"""
        results = self._execute_query(
            """
            SELECT 
                datname as name,
                spcname as tablespace,
                pg_size_pretty(pg_database_size(datname)) as size,
                numbackends as connections
            FROM pg_database
            JOIN pg_tablespace ON pg_database.spcname = pg_tablespace.spcname
            ORDER BY pg_database_size(datname) DESC
            """
        )
        return [dict(r) for r in results]

    def _get_tables_count(self) -> int:
        """Get total tables count"""
        result = self._execute_scalar(
            (
                "SELECT count(*) FROM information_schema.tables "
                "WHERE table_schema NOT IN ('pg_catalog', 'information_schema')"
            )
        )
        return int(result) if result else 0

    def _get_indexes_count(self) -> int:
        """Get total indexes count"""
        result = self._execute_scalar(
            """
            SELECT count(*) FROM pg_indexes 
            WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
            """
        )
        return int(result) if result else 0

    def _get_total_size(self) -> int:
        """Get total database size in bytes"""
        result = self._execute_scalar("SELECT pg_database_size(current_database())")
        return int(result) if result else 0

    def _get_cache_info(self) -> Dict[str, str]:
        """Get cache hit ratio information"""
        try:
            # Index cache hit ratio
            index_hit = self._execute_scalar(
                (
                    "SELECT "
                    "CASE WHEN sum(heap_blks_read) = 0 THEN 'N/A' "
                    "ELSE round(100.0 * sum(heap_blks_hit) / "
                    "(sum(heap_blks_hit) + sum(heap_blks_read)), 2)::text "
                    "END FROM pg_statio_user_tables"
                )
            )

            # Table cache hit ratio
            table_hit = self._execute_scalar(
                (
                    "SELECT "
                    "CASE WHEN sum(idx_blks_read) = 0 THEN 'N/A' "
                    "ELSE round(100.0 * sum(idx_blks_hit) / "
                    "(sum(idx_blks_hit) + sum(idx_blks_read)), 2)::text "
                    "END FROM pg_statio_user_indexes"
                )
            )

            return {
                "index_cache_hit_ratio": f"{index_hit}%",
                "table_cache_hit_ratio": f"{table_hit}%",
            }
        except Exception as e:
            logger.warning(f"Could not get cache info: {e}")
            return {}
