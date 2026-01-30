"""Prompt templates for database analysis with AI integration"""


class PostgreSQLPromptBuilder:
    """Build structured prompts for PostgreSQL analysis via Gemini"""

    SYSTEM_INSTRUCTION = """You are an expert PostgreSQL database performance analyst. 
Analyze the provided database metrics and activity data, then provide:
1. **Critical Issues** (immediate action required)
2. **High Priority** (performance impact)
3. **Medium Priority** (optimization opportunities)
4. **Low Priority** (nice-to-have improvements)

Be concise, actionable, and focus on practical solutions."""

    @staticmethod
    def build_prompt(
        db_version: str,
        slow_queries: list[dict],
        table_stats: list[dict],
        locks_info: dict,
        activity_snapshot: dict,
        cache_metrics: dict,
        workload_type: str = "OLTP",
    ) -> str:
        """Build PostgreSQL analysis prompt for Gemini

        Args:
            db_version: PostgreSQL version
            slow_queries: List of slow query findings
            table_stats: Table statistics
            locks_info: Lock contention data
            activity_snapshot: Current activity metrics
            cache_metrics: Cache hit ratios and buffer stats
            workload_type: Detected workload (OLTP, OLAP, batch)

        Returns:
            Formatted prompt string
        """
        prompt = f"""# PostgreSQL Database Analysis Report

## Database Environment
- **Version:** {db_version}
- **Workload Type:** {workload_type}
- **Analysis Timestamp:** {activity_snapshot.get("timestamp", "N/A")}

## Current Activity
- **Total Sessions:** {activity_snapshot.get("total_sessions", 0)}
- **Active Sessions:** {activity_snapshot.get("active_sessions", 0)}
- **Idle Sessions:** {activity_snapshot.get("idle_sessions", 0)}
- **Idle in Transaction:** {activity_snapshot.get("idle_in_transaction", 0)}

## Slow Queries
{PostgreSQLPromptBuilder._format_slow_queries(slow_queries)}

## Lock Contention
{PostgreSQLPromptBuilder._format_locks(locks_info)}

## Cache Performance
{PostgreSQLPromptBuilder._format_cache(cache_metrics)}

## Table Statistics
{PostgreSQLPromptBuilder._format_tables(table_stats)}

Please provide optimization recommendations for this PostgreSQL database."""

        return prompt

    @staticmethod
    def _format_slow_queries(queries: list[dict]) -> str:
        """Format slow query data"""
        if not queries:
            return "- No slow queries detected"
        return "\n".join(
            [
                f"- Query: {q.get('query', 'N/A')[:100]}...\n"
                f"  Duration: {q.get('duration_ms', 0)}ms\n"
                f"  Calls: {q.get('calls', 0)}"
                for q in queries[:5]
            ]
        )

    @staticmethod
    def _format_locks(locks: dict) -> str:
        """Format lock contention data"""
        if not locks:
            return "- No lock contention detected"
        blocked = locks.get("blocked_count", 0)
        blocking = locks.get("blocking_count", 0)
        return f"- Blocked Sessions: {blocked}\n- Blocking Sessions: {blocking}"

    @staticmethod
    def _format_cache(metrics: dict) -> str:
        """Format cache metrics"""
        index_ratio = metrics.get("index_hit_ratio", 0)
        cache_ratio = metrics.get("cache_hit_ratio", 0)
        ratio_str = (
            f"- Index Hit Ratio: {index_ratio:.2f}%\n"
            f"- Cache Hit Ratio: {cache_ratio:.2f}%"
        )
        return ratio_str

    @staticmethod
    def _format_tables(tables: list[dict]) -> str:
        """Format table statistics"""
        if not tables:
            return "- No table statistics available"
        return "\n".join(
            [
                f"- {t.get('table_name', 'N/A')}: {t.get('row_count', 0)} rows, "
                f"{t.get('size_mb', 0):.2f} MB"
                for t in tables[:5]
            ]
        )


