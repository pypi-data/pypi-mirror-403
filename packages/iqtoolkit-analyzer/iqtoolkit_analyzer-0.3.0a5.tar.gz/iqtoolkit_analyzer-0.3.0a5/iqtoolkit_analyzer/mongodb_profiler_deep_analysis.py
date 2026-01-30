"""
MongoDB Profiler Deep Analysis Module using mongo-toolkit

Provides deep profiler analysis using mongo-toolkit's specialized tools:
- Profiler record deep inspection
- Advanced execution plan analysis
- Index usage optimization
- Aggregation pipeline stage analysis
"""

import logging
from dataclasses import dataclass
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

# Try to import mongo-toolkit components
try:
    from mongo_toolkit.execution_plan import ExecutionPlanAnalyzer
    from mongo_toolkit.index_advisor import IndexAdvisor
    from mongo_toolkit.profiler import ProfilerAnalyzer

    MONGO_TOOLKIT_AVAILABLE = True
except ImportError:
    MONGO_TOOLKIT_AVAILABLE = False
    ProfilerAnalyzer = None
    ExecutionPlanAnalyzer = None
    IndexAdvisor = None

logger = logging.getLogger(__name__)


@dataclass
class ProfilerInsight:
    """Detailed insight from deep profiler analysis."""

    category: str  # e.g., "execution_efficiency", "index_usage", "aggregation_stage"
    severity: str  # "Critical", "High", "Medium", "Low", "Info"
    message: str
    affected_fields: Optional[List[str]] = None
    recommendation: Optional[str] = None
    impact_estimate: Optional[str] = None


@dataclass
class ExecutionPlanMetrics:
    """Metrics extracted from MongoDB execution plan."""

    # Scan metrics
    documents_scanned: int = 0
    documents_returned: int = 0
    scan_efficiency: float = 0.0  # 0-1, higher is better

    # Index metrics
    index_used: Optional[str] = None
    index_scan_efficiency: float = 0.0  # 0-1, higher is better

    # Stage metrics
    stage_count: int = 0
    blocking_stages: Optional[List[str]] = None  # Stages that block pipeline progress

    # Performance metrics
    execution_time_ms: float = 0.0

    def __post_init__(self) -> None:
        """Initialize defaults."""
        if self.blocking_stages is None:
            self.blocking_stages = []


