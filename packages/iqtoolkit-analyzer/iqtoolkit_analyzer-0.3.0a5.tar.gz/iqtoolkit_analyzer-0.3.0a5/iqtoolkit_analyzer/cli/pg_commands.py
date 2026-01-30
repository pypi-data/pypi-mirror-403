"""CLI commands for PostgreSQL analysis"""

import json
import logging
import os
from datetime import datetime
from typing import Optional

import click

from iqtoolkit_analyzer.postgresql import (
    PostgreSQLAnalyzer,
    SettingsReportGenerator,
)

# Optional AI integration
try:
    from iqtoolkit_analyzer.ai import GoogleAIAdapter

    HAS_AI = True
except ImportError:
    HAS_AI = False
    GoogleAIAdapter = None  # type: ignore

logger = logging.getLogger(__name__)


@click.group(name="pg", help="PostgreSQL analysis commands")
def postgresql_group() -> None:
    """PostgreSQL analysis and reporting commands"""
    pass


@postgresql_group.command(name="analyze", help="Analyze a PostgreSQL database")
@click.option(
    "--connection",
    "-c",
    required=True,
    help="PostgreSQL connection string (e.g., postgresql://user:pass@localhost/dbname)",
)
@click.option(
    "--output",
    "-o",
    help="Output file path for JSON results (optional)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output",
)
@click.option(
    "--use-ai",
    is_flag=True,
    help="Enable AI-powered recommendations (requires GOOGLE_API_KEY env var)",
)
@click.option(
    "--ai-model",
    default="gemini-2.0-flash",
    help="Google Gemini model to use (default: gemini-2.0-flash)",
    type=click.Choice(
        ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"], case_sensitive=False
    ),
)
@click.option(
    "--ai-stream",
    is_flag=True,
    help="Stream AI response chunks in real-time",
)
def analyze_database(
    connection: str,
    output: Optional[str],
    verbose: bool,
    use_ai: bool,
    ai_model: str,
    ai_stream: bool,
) -> None:
    """
    Analyze a PostgreSQL database and generate recommendations.

    Examples:

    \b
    # Basic analysis with summary output
    iqtoolkit-analyzer pg analyze -c "postgresql://localhost/postgres"

    \b
    # Detailed analysis with JSON export
    iqtoolkit-analyzer pg analyze -c postgresql://user:pass@localhost/db \\
    -o results.json -v
    """
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    logger.info(f"Analyzing PostgreSQL database: {connection}")

    try:
        # Initialize AI adapter if requested
        ai_adapter = None
        if use_ai:
            if not HAS_AI or GoogleAIAdapter is None:
                msg = (
                    "\u26a0\ufe0f  Google AI adapter not available "
                    "(google-generativeai not installed)"
                )
                click.secho(msg, fg="yellow")
                use_ai = False
            else:
                try:
                    api_key = os.getenv("GOOGLE_API_KEY")
                    ai_adapter = GoogleAIAdapter(api_key=api_key, model=ai_model)
                    logger.info(f"Initialized Google AI adapter (model: {ai_model})")
                except Exception as e:
                    click.secho(
                        f"\u26a0\ufe0f  Failed to initialize AI adapter: {e}",
                        fg="yellow",
                    )
                    use_ai = False

        # Run analysis
        analyzer = PostgreSQLAnalyzer(connection, ai_adapter=ai_adapter, use_ai=use_ai)
        result = analyzer.analyze()

        # Display summary
        click.echo("\n" + "=" * 80)
        click.echo("📊 PostgreSQL Database Analysis Summary")
        click.echo("=" * 80)

        click.echo(f"\n🗄️  Database: {result.settings.database_name}")
        click.echo(f"📌 Version: {result.settings.server_version_num}")
        click.echo(f"👤 User: {result.settings.current_user}")
        click.echo(f"🔐 Superuser: {result.settings.superuser}")
        click.echo(f"📦 Tables: {result.settings.tables_count}")
        click.echo(f"🔑 Indexes: {result.settings.indexes_count}")
        click.echo(f"🧩 Extensions: {len(result.settings.extensions)}")

        # Display metrics
        click.echo("\n📈 Metrics:")
        click.echo(f"  • Slow queries: {len(result.slow_queries)}")
        click.echo(f"  • Table stats: {len(result.table_stats)}")
        click.echo(f"  • Index stats: {len(result.index_stats)}")
        click.echo(f"  • Active locks: {len(result.locks)}")
        click.echo(f"  • Vacuum stats: {len(result.vacuum_stats)}")
        click.echo(f"  • Active connections: {len(result.connections)}")

        # Group recommendations by severity
        critical = [r for r in result.recommendations if r.severity == "critical"]
        warning = [r for r in result.recommendations if r.severity == "warning"]
        info = [r for r in result.recommendations if r.severity == "info"]

        click.echo(f"\n💡 Recommendations: {len(result.recommendations)} total")
        click.echo(f"  • 🔴 Critical: {len(critical)}")
        click.echo(f"  • 🟡 Warning: {len(warning)}")
        click.echo(f"  • 🔵 Info: {len(info)}")

        # Display critical recommendations
        if critical:
            click.echo("\n🔴 Critical Issues:")
            for i, rec in enumerate(critical[:10], 1):
                click.echo(f"\n  {i}. {rec.title}")
                click.echo(f"     Category: {rec.category}")
                click.echo(f"     {rec.description}")
                click.echo(f"     → {rec.suggestion}")
                if rec.current_value is not None:
                    click.echo(
                        f"     Current: {rec.current_value}; Threshold: {rec.threshold}"
                    )

        # Display warnings
        if warning:
            click.echo(f"\n🟡 Warnings ({min(5, len(warning))} of {len(warning)}):")
            for i, rec in enumerate(warning[:5], 1):
                click.echo(f"\n  {i}. {rec.title}")
                click.echo(f"     → {rec.suggestion}")

        # Get AI recommendations if enabled
        if use_ai and ai_adapter:
            click.echo("\n" + "=" * 80)
            click.echo("🤖 AI-Powered Recommendations (Google Gemini)")
            click.echo("=" * 80)
            try:
                ai_recommendations = analyzer.get_ai_recommendations(
                    result, use_streaming=ai_stream
                )
                if ai_recommendations:
                    click.echo(f"\n{ai_recommendations}")
                else:
                    click.echo("\n⚠️  No AI recommendations available at this time")
            except Exception as e:
                logger.error(f"AI recommendation error: {e}")
                click.secho(f"\n⚠️  AI recommendation failed: {e}", fg="yellow")

        # Export to JSON if requested
        if output:
            export_data = {
                "timestamp": datetime.now().isoformat(),
                "database": result.settings.database_name,
                "version": result.settings.server_version_num,
                "summary": {
                    "tables": result.settings.tables_count,
                    "indexes": result.settings.indexes_count,
                    "extensions": len(result.settings.extensions),
                    "slow_queries": len(result.slow_queries),
                    "active_locks": len(result.locks),
                    "active_connections": len(result.connections),
                },
                "recommendations": {
                    "total": len(result.recommendations),
                    "critical": len(critical),
                    "warning": len(warning),
                    "info": len(info),
                },
                "issues": [
                    {
                        "severity": rec.severity,
                        "category": rec.category,
                        "title": rec.title,
                        "description": rec.description,
                        "suggestion": rec.suggestion,
                        "metric": rec.metric,
                        "current_value": rec.current_value,
                        "threshold": rec.threshold,
                    }
                    for rec in result.recommendations
                ],
            }

            with open(output, "w") as f:
                json.dump(export_data, f, indent=2)
            click.echo(f"\n✅ Results saved to: {output}")

        click.echo("\n" + "=" * 80)

    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red", bold=True)
        if verbose:
            import traceback

            traceback.print_exc()
        raise click.ClickException(str(e))


