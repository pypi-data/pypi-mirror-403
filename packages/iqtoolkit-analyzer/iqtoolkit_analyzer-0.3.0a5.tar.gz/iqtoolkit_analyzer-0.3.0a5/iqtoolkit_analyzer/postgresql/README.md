# PostgreSQL Module

This module provides comprehensive PostgreSQL database analysis, monitoring, and optimization capabilities.

## Quick Start

### Installation
```bash
pip install iqtoolkit-analyzer
```

### Basic Usage
```python
from iqtoolkit_analyzer.postgresql import PostgreSQLAnalyzer

# Analyze a database
analyzer = PostgreSQLAnalyzer("postgresql://user:pass@localhost/mydb")
result = analyzer.analyze()

# View recommendations
for rec in result.recommendations:
    print(f"{rec.severity.upper()}: {rec.title}")
    print(f"  {rec.suggestion}")
```

### CLI Usage
```bash
# Analyze database
iqtoolkit-analyzer pg analyze -c "postgresql://localhost/postgres"

# Generate settings report
iqtoolkit-analyzer pg settings -c "postgresql://localhost/postgres"

# Find slow queries
iqtoolkit-analyzer pg slow-queries -c "postgresql://localhost/postgres"

# Quick health check
iqtoolkit-analyzer pg health -c "postgresql://localhost/postgres"
```

## Module Structure

```
iqtoolkit_analyzer/postgresql/
├── __init__.py                 # Public API exports
├── settings_capture.py         # Capture PostgreSQL configuration
├── settings_report.py          # Generate HTML reports
├── pgtools_wrapper.py          # Execute pgtools scripts
└── pgtools_analyzer.py         # Comprehensive analysis engine
```

## Components

### SettingsCapture
Captures PostgreSQL configuration and metrics:
- Database version and user info
- Configuration parameters
- Installed extensions
- Database/table/index counts
- Cache metrics

```python
from iqtoolkit_analyzer.postgresql import SettingsCapture

capture = SettingsCapture("postgresql://localhost/postgres")
settings = capture.capture_all()
print(f"Version: {settings.server_version_num}")
```

### SettingsReportGenerator
Generates professional HTML reports:

```python
from iqtoolkit_analyzer.postgresql import SettingsReportGenerator

SettingsReportGenerator.save_report(settings, "report.html")
```

### PgToolsWrapper
Executes pgtools scripts:

```python
from iqtoolkit_analyzer.postgresql import PgToolsWrapper

wrapper = PgToolsWrapper("postgresql://localhost/postgres")
slow_queries = wrapper.get_slow_queries()
table_stats = wrapper.get_table_stats()
```

### PostgreSQLAnalyzer
Comprehensive analysis with recommendations:

```python
from iqtoolkit_analyzer.postgresql import PostgreSQLAnalyzer

analyzer = PostgreSQLAnalyzer("postgresql://localhost/postgres")
result = analyzer.analyze()

# Get critical issues only
critical = [r for r in result.recommendations if r.severity == "critical"]
```

## Analysis Categories

The analyzer examines 8 key areas:

1. **Slow Queries** - Identifies queries slower than 1 second (requires pg_stat_statements)
2. **Tables** - Detects bloat, size issues, and missing statistics
3. **Indexes** - Analyzes index efficiency and redundancy
4. **Locks** - Detects long-running locks and contention
5. **Vacuum** - Checks autovacuum configuration and stats
6. **Cache** - Evaluates cache hit ratios
7. **Settings** - Validates configuration parameters
8. **Connections** - Checks connection limits and usage

## Output Formats

### Console Output
```
📊 PostgreSQL Database Analysis Summary
================================================================================
🗄️  Database: production_db
📌 Version: 150000
📦 Tables: 25
🔑 Indexes: 87

💡 Recommendations: 15 total
  🔴 Critical: 2
  🟡 Warning: 6
  🔵 Info: 7
```

### HTML Report
Professional HTML report with:
- System information cards
- Configuration parameters
- Extensions list
- Performance metrics
- Responsive design
- Color-coded information

### JSON Export
```json
{
  "database": "production_db",
  "version": 150000,
  "recommendations": {
    "total": 15,
    "critical": 2,
    "warning": 6
  },
  "issues": [...]
}
```

## Prerequisites

### Required
- Python 3.11+
- PostgreSQL 12+
- psycopg 3.1.18+

### Recommended Extensions
- pg_stat_statements (slow query analysis)
- pgstattuple (table/index bloat analysis)
- auto_explain (query plan logging)

