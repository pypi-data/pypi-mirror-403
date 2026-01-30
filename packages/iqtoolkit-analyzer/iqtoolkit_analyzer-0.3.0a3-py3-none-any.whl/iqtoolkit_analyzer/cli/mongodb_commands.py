"""CLI commands for MongoDB analysis"""

import json
import logging
import os
import sys
from datetime import datetime
from typing import Optional

import click

from iqtoolkit_analyzer.mongodb_analyzer import MongoDBProfilerIntegration
from iqtoolkit_analyzer.mongodb_config import MongoDBThresholdConfig

# Optional AI integration
try:
    from iqtoolkit_analyzer.ai import GoogleAIAdapter

    HAS_AI = True
except ImportError:
    HAS_AI = False
    GoogleAIAdapter = None  # type: ignore

logger = logging.getLogger(__name__)


@click.group(name="mongo", help="MongoDB analysis commands")
def mongodb_group() -> None:
    """MongoDB analysis and reporting commands"""
    pass


@mongodb_group.command(name="analyze", help="Analyze a MongoDB database")
@click.option(
    "--connection",
    "-c",
    required=True,
    help="MongoDB connection string (e.g., mongodb://user:pass@localhost:27017/dbname)",
)
@click.option(
    "--database",
    "-d",
    required=True,
    help="Database name to analyze",
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
    database: str,
    output: Optional[str],
    verbose: bool,
    use_ai: bool,
    ai_model: str,
    ai_stream: bool,
) -> None:
    """
    Analyze a MongoDB database and generate recommendations.

    Examples:

    \b
    # Basic analysis
    iqtoolkit-analyzer mongo analyze -c "mongodb://localhost:27017" -d mydb

    \b
    # With AI recommendations
    iqtoolkit-analyzer mongo analyze -c mongodb://user:pass@localhost/admin \\
    -d mydb --use-ai --ai-stream
    """
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    logger.info(f"Analyzing MongoDB database: {database}")

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

        # Initialize MongoDB analyzer
        thresholds = MongoDBThresholdConfig()
        analyzer = MongoDBProfilerIntegration(
            connection, thresholds, ai_adapter=ai_adapter, use_ai=use_ai
        )

        # Connect to MongoDB
        if not analyzer.connect():
            click.secho("❌ Failed to connect to MongoDB", fg="red")
            raise click.Abort()

        # Display connection info
        click.echo("\n" + "=" * 80)
        click.echo("📊 MongoDB Database Analysis Summary")
        click.echo("=" * 80)

        click.echo(f"\n🗄️  Database: {database}")
        click.echo(f"🔗 Connection: {connection}")

        # Collect profiler data
        click.echo("\n📥 Collecting profiler data...")
        profile_data = analyzer.collect_profile_data(database, time_window_minutes=60)
        click.echo(f"  ✅ Collected {len(profile_data)} slow operations")

        # Display findings
        click.echo("\n💡 Findings:")
        click.echo(f"  • Profiler entries: {len(profile_data)}")

        # Show top slow operations (raw profile data)
        if profile_data:
            click.echo("\n⏱️  Top Slow Operations (first 5):")
            for i, record in enumerate(profile_data[:5], 1):
                ns = record.get("ns", "unknown")
                millis = record.get("millis", 0)
                command_type = (
                    next(iter(record.get("command", {})))
                    if record.get("command")
                    else "unknown"
                )
                click.echo(f"\n  {i}. Operation: {command_type}")
                click.echo(f"     Namespace: {ns}")
                click.echo(f"     Duration: {millis}ms")

        # Export to JSON if requested
        if output:
            export_data = {
                "timestamp": datetime.now().isoformat(),
                "database": database,
                "summary": {
                    "slow_operations": len(profile_data),
                    "profiler_entries": len(profile_data),
                },
                "slow_queries": profile_data,
            }

            with open(output, "w") as f:
                json.dump(export_data, f, indent=2, default=str)

            click.secho(f"\n✅ Results exported to {output}", fg="green")

        click.echo("\n✅ Analysis complete\n")

    except click.Abort:
        # User aborted the operation (e.g., Ctrl+C), exit gracefully without error
        pass
    except Exception as e:
        logger.exception("Analysis failed")
        click.secho(f"\n❌ Analysis failed: {e}", fg="red")
        sys.exit(1)


@mongodb_group.command(name="profile", help="Manage MongoDB profiling")
@click.option(
    "--connection",
    "-c",
    required=True,
    help="MongoDB connection string",
)
@click.option(
    "--database",
    "-d",
    required=True,
    help="Database name to profile",
)
@click.option(
    "--level",
    type=click.Choice(["0", "1", "2"], case_sensitive=False),
    default="1",
    help="Profiling level (0=off, 1=slow ops, 2=all ops)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output",
)
def manage_profiling(connection: str, database: str, level: str, verbose: bool) -> None:
    """
    Manage MongoDB profiling settings.

    Examples:

    \b
    # Enable slow query profiling
    iqtoolkit-analyzer mongo profile -c mongodb://localhost:27017 -d mydb --level 1

    \b
    # Disable profiling
    iqtoolkit-analyzer mongo profile -c mongodb://localhost:27017 -d mydb --level 0
    """
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    try:
        thresholds = MongoDBThresholdConfig()
        analyzer = MongoDBProfilerIntegration(connection, thresholds)

        if not analyzer.connect():
            click.secho("❌ Failed to connect to MongoDB", fg="red")
            raise click.Abort()

        # Enable/disable profiling
        success = analyzer.enable_profiling(database, level=int(level))

        if success:
            status = {0: "disabled", 1: "slow queries", 2: "all operations"}
            click.secho(
                f"✅ Profiling {status[int(level)]} for database '{database}'",
                fg="green",
            )
        else:
            click.secho(
                f"❌ Failed to set profiling level for database '{database}'", fg="red"
            )

    except click.Abort:
        # User aborted the operation (e.g., Ctrl+C), exit gracefully without error
        pass
    except Exception as e:
        logger.exception("Profiling management failed")
        click.secho(f"\n❌ Failed: {e}", fg="red")
        sys.exit(1)