@postgresql_group.command(name="settings", help="Generate PostgreSQL settings report")
@click.option(
    "--connection",
    "-c",
    required=True,
    help="PostgreSQL connection string",
)
@click.option(
    "--output",
    "-o",
    default="postgresql_settings_report.html",
    help="Output HTML file path (default: postgresql_settings_report.html)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output",
)
def generate_settings_report(connection: str, output: str, verbose: bool) -> None:
    """
    Generate an HTML report of PostgreSQL settings and configuration.

    Examples:

    \b
    # Generate settings report
    iqtoolkit-analyzer pg settings -c "postgresql://localhost/postgres"

    \b
    # Save to custom file
    iqtoolkit-analyzer pg settings -c postgresql://localhost/db -o custom_report.html
    """
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    logger.info(f"Generating settings report for: {connection}")

    try:
        from iqtoolkit_analyzer.postgresql import SettingsCapture

        # Capture settings
        click.echo("📊 Capturing PostgreSQL settings...")
        capture = SettingsCapture(connection)
        settings = capture.capture_all()

        # Generate report
        click.echo("🎨 Generating HTML report...")
        SettingsReportGenerator.save_report(settings, output)

        click.secho(f"✅ Settings report saved to: {output}", fg="green", bold=True)
        click.echo("\nReport includes:")
        click.echo("  • System information")
        click.echo("  • Runtime settings")
        click.echo("  • Configuration files")
        click.echo("  • Databases and tables")
        click.echo("  • Installed extensions")
        click.echo("  • Performance metrics")

    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red", bold=True)
        if verbose:
            import traceback

            traceback.print_exc()
        raise click.ClickException(str(e))


