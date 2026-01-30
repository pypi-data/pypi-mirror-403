"""
MongoDB currentOp Analysis Module for Real-Time Operation Monitoring

Provides analysis of currently running MongoDB operations via the currentOp command:
- Long-running operation detection
- Blocking operation identification
- Lock contention analysis
- Operation type distribution
- Client connection analysis
- Per-database operation metrics
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from .mongodb_config import MongoDBThresholdConfig

if TYPE_CHECKING:
    from pymongo import MongoClient
else:
    MongoClient = None

try:
    from pymongo import MongoClient

    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class CurrentOpMetrics:
    """Metrics extracted from a single currentOp operation."""

    operation_id: str
    operation_type: str  # "find", "update", "insert", "delete", "aggregate"
    namespace: str  # "database.collection"
    query: Optional[Dict[str, Any]] = None
    duration_ms: int = 0
    client_ip: Optional[str] = None
    client_port: Optional[int] = None
    locks_held: Optional[Dict[str, str]] = None  # lock_type -> lock_state
    wait_for_lock: bool = False
    plan_summary: Optional[str] = None
    numYield: int = 0  # Number of times operation yielded


@dataclass
class OperationInsight:
    """Insight from currentOp analysis."""

    category: str  # "long_running", "blocking", "lock_contention", "type_distribution"
    severity: str  # "Critical", "High", "Medium", "Low", "Info"
    message: str
    operation_ids: Optional[List[str]] = None
    recommendation: Optional[str] = None
    impact_estimate: Optional[str] = None


@dataclass
class CurrentOpSnapshot:
    """Complete snapshot of current operations at a point in time."""

    timestamp: datetime
    total_operations: int
    long_running_ops: List[CurrentOpMetrics]
    blocking_ops: List[CurrentOpMetrics]
    lock_contentions: List[OperationInsight]
    operation_breakdown: Dict[str, int]  # operation_type -> count
    database_breakdown: Dict[str, int]  # database -> count
    insights: List[OperationInsight]


class MongoDBCurrentOpAnalyzer:
    """
    Analyzer for MongoDB currentOp command output.

    Monitors real-time operations and detects:
    - Long-running operations (configurable threshold)
    - Blocking operations (waiting for locks)
    - Lock contention patterns
    - Operation type distribution
    - Per-database operation metrics
    """

    def __init__(
        self,
        connection_string: str,
        thresholds: MongoDBThresholdConfig,
    ):
        if not PYMONGO_AVAILABLE:
            raise ImportError(
                "pymongo is required for MongoDB integration. "
                "Install with: pip install pymongo"
            )

        self.connection_string = connection_string
        self.thresholds = thresholds
        self.client: Optional[MongoClient] = None

        # Configuration
        self.long_running_threshold_ms = 30000  # 30 seconds by default
        self.lock_wait_threshold_ms = 5000  # 5 seconds

    def connect(self) -> bool:
        """Establish connection to MongoDB."""
        try:
            self.client = MongoClient(
                self.connection_string, serverSelectionTimeoutMS=5000
            )
            self.client.admin.command("ping")
            logger.info("Successfully connected to MongoDB for currentOp analysis")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False

    def disconnect(self) -> None:
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")

    def get_current_ops_snapshot(
        self,
        filter_query: Optional[Dict[str, Any]] = None,
    ) -> Optional[CurrentOpSnapshot]:
        """
        Get a complete snapshot of current operations.

        Args:
            filter_query: Optional filter for the currentOp command.

        Returns:
            CurrentOpSnapshot with analyzed operations, or None if connection fails.
        """
        if not self.client:
            logger.warning("Not connected to MongoDB")
            return None

        try:
            # Execute currentOp with optional filter
            admin_db = self.client.admin
            if filter_query:
                current_ops = list(admin_db.command("currentOp", filter_query))
            else:
                current_ops = list(admin_db.command("currentOp", True))

            # Extract inprog operations
            ops = [op for op in current_ops if "inprog" in op]
            if ops:
                inprog_list = ops[0]["inprog"]
            else:
                inprog_list = []

            # Parse operations
            parsed_ops: List[CurrentOpMetrics] = []
            for op in inprog_list:
                parsed_op = self._parse_current_op(op)
                if parsed_op:
                    parsed_ops.append(parsed_op)

            # Analyze operations
            long_running = self._identify_long_running(parsed_ops)
            blocking = self._identify_blocking_ops(parsed_ops)
            lock_contentions = self._analyze_lock_contention(parsed_ops)
            op_breakdown = self._get_operation_breakdown(parsed_ops)
            db_breakdown = self._get_database_breakdown(parsed_ops)

            # Generate insights
            insights = self._generate_insights(
                long_running, blocking, lock_contentions, op_breakdown
            )

            return CurrentOpSnapshot(
                timestamp=datetime.utcnow(),
                total_operations=len(parsed_ops),
                long_running_ops=long_running,
                blocking_ops=blocking,
                lock_contentions=lock_contentions,
                operation_breakdown=op_breakdown,
                database_breakdown=db_breakdown,
                insights=insights,
            )

        except Exception as e:
            logger.error(f"Failed to get currentOp snapshot: {e}")
            return None

    def _parse_current_op(self, op: Dict[str, Any]) -> Optional[CurrentOpMetrics]:
        """Parse a raw currentOp entry into CurrentOpMetrics."""
        try:
            # Extract basic info
            op_id = str(op.get("opid", "unknown"))
            op_type = op.get("op", "unknown")
            namespace = op.get("ns", "unknown")
            duration_ms = int(op.get("secs_running", 0) * 1000)
            numYield = int(op.get("numYield", 0))

            # Extract client info
            client_info = op.get("client", "")
            client_ip = None
            client_port = None
            if client_info and ":" in str(client_info):
                try:
                    parts = str(client_info).rsplit(":", 1)
                    client_ip = parts[0]
                    client_port = int(parts[1])
                except (ValueError, IndexError) as e:
                    # Log malformed client info but continue
                    # (client_ip and client_port remain None)
                    logger.debug(f"Failed to parse client info '{client_info}': {e}")

            # Extract query/command
            query = None
            if "command" in op:
                query = op.get("command")
            elif "query" in op:
                query = op.get("query")

            # Extract locks
            locks_held = op.get("locks", {})

            # Wait for lock flag
            wait_for_lock = bool(op.get("waitingForLock", False))

            # Plan summary
            plan_summary = op.get("planSummary")

            return CurrentOpMetrics(
                operation_id=op_id,
                operation_type=op_type,
                namespace=namespace,
                query=query,
                duration_ms=duration_ms,
                client_ip=client_ip,
                client_port=client_port,
                locks_held=locks_held,
                wait_for_lock=wait_for_lock,
                plan_summary=plan_summary,
                numYield=numYield,
            )
        except Exception as e:
            logger.warning(f"Failed to parse currentOp entry: {e}")
            return None

    def _identify_long_running(
        self, ops: List[CurrentOpMetrics]
    ) -> List[CurrentOpMetrics]:
        """Identify operations that have been running longer than threshold."""
        return [
            op
            for op in ops
            if op.duration_ms > self.long_running_threshold_ms
            and op.operation_type not in ("none", "noop")
        ]

    def _identify_blocking_ops(
        self, ops: List[CurrentOpMetrics]
    ) -> List[CurrentOpMetrics]:
        """Identify operations waiting for locks."""
        return [op for op in ops if op.wait_for_lock]

    def _analyze_lock_contention(
        self, ops: List[CurrentOpMetrics]
    ) -> List[OperationInsight]:
        """Analyze lock contention patterns."""
        insights: List[OperationInsight] = []

        # Count operations by lock type
        lock_holders: Dict[str, List[str]] = {}
        lock_waiters: Dict[str, List[str]] = {}

        for op in ops:
            if op.locks_held:
                for lock_type, lock_state in op.locks_held.items():
                    if lock_type not in lock_holders:
                        lock_holders[lock_type] = []
                    lock_holders[lock_type].append(op.operation_id)

            if op.wait_for_lock:
                # Try to identify what lock is being waited for
                if op.locks_held:
                    for lock_type in op.locks_held:
                        if lock_type not in lock_waiters:
                            lock_waiters[lock_type] = []
                        lock_waiters[lock_type].append(op.operation_id)

        # Generate insights for contention
        if lock_waiters:
            for lock_type, waiting_ops in lock_waiters.items():
                if len(waiting_ops) > 0:
                    insights.append(
                        OperationInsight(
                            category="lock_contention",
                            severity="High",
                            message=(
                                f"Lock contention detected on {lock_type} lock "
                                f"({len(waiting_ops)} operations waiting)"
                            ),
                            operation_ids=waiting_ops,
                            recommendation=(
                                "Review long-running operations and optimize "
                                "transaction scope to reduce lock hold time"
                            ),
                            impact_estimate=(
                                f"Could improve throughput by reducing "
                                f"lock wait times for {len(waiting_ops)} operations"
                            ),
                        )
                    )

        return insights

    def _get_operation_breakdown(self, ops: List[CurrentOpMetrics]) -> Dict[str, int]:
        """Get count of operations by type."""
        breakdown: Dict[str, int] = {}
        for op in ops:
            op_type = op.operation_type
            breakdown[op_type] = breakdown.get(op_type, 0) + 1
        return breakdown

    def _get_database_breakdown(self, ops: List[CurrentOpMetrics]) -> Dict[str, int]:
        """Get count of operations by database."""
        breakdown: Dict[str, int] = {}
        for op in ops:
            # Extract database from namespace (format: "database.collection")
            if "." in op.namespace:
                db = op.namespace.split(".")[0]
            else:
                db = op.namespace

            breakdown[db] = breakdown.get(db, 0) + 1
        return breakdown

    def _generate_insights(
        self,
        long_running: List[CurrentOpMetrics],
        blocking: List[CurrentOpMetrics],
        lock_contentions: List[OperationInsight],
        op_breakdown: Dict[str, int],
    ) -> List[OperationInsight]:
        """Generate insights from current operations."""
        insights: List[OperationInsight] = []

        # Long-running operations insight
        if long_running:
            long_running_ids = [op.operation_id for op in long_running]
            avg_duration = sum(op.duration_ms for op in long_running) / len(
                long_running
            )
            insights.append(
                OperationInsight(
                    category="long_running",
                    severity="High" if len(long_running) > 2 else "Medium",
                    message=(
                        f"Found {len(long_running)} long-running operations "
                        f"(avg duration: {avg_duration:.0f}ms)"
                    ),
                    operation_ids=long_running_ids,
                    recommendation=(
                        "Review long-running queries; consider optimizing or "
                        "adding indexes. Check client timeout settings."
                    ),
                    impact_estimate=(
                        f"Optimizing {len(long_running)} operations could free up "
                        "resources and improve overall throughput"
                    ),
                )
            )

        # Blocking operations insight
        if blocking:
            blocking_ids = [op.operation_id for op in blocking]
            insights.append(
                OperationInsight(
                    category="blocking",
                    severity="High",
                    message=f"{len(blocking)} operations waiting for locks",
                    operation_ids=blocking_ids,
                    recommendation=(
                        "Reduce lock contention by optimizing transaction scope; "
                        "consider sharding for better concurrency"
                    ),
                    impact_estimate=(
                        f"Could improve latency for {len(blocking)} operations "
                        "by reducing lock wait times"
                    ),
                )
            )

        # Operation type distribution insight
        if op_breakdown:
            total_ops = sum(op_breakdown.values())
            insights.append(
                OperationInsight(
                    category="type_distribution",
                    severity="Info",
                    message=(
                        "Operation distribution: "
                        + ", ".join(
                            f"{count} {op_type}"
                            for op_type, count in sorted(
                                op_breakdown.items(), key=lambda x: x[1], reverse=True
                            )
                        )
                    ),
                    recommendation=None,
                    impact_estimate=f"Total operations monitored: {total_ops}",
                )
            )

        # Include lock contention insights
        insights.extend(lock_contentions)

        return insights