### Enable pg_stat_statements
```sql
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
-- Add to postgresql.conf:
shared_preload_libraries = 'pg_stat_statements'
-- Then restart PostgreSQL
SELECT pg_stat_statements_reset();
```

## Examples

### Example 1: Analyze and Export
```python
from iqtoolkit_analyzer.postgresql import PostgreSQLAnalyzer
import json

analyzer = PostgreSQLAnalyzer("postgresql://localhost/postgres")
result = analyzer.analyze()

# Export critical issues
export_data = {
    "database": result.settings.database_name,
    "critical_issues": [
        {
            "title": r.title,
            "description": r.description,
            "suggestion": r.suggestion
        }
        for r in result.recommendations if r.severity == "critical"
    ]
}

with open("critical_issues.json", "w") as f:
    json.dump(export_data, f, indent=2)
```

### Example 2: Custom Reports
```python
from iqtoolkit_analyzer.postgresql import PostgreSQLAnalyzer

analyzer = PostgreSQLAnalyzer("postgresql://localhost/postgres")
result = analyzer.analyze()

# Performance issues only
perf_issues = [
    r for r in result.recommendations 
    if r.category == "performance" and r.severity in ["critical", "warning"]
]

print(f"Found {len(perf_issues)} performance issues")
for issue in perf_issues:
    print(f"  • {issue.title}: {issue.suggestion}")
```

### Example 3: Monitoring Script
```python
from iqtoolkit_analyzer.postgresql import PostgreSQLAnalyzer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_database_health(conn_string):
    analyzer = PostgreSQLAnalyzer(conn_string)
    result = analyzer.analyze()
    
    critical = [r for r in result.recommendations if r.severity == "critical"]
    
    if critical:
        logger.critical(f"Found {len(critical)} critical issues!")
        for issue in critical:
            logger.critical(f"  {issue.title}: {issue.suggestion}")
        return False
    else:
        logger.info("Database health is good")
        return True

# Check every hour
import schedule
schedule.every(1).hours.do(check_database_health, "postgresql://localhost/postgres")
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest tests/test_postgresql_modules.py -v

# Run with coverage
pytest tests/test_postgresql_modules.py --cov=iqtoolkit_analyzer.postgresql

# Run specific test class
pytest tests/test_postgresql_modules.py::TestPostgreSQLAnalyzer -v

# Run full integration test (requires live database)
pytest tests/test_postgresql_modules.py::TestIntegrationFull -v -s
```

## Documentation

- [PostgreSQL Tools Guide](../postgresql-tools.md) - Comprehensive user guide
- [CLI Reference](../api-reference.md) - Command-line interface reference
- [Examples](../examples.md) - More usage examples

## Troubleshooting

### Connection Issues
```python
try:
    analyzer = PostgreSQLAnalyzer("postgresql://localhost/postgres")
except Exception as e:
    print(f"Connection failed: {e}")
    # Check: PostgreSQL running, credentials correct, network access
```

### Missing pg_stat_statements
```sql
-- Install extension
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
-- Add to postgresql.conf and restart PostgreSQL
```

### High Memory Usage
The analysis should use minimal memory (<100MB). If it uses more:
- Reduce the number of slow queries being analyzed
- Analyze one schema at a time
- Use the `--limit` CLI option

## Performance Notes

- First run takes 5-10 seconds (initial connection + data collection)
- Subsequent runs take 2-5 seconds
- Analysis requires read-only database access
- No data is modified by the analysis

## Contributing

To add new analysis features:

1. Add a new `_analyze_*()` method to `PostgreSQLAnalyzer`
2. Return a list of `AnalysisRecommendation` objects
3. Call from the main `analyze()` method
4. Add corresponding tests to `test_postgresql_modules.py`

Example:
```python
def _analyze_custom(self) -> list[AnalysisRecommendation]:
    """Analyze custom metric"""
    recommendations = []
    
    # Get data from wrapper
    data = self.wrapper.get_custom_data()
    
    # Check threshold
    if data['value'] > threshold:
        recommendations.append(AnalysisRecommendation(
            severity="warning",
            category="performance",
            title="Custom Issue",
            description=f"Custom metric is {data['value']}",
            suggestion="Take corrective action"
        ))
    
    return recommendations
```

## API Reference

See [API Reference](../api-reference.md#postgresql-module) for detailed class and method documentation.

## License

MIT - See LICENSE file for details

## Support

- GitHub Issues: https://github.com/iqtoolkit/iqtoolkit-analyzer/issues
- Documentation: https://docs.iqtoolkit.ai/v0.3.0-alpha.5/
- Email: support@iqtoolkit.ai