class MongoDBPromptBuilder:
    """Build structured prompts for MongoDB analysis via Gemini"""

    SYSTEM_INSTRUCTION = (
        "You are an expert MongoDB performance analyst and "
        "optimization specialist.\n"
        "Analyze the provided profiler data and current operations, "
        "then provide:\n"
        "1. **Critical Issues** (blocking operations, memory pressure)\n"
        "2. **High Priority** (index optimization, query efficiency)\n"
        "3. **Medium Priority** (aggregation improvements, data modeling)\n"
        "4. **Low Priority** (monitoring enhancements)\n\n"
        "Focus on practical, immediately actionable recommendations."
    )

    @staticmethod
    def build_prompt(
        db_name: str,
        profiler_analysis: dict,
        currentop_snapshot: dict,
        index_stats: dict,
        connection_info: dict,
        workload_type: str = "OLTP",
    ) -> str:
        """Build MongoDB analysis prompt for Gemini

        Args:
            db_name: Database name
            profiler_analysis: Profiler deep analysis results
            currentop_snapshot: Current operations snapshot
            index_stats: Index usage statistics
            connection_info: Connection and resource info
            workload_type: Detected workload type

        Returns:
            Formatted prompt string
        """
        prompt = f"""# MongoDB Database Analysis Report

## Database Environment
- **Database:** {db_name}
- **Workload Type:** {workload_type}
- **Timestamp:** {currentop_snapshot.get("timestamp", "N/A")}

## Current Operations
- **Total Operations:** {currentop_snapshot.get("total_operations", 0)}
- **Long-Running Ops:** {currentop_snapshot.get("long_running_count", 0)}
- **Blocked Operations:** {currentop_snapshot.get("blocked_count", 0)}
- **Idle Connections:** {currentop_snapshot.get("idle_count", 0)}

## Profiler Analysis
{MongoDBPromptBuilder._format_profiler(profiler_analysis)}

## Index Usage
{MongoDBPromptBuilder._format_indexes(index_stats)}

## Slow Operations
{MongoDBPromptBuilder._format_slow_ops(currentop_snapshot)}

## Resource Utilization
{MongoDBPromptBuilder._format_resources(connection_info)}

Please provide optimization recommendations for this MongoDB deployment."""

        return prompt

    @staticmethod
    def _format_profiler(analysis: dict) -> str:
        """Format profiler analysis"""
        if not analysis:
            return "- No profiler data available"
        return (
            f"- Slow Queries: {analysis.get('slow_query_count', 0)}\n"
            f"- Inefficient Queries: {analysis.get('inefficient_count', 0)}\n"
            f"- Avg Query Time: {analysis.get('avg_duration_ms', 0):.2f}ms"
        )

    @staticmethod
    def _format_indexes(stats: dict) -> str:
        """Format index statistics"""
        if not stats:
            return "- No index statistics available"
        return (
            f"- Total Indexes: {stats.get('total_indexes', 0)}\n"
            f"- Unused Indexes: {stats.get('unused_count', 0)}\n"
            f"- Missing Indexes: {stats.get('missing_count', 0)}"
        )

    @staticmethod
    def _format_slow_ops(snapshot: dict) -> str:
        """Format slow operations"""
        ops = snapshot.get("slow_operations", [])
        if not ops:
            return "- No slow operations detected"
        return "\n".join(
            [
                f"- Operation: {op.get('op', 'N/A')} ({op.get('ns', 'N/A')})\n"
                f"  Duration: {op.get('duration_ms', 0)}ms"
                for op in ops[:5]
            ]
        )

    @staticmethod
    def _format_resources(info: dict) -> str:
        """Format resource utilization"""
        return (
            f"- Connections: {info.get('current_connections', 0)} / "
            f"{info.get('max_connections', 0)}\n"
            f"- Memory Usage: {info.get('memory_usage_mb', 0):.2f} MB"
        )


class AIPromptDefaults:
    """Default configurations for AI prompts"""

    POSTGRESQL_SYSTEM_INSTRUCTION = PostgreSQLPromptBuilder.SYSTEM_INSTRUCTION
    MONGODB_SYSTEM_INSTRUCTION = MongoDBPromptBuilder.SYSTEM_INSTRUCTION

    @staticmethod
    def get_system_instruction(database_type: str) -> str:
        """Get appropriate system instruction for database type

        Args:
            database_type: 'postgresql' or 'mongodb'

        Returns:
            System instruction string
        """
        if database_type.lower() == "postgresql":
            return AIPromptDefaults.POSTGRESQL_SYSTEM_INSTRUCTION
        elif database_type.lower() == "mongodb":
            return AIPromptDefaults.MONGODB_SYSTEM_INSTRUCTION
        else:
            return (
                "You are a database performance analyst. "
                "Provide actionable recommendations."
            )
