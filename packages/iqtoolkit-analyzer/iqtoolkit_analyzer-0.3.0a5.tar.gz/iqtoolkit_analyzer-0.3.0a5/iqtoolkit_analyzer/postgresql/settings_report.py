"""Generate HTML reports for PostgreSQL settings"""

import logging
from datetime import datetime
from pathlib import Path

from .settings_capture import PostgreSQLSettings

logger = logging.getLogger(__name__)


class SettingsReportGenerator:
    """Generate HTML reports for PostgreSQL settings"""

    @staticmethod
    def generate_html(
        settings: PostgreSQLSettings, title: str = "PostgreSQL Settings Report"
    ) -> str:
        """Generate complete HTML report"""
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        {SettingsReportGenerator._get_css()}
    </style>
</head>
<body>
    <div class="container">
        {SettingsReportGenerator._header_section(settings)}
        {SettingsReportGenerator._summary_section(settings)}
        {SettingsReportGenerator._system_info_section(settings)}
        {SettingsReportGenerator._runtime_settings_section(settings)}
        {SettingsReportGenerator._configuration_section(settings)}
        {SettingsReportGenerator._database_objects_section(settings)}
        {SettingsReportGenerator._extensions_section(settings)}
        {SettingsReportGenerator._performance_section(settings)}
        {SettingsReportGenerator._footer()}
    </div>
