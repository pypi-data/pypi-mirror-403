"""PostgreSQL real-time activity analysis for pg_stat_activity"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ActiveSessionMetrics:
    """Metrics for an active database session"""

    query_id: str  # pid as string
    pid: int
    user: str
    database: str
    application: str
    query: Optional[str]
    state: str  # active, idle, idle in transaction, etc.
    duration_ms: float  # milliseconds
    wait_event_type: Optional[str]
    wait_event: Optional[str]
    client_addr: Optional[str] = None
    client_port: Optional[int] = None
    is_blocking: bool = False
    blocking_pids: List[int] = field(default_factory=list)
    transaction_duration_ms: Optional[float] = None


@dataclass
class ActivityInsight:
    """Insight generated from activity analysis"""

    category: (
        str  # long_running, blocking, idle_in_transaction, type_distribution, info
    )
    severity: str  # critical, warning, info
    message: str
    query_ids: List[str] = field(default_factory=list)
    session_count: int = 0
    recommendation: str = ""
    impact_estimate: str = ""


@dataclass
class ActivitySnapshot:
    """Complete snapshot of current database activity"""

    timestamp: datetime
    total_sessions: int
    active_sessions: int
    idle_sessions: int
    idle_in_transaction: int
    long_running_queries: List[ActiveSessionMetrics] = field(default_factory=list)
    blocking_queries: List[ActiveSessionMetrics] = field(default_factory=list)
    idle_in_transaction_sessions: List[ActiveSessionMetrics] = field(
        default_factory=list
    )
    session_breakdown: Dict[str, int] = field(default_factory=dict)
    database_breakdown: Dict[str, int] = field(default_factory=dict)
    user_breakdown: Dict[str, int] = field(default_factory=dict)
    insights: List[ActivityInsight] = field(default_factory=list)


class PostgreSQLActivityAnalyzer:
    """Real-time PostgreSQL activity analyzer using pg_stat_activity"""

    def __init__(
        self,
        connection_obj: Any,
        long_running_threshold_ms: float = 60000,
        idle_in_transaction_threshold_ms: float = 30000,
    ):
        """Initialize activity analyzer

        Args:
            connection_obj: psycopg2 or psycopg3 connection object
            long_running_threshold_ms: Threshold for long-running queries
                (default 60s)
            idle_in_transaction_threshold_ms: Threshold for idle in transaction
                (default 30s)
        """
        self.client = connection_obj
        self.long_running_threshold_ms = long_running_threshold_ms
        self.idle_in_transaction_threshold_ms = idle_in_transaction_threshold_ms

    def get_activity_snapshot(
        self, filter_query: Optional[str] = None
    ) -> Optional[ActivitySnapshot]:
        """Get current activity snapshot from pg_stat_activity

        Args:
            filter_query: Optional WHERE clause to filter sessions

        Returns:
            ActivitySnapshot with all current activity data
        """
        if not self.client:
            logger.warning("No database connection available")
            return None

        try:
            cursor = self.client.cursor()

            # Base query with all essential pg_stat_activity columns
            base_query = """
                SELECT
                    pid,
                    usename,
                    datname,
                    application_name,
                    state,
                    query,
                    query_start,
                    state_change,
                    wait_event_type,
                    wait_event,
                    client_addr,
                    client_port,
                    backend_start,
                    xact_start
                FROM pg_stat_activity
                WHERE pid != pg_backend_pid()
            """

            if filter_query:
                base_query += f" AND {filter_query}"

            cursor.execute(base_query)
            rows = cursor.fetchall()
            cursor.close()

            sessions = []
            for row in rows:
                session = self._parse_activity_row(row)
                if session:
                    sessions.append(session)

            # Analyze the sessions
            long_running = self._identify_long_running(sessions)
            blocking = self._identify_blocking_queries(sessions)
            idle_in_tx = self._identify_idle_in_transaction(sessions)
            session_breakdown = self._get_session_breakdown(sessions)
            database_breakdown = self._get_database_breakdown(sessions)
            user_breakdown = self._get_user_breakdown(sessions)

            # Generate insights
            insights = self._generate_insights(
                sessions, long_running, blocking, idle_in_tx
            )

            snapshot = ActivitySnapshot(
                timestamp=datetime.now(timezone.utc),
                total_sessions=len(sessions),
                active_sessions=sum(1 for s in sessions if s.state == "active"),
                idle_sessions=sum(1 for s in sessions if s.state == "idle"),
                idle_in_transaction=sum(
                    1 for s in sessions if s.state == "idle in transaction"
                ),
                long_running_queries=long_running,
                blocking_queries=blocking,
                idle_in_transaction_sessions=idle_in_tx,
                session_breakdown=session_breakdown,
                database_breakdown=database_breakdown,
                user_breakdown=user_breakdown,
                insights=insights,
            )

            return snapshot

        except Exception as e:
            logger.error(f"Error getting activity snapshot: {e}")
            return None

    def _parse_activity_row(self, row: tuple) -> Optional[ActiveSessionMetrics]:
        """Parse a pg_stat_activity row into ActiveSessionMetrics

        Args:
            row: Tuple from pg_stat_activity query

        Returns:
            ActiveSessionMetrics or None if parsing fails
        """
        try:
            (
                pid,
                usename,
                datname,
                application_name,
                state,
                query,
                query_start,
                state_change,
                wait_event_type,
                wait_event,
                client_addr,
                client_port,
                backend_start,
                xact_start,
            ) = row

            # Calculate duration
            duration_ms = 0.0
            if query_start:
                from datetime import datetime as dt

                duration = dt.now(query_start.tzinfo) - query_start
                duration_ms = duration.total_seconds() * 1000

            # Calculate transaction duration
            transaction_duration_ms = None
            if xact_start:
                from datetime import datetime as dt

                tx_duration = dt.now(xact_start.tzinfo) - xact_start
                transaction_duration_ms = tx_duration.total_seconds() * 1000

            return ActiveSessionMetrics(
                query_id=str(pid),
                pid=pid,
                user=usename or "unknown",
                database=datname or "unknown",
                application=application_name or "unknown",
                query=query,
                state=state or "unknown",
                duration_ms=duration_ms,
                wait_event_type=wait_event_type,
                wait_event=wait_event,
                client_addr=str(client_addr) if client_addr else None,
                client_port=client_port,
                transaction_duration_ms=transaction_duration_ms,
            )

        except Exception as e:
            logger.error(f"Error parsing activity row: {e}")
            return None

    def _identify_long_running(
        self, sessions: List[ActiveSessionMetrics]
    ) -> List[ActiveSessionMetrics]:
        """Identify long-running active queries

        Args:
            sessions: List of active sessions

        Returns:
            List of long-running query sessions
        """
        long_running = []
        for session in sessions:
            if (
                session.state == "active"
                and session.duration_ms > self.long_running_threshold_ms
            ):
                long_running.append(session)

        return sorted(long_running, key=lambda s: s.duration_ms, reverse=True)

    def _identify_blocking_queries(
        self, sessions: List[ActiveSessionMetrics]
    ) -> List[ActiveSessionMetrics]:
        """Identify queries that are blocking other queries

        Args:
            sessions: List of active sessions

        Returns:
            List of blocking query sessions
        """
        blocking = []

        try:
            cursor = self.client.cursor()

            # Query to find blocking relationships
            blocking_query = """
                SELECT DISTINCT
                    blocked_locks.pid AS blocked_pid,
                    blocking_locks.pid AS blocking_pid
                FROM pg_catalog.pg_locks blocked_locks
                JOIN pg_catalog.pg_locks blocking_locks ON
                    blocking_locks.locktype = blocked_locks.locktype
                    AND blocking_locks.database IS NOT DISTINCT FROM
                        blocked_locks.database
                    AND blocking_locks.relation IS NOT DISTINCT FROM
                        blocked_locks.relation
                    AND blocking_locks.page IS NOT DISTINCT FROM
                        blocked_locks.page
                    AND blocking_locks.tuple IS NOT DISTINCT FROM
                        blocked_locks.tuple
                    AND blocking_locks.virtualxid IS NOT DISTINCT FROM
                        blocked_locks.virtualxid
                    AND blocking_locks.transactionid IS NOT DISTINCT FROM
                        blocked_locks.transactionid
                    AND blocking_locks.classid IS NOT DISTINCT FROM
                        blocked_locks.classid
                    AND blocking_locks.objid IS NOT DISTINCT FROM
                        blocked_locks.objid
                    AND blocking_locks.objsubid IS NOT DISTINCT FROM
                        blocked_locks.objsubid
                    AND blocking_locks.pid != blocked_locks.pid
                WHERE NOT blocked_locks.granted
            """

            cursor.execute(blocking_query)
            blocking_pairs = cursor.fetchall()
            cursor.close()

            # Map of blocking pids
            blocking_pids_set = {pair[1] for pair in blocking_pairs}
            blocked_by_map: Dict[int, List[int]] = {}
            for blocked_pid, blocking_pid in blocking_pairs:
                if blocked_pid not in blocked_by_map:
                    blocked_by_map[blocked_pid] = []
                blocked_by_map[blocked_pid].append(blocking_pid)

            # Find sessions that are blocking
            for session in sessions:
                if session.pid in blocking_pids_set:
                    blocking_pids_list = [
                        blocked_pid
                        for blocked_pid, blocking_list in blocked_by_map.items()
                        if session.pid in blocking_list
                    ]
                    session.is_blocking = True
                    session.blocking_pids = blocking_pids_list
                    blocking.append(session)

        except Exception as e:
            logger.warning(f"Could not analyze blocking queries: {e}")

        return blocking

    def _identify_idle_in_transaction(
        self, sessions: List[ActiveSessionMetrics]
    ) -> List[ActiveSessionMetrics]:
        """Identify idle in transaction sessions that hold locks

        Args:
            sessions: List of active sessions

        Returns:
            List of idle in transaction sessions exceeding threshold
        """
        idle_in_tx = []
        for session in sessions:
            if session.state == "idle in transaction":
                if (
                    session.transaction_duration_ms
                    and session.transaction_duration_ms
                    > self.idle_in_transaction_threshold_ms
                ):
                    idle_in_tx.append(session)

        return sorted(
            idle_in_tx,
            key=lambda s: s.transaction_duration_ms or 0,
            reverse=True,
        )

    def _get_session_breakdown(
        self, sessions: List[ActiveSessionMetrics]
    ) -> Dict[str, int]:
        """Get breakdown of sessions by state

        Args:
            sessions: List of active sessions

        Returns:
            Dictionary with state -> count
        """
        breakdown: Dict[str, int] = {}
        for session in sessions:
            state = session.state
            breakdown[state] = breakdown.get(state, 0) + 1
        return breakdown

    def _get_database_breakdown(
        self, sessions: List[ActiveSessionMetrics]
    ) -> Dict[str, int]:
        """Get breakdown of sessions by database

        Args:
            sessions: List of active sessions

        Returns:
            Dictionary with database_name -> count
        """
        breakdown: Dict[str, int] = {}
        for session in sessions:
            db = session.database
            breakdown[db] = breakdown.get(db, 0) + 1
        return breakdown

    def _get_user_breakdown(
        self, sessions: List[ActiveSessionMetrics]
    ) -> Dict[str, int]:
        """Get breakdown of sessions by user

        Args:
            sessions: List of active sessions

        Returns:
            Dictionary with username -> count
        """
        breakdown: Dict[str, int] = {}
        for session in sessions:
            user = session.user
            breakdown[user] = breakdown.get(user, 0) + 1
        return breakdown

    def _generate_insights(
        self,
        sessions: List[ActiveSessionMetrics],
        long_running: List[ActiveSessionMetrics],
        blocking: List[ActiveSessionMetrics],
        idle_in_tx: List[ActiveSessionMetrics],
    ) -> List[ActivityInsight]:
        """Generate insights from activity data

        Args:
            sessions: All sessions
            long_running: Long-running query sessions
            blocking: Blocking query sessions
            idle_in_tx: Idle in transaction sessions

        Returns:
            List of ActivityInsight objects
        """
        insights = []

        # Long-running query insight
        if long_running:
            insights.append(
                ActivityInsight(
                    category="long_running",
                    severity="warning" if len(long_running) > 1 else "info",
                    message=f"Found {len(long_running)} long-running query session(s)",
                    query_ids=[s.query_id for s in long_running],
                    session_count=len(long_running),
                    recommendation=(
                        "Investigate queries running longer than "
                        f"{self.long_running_threshold_ms / 1000:.0f}s. "
                        "Consider optimizing or terminating if unnecessary."
                    ),
                    impact_estimate=(
                        "Medium - Long-running queries can lock resources and "
                        "slow down other operations"
                    ),
                )
            )

        # Blocking queries insight
        if blocking:
            insights.append(
                ActivityInsight(
                    category="blocking",
                    severity="critical",
                    message=f"Found {len(blocking)} blocking query session(s)",
                    query_ids=[s.query_id for s in blocking],
                    session_count=len(blocking),
                    recommendation=(
                        "Blocking queries are holding locks preventing other "
                        "transactions from proceeding. Review and optimize "
                        "immediately."
                    ),
                    impact_estimate=(
                        "High - Blocking queries cause transaction bottlenecks "
                        "and application hangs"
                    ),
                )
            )

        # Idle in transaction insight
        if idle_in_tx:
            insights.append(
                ActivityInsight(
                    category="idle_in_transaction",
                    severity="warning",
                    message=(
                        f"Found {len(idle_in_tx)} idle in transaction session(s) "
                        "holding locks"
                    ),
                    query_ids=[s.query_id for s in idle_in_tx],
                    session_count=len(idle_in_tx),
                    recommendation=(
                        "Sessions idle in transaction should be committed or "
                        "rolled back promptly to release locks. Consider "
                        "setting idle_in_transaction_session_timeout."
                    ),
                    impact_estimate=(
                        "Medium - Idle transactions can block autovacuum and "
                        "lock resources"
                    ),
                )
            )

        # Session distribution insight
        total_idle = sum(
            1 for s in sessions if s.state in ["idle", "idle in transaction"]
        )
        if total_idle > len(sessions) * 0.7:
            insights.append(
                ActivityInsight(
                    category="info",
                    severity="info",
                    message=f"Most sessions are idle ({total_idle}/{len(sessions)})",
                    session_count=total_idle,
                    recommendation=(
                        "Normal for applications with connection pooling. "
                        "Monitor for idle sessions that should be closed."
                    ),
                    impact_estimate="Low",
                )
            )

        return insights
