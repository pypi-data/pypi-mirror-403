"""Wrapper for pgtools SQL and bash scripts"""

import logging
import os
import subprocess
from importlib.resources import files
from typing import Any, Dict, List, Optional

import psycopg

logger = logging.getLogger(__name__)


class PgToolsScriptLoader:
    """Load pgtools SQL and bash scripts from the package"""

    @staticmethod
    def load_sql_script(script_name: str) -> str:
        """Load SQL script from pgtools package

        Args:
            script_name: Script name without .sql extension

        Returns:
            SQL script content
        """
        try:
            script_path = files("pgtools").joinpath("scripts", f"{script_name}.sql")
            content = script_path.read_text()
            logger.debug(f"Loaded SQL script: {script_name}")
            return content
        except Exception as e:
            logger.error(f"Failed to load SQL script {script_name}: {e}")
            raise

    @staticmethod
    def load_bash_script(script_name: str) -> str:
        """Load bash script from pgtools package

        Args:
            script_name: Script name without .sh extension

        Returns:
            Bash script content
        """
        try:
            script_path = files("pgtools").joinpath("scripts", f"{script_name}.sh")
            content = script_path.read_text()
            logger.debug(f"Loaded bash script: {script_name}")
            return content
        except Exception as e:
            logger.error(f"Failed to load bash script {script_name}: {e}")
            raise

    @staticmethod
    def list_available_scripts() -> Dict[str, List[str]]:
        """List all available pgtools scripts"""
        try:
            scripts_dir = files("pgtools").joinpath("scripts")
            sql_scripts = []
            bash_scripts = []

            for item in scripts_dir.iterdir():
                if item.name.endswith(".sql"):
                    sql_scripts.append(item.name[:-4])
                elif item.name.endswith(".sh"):
                    bash_scripts.append(item.name[:-3])

            return {
                "sql": sorted(sql_scripts),
                "bash": sorted(bash_scripts),
            }
        except Exception as e:
            logger.warning(f"Could not list pgtools scripts: {e}")
            return {"sql": [], "bash": []}


class PgToolsWrapper:
    """Execute pgtools scripts against PostgreSQL database"""

    def __init__(self, connection_string: str):
        """Initialize wrapper with database connection

        Args:
            connection_string: PostgreSQL connection string
        """
        self.connection_string = connection_string
        self.conn: Optional[psycopg.Connection] = None
        self.script_loader = PgToolsScriptLoader()

    def connect(self) -> None:
        """Establish connection to PostgreSQL"""
        try:
            self.conn = psycopg.connect(self.connection_string)
            logger.info("Connected to PostgreSQL database")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def disconnect(self) -> None:
        """Close connection to PostgreSQL"""
        if self.conn:
            self.conn.close()
            logger.info("Disconnected from PostgreSQL database")

    def execute_sql_script(self, script_name: str) -> List[Dict[str, Any]]:
        """Execute SQL script and return results

        Args:
            script_name: Name of script without .sql extension

        Returns:
            List of result rows as dicts
        """
        if not self.conn:
            self.connect()

        if not self.conn:
            raise RuntimeError("Failed to establish database connection")

        try:
            sql = self.script_loader.load_sql_script(script_name)
            logger.debug(f"Executing SQL script: {script_name}")

            with self.conn.cursor() as cur:
                cur.execute(sql)

                # Check if query returned results
                if cur.description:
                    colnames = [desc[0] for desc in cur.description]
                    results = [dict(zip(colnames, row)) for row in cur.fetchall()]
                    logger.info(f"Script {script_name} returned {len(results)} rows")
                    return results
                else:
                    logger.info(f"Script {script_name} executed (no results)")
                    return []

        except Exception as e:
            logger.error(f"Error executing SQL script {script_name}: {e}")
            raise

    def execute_bash_script(
        self, script_name: str, env: Optional[Dict[str, str]] = None
    ) -> str:
        """Execute bash script locally

        Args:
            script_name: Name of script without .sh extension
            env: Optional environment variables

        Returns:
            Script output
        """
        try:
            script = self.script_loader.load_bash_script(script_name)
            logger.debug(f"Executing bash script: {script_name}")

            result = subprocess.run(
                ["bash", "-c", script],
                capture_output=True,
                text=True,
                env={**os.environ, **(env or {})},
                timeout=300,  # 5 minute timeout
            )

            if result.returncode != 0:
                logger.error(f"Bash script {script_name} failed: {result.stderr}")
                raise RuntimeError(f"Script failed: {result.stderr}")

            logger.info(f"Bash script {script_name} executed successfully")
            return str(result.stdout)

        except subprocess.TimeoutExpired:
            logger.error(f"Bash script {script_name} timed out")
            raise
        except Exception as e:
            logger.error(f"Error executing bash script {script_name}: {e}")
            raise

    # Convenience methods for common pgtools scripts

    def get_slow_queries(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get slow queries using pg_stat_statements script

        Args:
            limit: Maximum number of queries to return

        Returns:
            List of slow queries with metrics
        """
        try:
            results = self.execute_sql_script("pg_stat_statements")
            return results[:limit] if results else []
        except Exception as e:
            logger.error(f"Failed to get slow queries: {e}")
            return []

    def get_table_stats(self) -> List[Dict[str, Any]]:
        """Get table statistics using pg_stat_user_tables script

        Returns:
            List of table statistics
        """
        try:
            return self.execute_sql_script("pg_stat_user_tables")
        except Exception as e:
            logger.error(f"Failed to get table stats: {e}")
            return []

    def get_index_stats(self) -> List[Dict[str, Any]]:
        """Get index statistics using pg_stat_user_indexes script

        Returns:
            List of index statistics
        """
        try:
            return self.execute_sql_script("pg_stat_user_indexes")
        except Exception as e:
            logger.error(f"Failed to get index stats: {e}")
            return []

    def get_locks(self) -> List[Dict[str, Any]]:
        """Get current locks using pg_locks script

        Returns:
            List of active locks
        """
        try:
            return self.execute_sql_script("pg_locks")
        except Exception as e:
            logger.error(f"Failed to get locks: {e}")
            return []

    def get_vacuum_stats(self) -> List[Dict[str, Any]]:
        """Get vacuum statistics using vacuum_stats script

        Returns:
            List of vacuum statistics
        """
        try:
            return self.execute_sql_script("vacuum_stats")
        except Exception as e:
            logger.error(f"Failed to get vacuum stats: {e}")
            return []

    def get_cache_info(self) -> List[Dict[str, Any]]:
        """Get cache hit ratios using cache_info script

        Returns:
            List of cache statistics
        """
        try:
            return self.execute_sql_script("cache_info")
        except Exception as e:
            logger.error(f"Failed to get cache info: {e}")
            return []

    def get_connections(self) -> List[Dict[str, Any]]:
        """Get active connections using connections script

        Returns:
            List of active connections
        """
        try:
            return self.execute_sql_script("connections")
        except Exception as e:
            logger.error(f"Failed to get connections: {e}")
            return []

    def list_scripts(self) -> Dict[str, List[str]]:
        """List all available pgtools scripts

        Returns:
            Dict with 'sql' and 'bash' keys containing available scripts
        """
        return self.script_loader.list_available_scripts()