class MongoDBProfilerDeepAnalyzer:
    """
    Deep analysis of MongoDB profiler data using mongo-toolkit.

    Provides advanced analysis beyond basic slow query detection:
    - Execution plan optimization analysis
    - Index usage recommendations
    - Aggregation pipeline stage analysis
    - Profiler metric trends
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

        if not MONGO_TOOLKIT_AVAILABLE:
            logger.warning(
                "mongo-toolkit not available. Some advanced profiler analysis features "
                "will be disabled. Install with: pip install mongo-toolkit"
            )

        self.connection_string = connection_string
        self.thresholds = thresholds
        self.client: Optional[MongoClient] = None

        # Initialize toolkit components if available
        self.profiler_analyzer: Optional[ProfilerAnalyzer] = None
        self.execution_plan_analyzer: Optional[ExecutionPlanAnalyzer] = None
        self.index_advisor: Optional[IndexAdvisor] = None

    def connect(self) -> bool:
        """Establish connection to MongoDB."""
        try:
            self.client = MongoClient(
                self.connection_string, serverSelectionTimeoutMS=5000
            )
            self.client.admin.command("ping")
            logger.info("Successfully connected to MongoDB for deep profiler analysis")

            # Initialize toolkit analyzers if available
            if MONGO_TOOLKIT_AVAILABLE:
                self._initialize_toolkit_analyzers()

            return True
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False

    def _initialize_toolkit_analyzers(self) -> None:
        """Initialize mongo-toolkit analyzer components."""
        try:
            if self.client:
                self.profiler_analyzer = ProfilerAnalyzer(self.client)
                self.execution_plan_analyzer = ExecutionPlanAnalyzer(self.client)
                self.index_advisor = IndexAdvisor(self.client)
                logger.debug("Initialized mongo-toolkit analyzers")
        except Exception as e:
            logger.warning(f"Failed to initialize toolkit analyzers: {e}")

    def analyze_profiler_record_deep(
        self,
        record: Dict[str, Any],
        database_name: str,
    ) -> List[ProfilerInsight]:
        """
        Perform deep analysis on a profiler record.

        Args:
            record: Profile record from system.profile
            database_name: Database name for context

        Returns:
            List of ProfilerInsight objects
        """
        insights: List[ProfilerInsight] = []

        # Analyze execution efficiency
        insights.extend(self._analyze_execution_efficiency(record))

        # Analyze index usage
        insights.extend(self._analyze_index_usage(record, database_name))

        # Analyze aggregation pipeline (if applicable)
        if "pipeline" in record.get("command", {}):
            insights.extend(self._analyze_aggregation_pipeline(record))

        # Use toolkit if available
        if self.profiler_analyzer:
            try:
                toolkit_insights = self._get_toolkit_insights(record, database_name)
                insights.extend(toolkit_insights)
            except Exception as e:
                logger.debug(f"Toolkit analysis failed: {e}")

        return insights

    def _analyze_execution_efficiency(
        self, record: Dict[str, Any]
    ) -> List[ProfilerInsight]:
        """Analyze query execution efficiency."""
        insights: List[ProfilerInsight] = []

        docs_examined = record.get("docsExamined", 0)
        docs_returned = record.get("docsReturned", 0)
        duration_ms = record.get("millis", 0)

        # Check for low efficiency (many documents examined vs returned)
        if docs_returned > 0:
            efficiency_ratio = docs_examined / docs_returned
            if efficiency_ratio > self.thresholds.max_examined_ratio:
                ratio_str = f"{efficiency_ratio:.1f}x"
                impact = int(efficiency_ratio / 2)
                insights.append(
                    ProfilerInsight(
                        category="execution_efficiency",
                        severity="High",
                        message=(
                            f"Low query efficiency: scanned {docs_examined} docs "
                            f"but only returned {docs_returned} ({ratio_str} ratio)"
                        ),
                        recommendation=(
                            "Add or improve indexing to reduce document scans"
                        ),
                        impact_estimate=f"Could reduce docs scanned by {impact}x",
                    )
                )

        # Check for collection scans
        plan_summary = record.get("planSummary", "")
        if docs_examined > 0 and not plan_summary.startswith("IXSCAN"):
            if plan_summary.startswith("COLLSCAN"):
                severity = "Critical" if duration_ms > 1000 else "High"
                insights.append(
                    ProfilerInsight(
                        category="execution_efficiency",
                        severity=severity,
                        message=(
                            f"Collection scan detected "
                            f"({docs_examined} docs scanned in {duration_ms}ms)"
                        ),
                        recommendation=("Create an index on the query filter fields"),
                        impact_estimate=(
                            "Creating an index could reduce execution time "
                            "significantly"
                        ),
                    )
                )

        return insights

    def _analyze_index_usage(
        self, record: Dict[str, Any], database_name: str
    ) -> List[ProfilerInsight]:
        """Analyze index usage patterns."""
        insights: List[ProfilerInsight] = []

        plan_summary = record.get("planSummary", "")
        keys_examined = record.get("keysExamined", 0)
        docs_returned = record.get("docsReturned", 0)

        # Analyze plan summary for index details
        if "IXSCAN" in plan_summary:
            # Extract index name if available
            if keys_examined > docs_returned * 10:
                insights.append(
                    ProfilerInsight(
                        category="index_usage",
                        severity="Medium",
                        message=(
                            f"Index inefficiency detected: {keys_examined} keys "
                            f"examined for {docs_returned} docs returned"
                        ),
                        recommendation=(
                            "Consider creating a more selective index with "
                            "additional fields"
                        ),
                    )
                )

        elif "COLLSCAN" in plan_summary:
            # Collection scan - try to recommend an index
            command = record.get("command", {})
            filter_fields = (
                list(command.get("filter", {}).keys()) if "filter" in command else []
            )

            if filter_fields:
                fields_str = ", ".join(filter_fields[:3])
                insights.append(
                    ProfilerInsight(
                        category="index_usage",
                        severity="High",
                        message=f"No index used for query filter on {filter_fields}",
                        recommendation=f"Create index on {fields_str}",
                        impact_estimate=(
                            "Index creation could provide 10-100x performance "
                            "improvement"
                        ),
                    )
                )

        return insights

    def _analyze_aggregation_pipeline(
        self, record: Dict[str, Any]
    ) -> List[ProfilerInsight]:
        """Analyze aggregation pipeline efficiency."""
        insights: List[ProfilerInsight] = []

        command = record.get("command", {})
        pipeline = command.get("pipeline", [])

        if not pipeline:
            return insights

        # Check for $match early in pipeline
        first_stage_type = list(pipeline[0].keys())[0] if pipeline else None
        if first_stage_type != "$match":
            insights.append(
                ProfilerInsight(
                    category="aggregation_stage",
                    severity="Medium",
                    message="$match stage should be first to filter early",
                    recommendation=("Move $match to the beginning of the pipeline"),
                    impact_estimate=(
                        "Could reduce documents processed by subsequent stages"
                    ),
                )
            )

        # Check for blocking stages
        blocking_stages = ["$group", "$sort", "$lookup"]
        stage_names = [list(stage.keys())[0] for stage in pipeline]

        for i, stage_name in enumerate(stage_names):
            if stage_name in blocking_stages and i > 0:
                # Check if $match comes before
                if "$match" not in stage_names[:i]:
                    insights.append(
                        ProfilerInsight(
                            category="aggregation_stage",
                            severity="High",
                            message=(
                                f"Blocking stage {stage_name} without prior filtering"
                            ),
                            recommendation=("Add $match stage before blocking stages"),
                            impact_estimate=(
                                "Could significantly improve pipeline performance"
                            ),
                        )
                    )

        # Check for unnecessary $lookup stages
        for stage in pipeline:
            if "$lookup" in stage:
                insights.append(
                    ProfilerInsight(
                        category="aggregation_stage",
                        severity="Low",
                        message="$lookup used in pipeline - verify necessity",
                        recommendation=(
                            "Ensure $lookup is justified; consider denormalization"
                        ),
                    )
                )

        return insights

    def _get_toolkit_insights(
        self, record: Dict[str, Any], database_name: str
    ) -> List[ProfilerInsight]:
        """Get insights from mongo-toolkit analyzers."""
        insights: List[ProfilerInsight] = []

        if not self.profiler_analyzer:
            return insights

        try:
            # Use mongo-toolkit's profiler analyzer
            # This is a placeholder for actual toolkit integration
            # Will be enhanced when mongo-toolkit API is finalized

            # Example: extract metrics using toolkit
            # metrics = self.profiler_analyzer.analyze(record)
            # insights.extend(self._convert_metrics_to_insights(metrics))

            pass
        except Exception as e:
            logger.debug(f"Toolkit insights failed: {e}")

        return insights

    def get_execution_plan_metrics(
        self,
        database_name: str,
        collection_name: str,
        query: Dict[str, Any],
    ) -> Optional[ExecutionPlanMetrics]:
        """
        Get execution plan metrics for a query using explain.

        Args:
            database_name: Database name
            collection_name: Collection name
            query: Query document

        Returns:
            ExecutionPlanMetrics or None if analysis fails
        """
        if not self.client:
            return None

        try:
            db = self.client[database_name]
            collection = db[collection_name]

            # Get execution plan
            explain_result = collection.aggregate(
                [{"$match": query}, {"$limit": 1}], explain=True
            )

            metrics = self._extract_metrics_from_explain(explain_result)
            return metrics

        except Exception as e:
            logger.debug(f"Failed to get execution plan metrics: {e}")
            return None

    def _extract_metrics_from_explain(
        self, explain_result: Dict[str, Any]
    ) -> ExecutionPlanMetrics:
        """Extract metrics from MongoDB explain output."""
        metrics = ExecutionPlanMetrics()

        try:
            # Extract from explain result
            execution_stats = explain_result.get("executionStats", {})

            metrics.documents_scanned = execution_stats.get("totalDocsExamined", 0)
            metrics.documents_returned = execution_stats.get("nReturned", 0)

            # Calculate scan efficiency
            if metrics.documents_scanned > 0:
                metrics.scan_efficiency = (
                    metrics.documents_returned / metrics.documents_scanned
                )

            # Extract execution time
            metrics.execution_time_ms = execution_stats.get("executionTimeMillis", 0)

            # Check for index usage
            win_stage = execution_stats.get("winningPlan", {})
            if "stage" in win_stage:
                stage = win_stage["stage"]
                metrics.stage_count += 1

                if stage == "IXSCAN":
                    metrics.index_used = win_stage.get("indexName", "unknown")
                    metrics.index_scan_efficiency = metrics.scan_efficiency

        except Exception as e:
            logger.debug(f"Failed to extract metrics: {e}")

        return metrics

    def disconnect(self) -> None:
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
