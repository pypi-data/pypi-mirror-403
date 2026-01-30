"""PostgreSQL analyzer using pgtools"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .pgtools_wrapper import PgToolsWrapper
from .postgresql_activity_analyzer import (
    ActivitySnapshot,
    PostgreSQLActivityAnalyzer,
)
from .settings_capture import PostgreSQLSettings, SettingsCapture

# Optional AI integration
try:
    from ..ai import GoogleAIAdapter, PostgreSQLPromptBuilder

    HAS_AI = True
except ImportError:
    HAS_AI = False
    GoogleAIAdapter = None  # type: ignore
    PostgreSQLPromptBuilder = None  # type: ignore

logger = logging.getLogger(__name__)


@dataclass
class AnalysisRecommendation:
    """A single analysis recommendation"""

    severity: str  # "critical", "warning", "info"
    category: str  # "performance", "maintenance", "security", etc.
    title: str
    description: str
    suggestion: str
    metric: Optional[str] = None
    current_value: Optional[str] = None
    recommended_value: Optional[str] = None
    threshold: Optional[str] = None


@dataclass
class PostgreSQLAnalysisResult:
    """Complete analysis result from pgtools"""

    settings: PostgreSQLSettings
    slow_queries: List[Dict[str, Any]] = field(default_factory=list)
    table_stats: List[Dict[str, Any]] = field(default_factory=list)
    index_stats: List[Dict[str, Any]] = field(default_factory=list)
    locks: List[Dict[str, Any]] = field(default_factory=list)
    vacuum_stats: List[Dict[str, Any]] = field(default_factory=list)
    cache_info: List[Dict[str, Any]] = field(default_factory=list)
    connections: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[AnalysisRecommendation] = field(default_factory=list)
    activity_snapshot: Optional[ActivitySnapshot] = None
    issues_found: int = 0


class PostgreSQLAnalyzer:
    """Comprehensive PostgreSQL analyzer using pgtools"""

    def __init__(
        self,
        connection_string: str,
        ai_adapter: Optional[Any] = None,
        use_ai: bool = False,
    ):
        """Initialize analyzer

        Args:
            connection_string: PostgreSQL connection string
            ai_adapter: Optional Google AI adapter for recommendations
            use_ai: Whether to use AI for enhanced recommendations
        """
        self.connection_string = connection_string
        self.wrapper = PgToolsWrapper(connection_string)
        self.settings_capture = SettingsCapture(connection_string)
        self.activity_analyzer: Optional[PostgreSQLActivityAnalyzer] = None
        self.connection_obj: Optional[Any] = None
        self.ai_adapter = ai_adapter
        self.use_ai = use_ai

    def analyze(self) -> PostgreSQLAnalysisResult:
        """Run comprehensive analysis

        Returns:
            Complete analysis result with recommendations
        """
        logger.info("Starting PostgreSQL analysis...")

        try:
            self.wrapper.connect()

            # Assign connection object for activity analysis
            self.connection_obj = self.wrapper.conn
            if self.connection_obj:
                self.activity_analyzer = PostgreSQLActivityAnalyzer(self.connection_obj)

            # Capture settings first
            logger.info("Capturing PostgreSQL settings...")
            settings = self.settings_capture.capture_all()

            # Execute pgtools scripts
            logger.info("Executing pgtools analysis scripts...")
            slow_queries = self.wrapper.get_slow_queries(limit=50)
            table_stats = self.wrapper.get_table_stats()
            index_stats = self.wrapper.get_index_stats()
            locks = self.wrapper.get_locks()
            vacuum_stats = self.wrapper.get_vacuum_stats()
            cache_info = self.wrapper.get_cache_info()
            connections = self.wrapper.get_connections()

            # Get activity snapshot if analyzer initialized
            activity_snapshot = None
            if self.activity_analyzer:
                logger.info("Capturing real-time activity snapshot...")
                activity_snapshot = self.activity_analyzer.get_activity_snapshot()

            # Create result object
            result = PostgreSQLAnalysisResult(
                settings=settings,
                slow_queries=slow_queries,
                table_stats=table_stats,
                index_stats=index_stats,
                locks=locks,
                vacuum_stats=vacuum_stats,
                cache_info=cache_info,
                connections=connections,
                activity_snapshot=activity_snapshot,
            )

            # Generate recommendations
            logger.info("Generating recommendations...")
            recommendations = self._generate_recommendations(result)
            result.recommendations = recommendations
            result.issues_found = len(recommendations)

            logger.info(
                f"Analysis complete. Found {result.issues_found} issues/recommendations"
            )
            return result

        finally:
            self.wrapper.disconnect()

    def _generate_recommendations(
        self, result: PostgreSQLAnalysisResult
    ) -> List[AnalysisRecommendation]:
        """Generate recommendations based on analysis data

        Args:
            result: Analysis result to analyze

        Returns:
            List of recommendations
        """
        recommendations = []

        # Analyze slow queries
        recommendations.extend(self._analyze_slow_queries(result.slow_queries))

        # Analyze table statistics
        recommendations.extend(self._analyze_tables(result.table_stats))

        # Analyze indexes
        recommendations.extend(self._analyze_indexes(result.index_stats))

        # Analyze locks
        recommendations.extend(self._analyze_locks(result.locks))

        # Analyze vacuum statistics
        recommendations.extend(self._analyze_vacuum(result.vacuum_stats))

        # Analyze cache hit ratios
        recommendations.extend(self._analyze_cache(result.cache_info))

        # Analyze settings
        recommendations.extend(self._analyze_settings(result.settings))

        # Analyze connections
        recommendations.extend(self._analyze_connections(result.connections))

        return recommendations

    def _analyze_slow_queries(
        self, slow_queries: List[Dict[str, Any]]
    ) -> List[AnalysisRecommendation]:
        """Analyze slow queries"""
        recommendations: List[AnalysisRecommendation] = []

        if not slow_queries:
            return recommendations

        # Check for very slow queries
        for i, query in enumerate(slow_queries[:10]):
            mean_time = query.get("mean_time", 0)
            if mean_time > 1000:  # 1 second
                recommendations.append(
                    AnalysisRecommendation(
                        severity="warning",
                        category="performance",
                        title=f"Slow Query #{i + 1}",
                        description=f"Query takes {mean_time:.0f}ms on average",
                        suggestion="Consider optimizing query or adding indexes",
                        metric="mean_time",
                        current_value=f"{mean_time:.0f}ms",
                        recommended_value="< 100ms",
                    )
                )

        # Check for frequently called slow queries
        total_queries = sum(q.get("calls", 0) for q in slow_queries)
        for query in slow_queries[:5]:
            calls = query.get("calls", 0)
            if calls > total_queries * 0.1:  # More than 10% of all queries
                desc = (
                    f"Query called {calls} times "
                    f"({calls / total_queries * 100:.1f}% of total)"
                )
                recommendations.append(
                    AnalysisRecommendation(
                        severity="warning",
                        category="performance",
                        title="Frequently Called Slow Query",
                        description=desc,
                        suggestion="This query significantly impacts performance",
                        metric="calls",
                        current_value=str(calls),
                    )
                )

        return recommendations

    def _analyze_tables(
        self, table_stats: List[Dict[str, Any]]
    ) -> List[AnalysisRecommendation]:
        """Analyze table statistics"""
        recommendations = []

        for table in table_stats:
            tablename = table.get("tablename", "unknown")
            n_live_tup = table.get("n_live_tup", 0)
            n_dead_tup = table.get("n_dead_tup", 0)
            last_autovacuum = table.get("last_autovacuum")

            # Check for table bloat
            if n_live_tup > 0:
                dead_ratio = n_dead_tup / n_live_tup
                if dead_ratio > 0.2:  # 20% dead tuples
                    desc = f"Table has {dead_ratio * 100:.1f}% dead tuples"
                    recommendations.append(
                        AnalysisRecommendation(
                            severity="warning",
                            category="maintenance",
                            title=f"Table Bloat: {tablename}",
                            description=desc,
                            suggestion="Run VACUUM to reclaim space",
                            metric="dead_ratio",
                            current_value=f"{dead_ratio * 100:.1f}%",
                            recommended_value="< 10%",
                        )
                    )

            # Check for never vacuumed tables
            if not last_autovacuum and n_live_tup > 1000:
                recommendations.append(
                    AnalysisRecommendation(
                        severity="info",
                        category="maintenance",
                        title=f"Never Autovacuumed: {tablename}",
                        description="Table has never been automatically vacuumed",
                        suggestion=(
                            "Monitor autovacuum settings or manually vacuum this table"
                        ),
                        metric="last_autovacuum",
                        current_value="Never",
                    )
                )

        return recommendations

    def _analyze_indexes(
        self, index_stats: List[Dict[str, Any]]
    ) -> List[AnalysisRecommendation]:
        """Analyze index statistics"""
        recommendations = []

        for index in index_stats:
            indexname = index.get("indexname", "unknown")
            idx_scan = index.get("idx_scan", 0)
            # idx_tup_read is available but unused for current checks

            # Check for unused indexes
            if idx_scan == 0:
                recommendations.append(
                    AnalysisRecommendation(
                        severity="info",
                        category="performance",
                        title=f"Unused Index: {indexname}",
                        description="Index has never been scanned",
                        suggestion="Consider dropping if no longer needed",
                        metric="idx_scan",
                        current_value="0",
                    )
                )

        return recommendations

    def _analyze_locks(
        self, locks: List[Dict[str, Any]]
    ) -> List[AnalysisRecommendation]:
        """Analyze lock contention"""
        recommendations = []

        if len(locks) > 5:
            recommendations.append(
                AnalysisRecommendation(
                    severity="warning",
                    category="performance",
                    title="High Lock Contention",
                    description=f"{len(locks)} active locks detected",
                    suggestion=(
                        "Check for blocking queries and long-running transactions"
                    ),
                    metric="lock_count",
                    current_value=str(len(locks)),
                    recommended_value="< 5",
                )
            )

        return recommendations

    def _analyze_vacuum(
        self, vacuum_stats: List[Dict[str, Any]]
    ) -> List[AnalysisRecommendation]:
        """Analyze vacuum statistics"""
        recommendations = []

        for table in vacuum_stats:
            tablename = table.get("tablename", "unknown")
            last_autovacuum = table.get("last_autovacuum")

            if not last_autovacuum:
                recommendations.append(
                    AnalysisRecommendation(
                        severity="info",
                        category="maintenance",
                        title=f"Never Autovacuumed: {tablename}",
                        description="Table has never been automatically vacuumed",
                        suggestion="Check autovacuum configuration",
                        metric="last_autovacuum",
                        current_value="Never",
                    )
                )

        return recommendations

    def _analyze_cache(
        self, cache_info: List[Dict[str, Any]]
    ) -> List[AnalysisRecommendation]:
        """Analyze cache hit ratios"""
        recommendations = []

        for metric in cache_info:
            metric_name = metric.get("metric", "unknown")
            hit_ratio = metric.get("hit_ratio", 0)

            if hit_ratio < 99:  # Less than 99%
                suggestions = (
                    "Consider increasing shared_buffers or effective_cache_size"
                )
                recommendations.append(
                    AnalysisRecommendation(
                        severity="warning",
                        category="performance",
                        title=f"Low Cache Hit Ratio: {metric_name}",
                        description=f"Cache hit ratio is {hit_ratio:.1f}%",
                        suggestion=suggestions,
                        metric=metric_name,
                        current_value=f"{hit_ratio:.1f}%",
                        recommended_value="> 99%",
                    )
                )

        return recommendations

    def _analyze_settings(
        self, settings: PostgreSQLSettings
    ) -> List[AnalysisRecommendation]:
        """Analyze PostgreSQL settings"""
        recommendations: List[AnalysisRecommendation] = []

        # Check shared_buffers (typical: 25% of RAM)
        # Check max_connections
        # Check work_mem
        # etc.

        return recommendations

    def _analyze_connections(
        self, connections: List[Dict[str, Any]]
    ) -> List[AnalysisRecommendation]:
        """Analyze active connections"""
        recommendations = []

        if len(connections) > 100:
            recommendations.append(
                AnalysisRecommendation(
                    severity="info",
                    category="performance",
                    title="High Connection Count",
                    description=f"{len(connections)} active connections",
                    suggestion="Monitor connection pool and application behavior",
                    metric="active_connections",
                    current_value=str(len(connections)),
                )
            )

        return recommendations

    def get_activity_snapshot(
        self, filter_query: Optional[str] = None
    ) -> Optional[ActivitySnapshot]:
        """Get current database activity snapshot from pg_stat_activity

        Args:
            filter_query: Optional WHERE clause to filter sessions (e.g.,
                "state = 'active'")

        Returns:
            ActivitySnapshot with current activity data or None if no analyzer
            initialized
        """
        if not self.activity_analyzer:
            logger.warning("Activity analyzer not initialized")
            return None

        return self.activity_analyzer.get_activity_snapshot(filter_query)

    def get_ai_recommendations(
        self,
        result: PostgreSQLAnalysisResult,
        use_streaming: bool = False,
    ) -> Optional[str]:
        """Get AI-powered recommendations for analysis result

        Args:
            result: PostgreSQL analysis result
            use_streaming: Whether to stream response chunks

        Returns:
            AI-generated recommendations as string, or None if AI unavailable
        """
        if not HAS_AI or not self.ai_adapter or not self.use_ai:
            logger.debug("AI adapter not available or disabled")
            return None

        try:
            # Build prompt from analysis result
            prompt = PostgreSQLPromptBuilder.build_prompt(
                db_version=result.settings.version if result.settings else "unknown",
                slow_queries=result.slow_queries,
                table_stats=result.table_stats,
                locks_info=result.locks[0] if result.locks else {},
                activity_snapshot=result.activity_snapshot.__dict__
                if result.activity_snapshot
                else {},
                cache_metrics=result.cache_info[0] if result.cache_info else {},
            )

            # Send to AI
            recommendations = self.ai_adapter.analyze_postgresql(
                prompt,
                use_streaming=use_streaming,
            )
            return recommendations  # type: ignore

        except Exception as e:
            logger.error(f"AI recommendation generation failed: {e}")
            return None
