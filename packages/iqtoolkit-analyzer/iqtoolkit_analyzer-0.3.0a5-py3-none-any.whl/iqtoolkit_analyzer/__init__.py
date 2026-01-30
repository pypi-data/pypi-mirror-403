"""
Iqtoolkit Analyzer - AI-powered multi-database performance analyzer

Database Support:
  - PostgreSQL ✓ (Production Ready)
  - MongoDB ✓ (Production Ready)
  - MySQL (Planned v0.4.0)
  - SQL Server (Planned v0.4.0)

AI Providers:
  - v0.2.2a1: OpenAI integration (requires OPENAI_API_KEY)
  - v0.2.3+: Configurable (Ollama privacy-first, OpenAI optional)

Self-hosted, privacy-first, 100% open source.
"""

from importlib import import_module
from typing import Any

from .__version__ import __version__

__all__ = [
    "__version__",
    "parse_postgres_log",
    "run_slow_query_analysis",
    "normalize_query",
    "LLMClient",
    "LLMConfig",
    "ReportGenerator",
    "AntiPatternDetector",
    "StaticQueryRewriter",
    "AntiPatternMatch",
    "AntiPatternType",
]

_LAZY_IMPORTS = {
    "parse_postgres_log": "iqtoolkit_analyzer.parser",
    "run_slow_query_analysis": "iqtoolkit_analyzer.analyzer",
    "normalize_query": "iqtoolkit_analyzer.analyzer",
    "LLMClient": "iqtoolkit_analyzer.llm_client",
    "LLMConfig": "iqtoolkit_analyzer.llm_client",
    "ReportGenerator": "iqtoolkit_analyzer.report_generator",
    "AntiPatternDetector": "iqtoolkit_analyzer.antipatterns",
    "StaticQueryRewriter": "iqtoolkit_analyzer.antipatterns",
    "AntiPatternMatch": "iqtoolkit_analyzer.antipatterns",
    "AntiPatternType": "iqtoolkit_analyzer.antipatterns",
}


def __getattr__(name: str) -> Any:
    if name in _LAZY_IMPORTS:
        module = import_module(_LAZY_IMPORTS[name])
        value = getattr(module, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module 'iqtoolkit_analyzer' has no attribute '{name}'")