</body>
</html>
"""

    @staticmethod
    def _get_css() -> str:
        """Get CSS styles"""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #333;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        
        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .section {
            padding: 30px;
            border-bottom: 1px solid #eee;
        }
        
        .section:last-child {
            border-bottom: none;
        }
        
        .section h2 {
            color: #667eea;
            font-size: 1.8em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }
        
        .section h3 {
            color: #764ba2;
            font-size: 1.3em;
            margin-top: 20px;
            margin-bottom: 15px;
        }
        
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .summary-card {
            background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .summary-card.warning {
            border-left-color: #f59e0b;
        }
        
        .summary-card.success {
            border-left-color: #10b981;
        }
        
        .summary-card label {
            display: block;
            font-size: 0.9em;
            color: #666;
            margin-bottom: 8px;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .summary-card .value {
            font-size: 1.8em;
            color: #667eea;
            font-weight: bold;
            word-break: break-all;
        }
        
        .summary-card.warning .value {
            color: #f59e0b;
        }
        
        .summary-card.success .value {
            color: #10b981;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        thead {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        th {
            padding: 15px;
            text-align: left;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.9em;
            letter-spacing: 0.5px;
        }
        
        td {
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
            font-size: 0.95em;
        }
        
        tbody tr:hover {
            background: #f9fafb;
        }
        
        tbody tr:nth-child(even) {
            background: #f3f4f6;
        }
        
        .setting-name {
            font-weight: 600;
            color: #667eea;
            font-family: 'Monaco', 'Courier New', monospace;
            font-size: 0.9em;
        }
        
        .setting-value {
            font-family: 'Monaco', 'Courier New', monospace;
            background: #f3f4f6;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.9em;
        }
        
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .badge.extension {
            background: #dbeafe;
            color: #0369a1;
        }
        
        .badge.database {
            background: #dcfce7;
            color: #166534;
        }
        
        .footer {
            background: #f9fafb;
            padding: 20px 30px;
            text-align: center;
            color: #999;
            font-size: 0.9em;
            border-top: 1px solid #eee;
        }
        
        .info-box {
            background: #eff6ff;
            border-left: 4px solid #3b82f6;
            padding: 15px;
            border-radius: 4px;
            margin: 15px 0;
            font-size: 0.95em;
        }
        
        .stats-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }
        
        .stats-row:last-child {
            border-bottom: none;
        }
        
        .stats-label {
            font-weight: 600;
            color: #666;
        }
        
        .stats-value {
            font-size: 1.2em;
            font-weight: bold;
            color: #667eea;
        }
    </style>
</head>
"""

    @staticmethod
    def _header_section(settings: PostgreSQLSettings) -> str:
        """Generate header section"""
        generated_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"""
        <div class="header">
            <h1>🐘 PostgreSQL Settings Report</h1>
            <p>
                Database: <strong>{settings.database_name}</strong><br/>
                User: <strong>{settings.current_user}</strong><br/>
                Generated: <strong>{generated_ts}</strong>
            </p>
        </div>
"""

    @staticmethod
    def _summary_section(settings: PostgreSQLSettings) -> str:
        """Generate summary section"""
        size_gb = settings.total_size_bytes / (1024**3)
        version_str = (
            f"{settings.server_version_num // 10000}."
            f"{(settings.server_version_num % 10000) // 100}"
        )
        super_cls = "success" if settings.superuser else "warning"
        return f"""
        <div class="section">
            <h2>📊 Summary</h2>
            <div class="summary-grid">
                <div class="summary-card success">
                    <label>PostgreSQL Version</label>
                    <div class="value">{version_str}</div>
                </div>
                <div class="summary-card">
                    <label>Current User</label>
                    <div class="value">{settings.current_user}</div>
                </div>
                <div class="summary-card {super_cls}">
                    <label>Superuser</label>
                    <div class="value">{"✓ Yes" if settings.superuser else "✗ No"}</div>
                </div>
                <div class="summary-card">
                    <label>Database Size</label>
                    <div class="value">{size_gb:.2f} GB</div>
                </div>
                <div class="summary-card">
                    <label>Total Tables</label>
                    <div class="value">{settings.tables_count}</div>
                </div>
                <div class="summary-card">
                    <label>Total Indexes</label>
                    <div class="value">{settings.indexes_count}</div>
                </div>
            </div>
        </div>
"""

    @staticmethod
    def _system_info_section(settings: PostgreSQLSettings) -> str:
        """Generate system info section"""
        return f"""
        <div class="section">
            <h2>ℹ️ System Information</h2>
            <div class="info-box">
                <strong>Version Details:</strong><br/>
                {settings.version}
            </div>
        </div>
"""

    @staticmethod
    def _runtime_settings_section(settings: PostgreSQLSettings) -> str:
        """Generate runtime settings section"""
        if not settings.runtime_settings:
            return ""

        rows = "".join(
            [
                f"""
            <tr>
                <td><span class="setting-name">{name}</span></td>
                <td><span class="setting-value">{value}</span></td>
            </tr>
            """
                for name, value in sorted(settings.runtime_settings.items())
            ]
        )

        return f"""
        <div class="section">
            <h2>⚙️ Runtime Settings</h2>
            <table>
                <thead>
                    <tr>
                        <th>Parameter</th>
                        <th>Value</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
"""

    @staticmethod
    def _configuration_section(settings: PostgreSQLSettings) -> str:
        """Generate configuration section"""
        if not settings.configuration_files:
            return ""

        rows = "".join(
            [
                f"""
            <div class="stats-row">
                <span class="stats-label">{name}</span>
                <span class="setting-value">{value}</span>
            </div>
            """
                for name, value in settings.configuration_files.items()
            ]
        )

        return f"""
        <div class="section">
            <h2>📁 Configuration Files</h2>
            {rows}
        </div>
"""

    @staticmethod
    def _database_objects_section(settings: PostgreSQLSettings) -> str:
        """Generate database objects section"""
        if not settings.databases:
            return ""

        rows = "".join(
            [
                f"""
            <tr>
                <td><span class="badge database">{db["name"]}</span></td>
                <td>{db.get("size", "N/A")}</td>
                <td>{db.get("connections", 0)}</td>
            </tr>
            """
                for db in settings.databases
            ]
        )

        return f"""
        <div class="section">
            <h2>🗄️ Databases</h2>
            <table>
                <thead>
                    <tr>
                        <th>Database Name</th>
                        <th>Size</th>
                        <th>Connections</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
"""

    @staticmethod
    def _extensions_section(settings: PostgreSQLSettings) -> str:
        """Generate extensions section"""
        if not settings.extensions:
            return (
                "<div class='section'><h2>📦 Extensions</h2>"
                "<p>No extensions installed</p></div>"
            )

        rows = "".join(
            [
                f"""
            <tr>
                <td><span class="badge extension">{ext["name"]}</span></td>
                <td>{ext.get("version", "N/A")}</td>
                <td><code>{ext.get("schema", "N/A")}</code></td>
            </tr>
            """
                for ext in settings.extensions
            ]
        )

        return f"""
        <div class="section">
            <h2>📦 Extensions ({len(settings.extensions)})</h2>
            <table>
                <thead>
                    <tr>
                        <th>Extension</th>
                        <th>Version</th>
                        <th>Schema</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
"""

    @staticmethod
    def _performance_section(settings: PostgreSQLSettings) -> str:
        """Generate performance section"""
        if not settings.cache_info:
            return ""

        stats = "".join(
            [
                f"""
            <div class="stats-row">
                <span class="stats-label">{key.replace("_", " ").title()}</span>
                <span class="stats-value">{value}</span>
            </div>
            """
                for key, value in settings.cache_info.items()
            ]
        )

        return f"""
        <div class="section">
            <h2>📈 Performance Metrics</h2>
            {stats}
        </div>
"""

    @staticmethod
    def _footer() -> str:
        """Generate footer"""
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"""
        <div class="footer">
            <p>Generated by IQToolkit Analyzer on {ts}</p>
            <p>This report captures PostgreSQL configuration and system
               information for analysis and documentation purposes.</p>
        </div>
"""

    @staticmethod
    def save_report(settings: PostgreSQLSettings, output_path: str) -> Path:
        """Generate and save HTML report to file"""
        html_content = SettingsReportGenerator.generate_html(settings)
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(html_content, encoding="utf-8")
        logger.info(f"Settings report saved to {path}")
        return path