@postgresql_group.command(name="slow-queries", help="Analyze slow queries")
@click.option(
    "--connection",
    "-c",
    required=True,
    help="PostgreSQL connection string",
)
@click.option(
    "--limit",
    "-l",
    default=10,
    help="Number of slow queries to display (default: 10)",
)
@click.option(
    "--min-time",
    "-m",
    default=1000,
    help="Minimum query time in milliseconds (default: 1000)",
)
def analyze_slow_queries(connection: str, limit: int, min_time: float) -> None:
    """
    Analyze slow queries in a PostgreSQL database.

    Requires pg_stat_statements extension to be installed.

    Example:

    \b
    iqtoolkit-analyzer pg slow-queries -c \\
    "postgresql://localhost/postgres" --limit 20 --min-time 500
    """
    logging.basicConfig(level=logging.INFO)

    click.echo(f"🐢 Analyzing slow queries (>{min_time}ms)...")

    try:
        analyzer = PostgreSQLAnalyzer(connection)
        result = analyzer.analyze()

        slow_queries = [
            q for q in result.slow_queries if q.get("mean_time", 0) >= min_time
        ]

        if not slow_queries:
            click.secho(f"✅ No slow queries found (>{min_time}ms)", fg="green")
            return

        click.echo(f"\n🐢 Found {len(slow_queries)} slow queries:\n")

        for i, query in enumerate(slow_queries[:limit], 1):
            mean_time = query.get("mean_time", 0)
            max_time = query.get("max_time", 0)
            calls = query.get("calls", 0)
            total_time = query.get("total_time", 0)

            click.echo(f"{i}. Query")
            click.echo(f"   Mean time: {mean_time:.0f}ms | Max: {max_time:.0f}ms")
            click.echo(f"   Calls: {calls} | Total: {total_time:.0f}ms")
            click.echo()

    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red", bold=True)
        raise click.ClickException(str(e))


@postgresql_group.command(name="bloat", help="Detect table bloat")
@click.option(
    "--connection",
    "-c",
    required=True,
    help="PostgreSQL connection string",
)
@click.option(
    "--threshold",
    "-t",
    default=20,
    help="Bloat percentage threshold (default: 20%)",
)
def detect_table_bloat(connection: str, threshold: float) -> None:
    """
    Detect bloated tables in a PostgreSQL database.

    Example:

    \b
    iqtoolkit-analyzer pg bloat -c "postgresql://localhost/postgres" --threshold 30
    """
    logging.basicConfig(level=logging.INFO)

    click.echo(f"🗑️  Detecting table bloat (>{threshold}%)...\n")

    try:
        analyzer = PostgreSQLAnalyzer(connection)
        result = analyzer.analyze()

        # Find bloat recommendations
        bloat_recs = [r for r in result.recommendations if "bloat" in r.title.lower()]

        if not bloat_recs:
            click.secho("✅ No significant bloat detected", fg="green")
            return

        click.echo(f"🗑️  Found {len(bloat_recs)} tables with bloat:\n")

        for i, rec in enumerate(bloat_recs[:10], 1):
            click.echo(f"{i}. {rec.title}")
            click.echo(f"   Severity: {rec.severity.upper()}")
            click.echo(f"   {rec.description}")
            click.echo(f"   → {rec.suggestion}")
            click.echo()

    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red", bold=True)
        raise click.ClickException(str(e))


@postgresql_group.command(name="health", help="Quick database health check")
@click.option(
    "--connection",
    "-c",
    required=True,
    help="PostgreSQL connection string",
)
def health_check(connection: str) -> None:
    """
    Perform a quick health check on a PostgreSQL database.

    Example:

    \b
    iqtoolkit-analyzer pg health -c "postgresql://localhost/postgres"
    """
    logging.basicConfig(level=logging.INFO)

    click.echo("🏥 Running health check...\n")

    try:
        analyzer = PostgreSQLAnalyzer(connection)
        result = analyzer.analyze()

        # Count issues
        critical = [r for r in result.recommendations if r.severity == "critical"]
        warning = [r for r in result.recommendations if r.severity == "warning"]

        # Determine overall health
        if len(critical) > 0:
            health_status = "🔴 CRITICAL"
            health_color = "red"
        elif len(warning) > 5:
            health_status = "🟡 WARNING"
            health_color = "yellow"
        else:
            health_status = "🟢 HEALTHY"
            health_color = "green"

        click.secho(f"Status: {health_status}", fg=health_color, bold=True)

        click.echo(f"\n📊 Database: {result.settings.database_name}")
        click.echo(f"📌 Version: {result.settings.server_version_num}")
        click.echo(f"📦 Tables: {result.settings.tables_count}")
        click.echo(f"🔑 Indexes: {result.settings.indexes_count}")

        click.echo("\n⚠️  Issues:")
        click.echo(f"  🔴 Critical: {len(critical)}")
        click.echo(f"  🟡 Warning: {len(warning)}")

        if critical:
            click.echo("\n  Critical issues:")
            for rec in critical[:3]:
                click.echo(f"    • {rec.title}")

    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red", bold=True)
        raise click.ClickException(str(e))


if __name__ == "__main__":
    postgresql_group()
