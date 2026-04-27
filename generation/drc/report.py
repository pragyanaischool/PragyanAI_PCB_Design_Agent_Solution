# generation/drc/report.py

from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

from utils.logger import get_module_logger
from utils.output_manager import OutputManager
from utils.json_utils import write_json

from generation.drc.rules import summarize_errors

logger = get_module_logger(__name__)
output_manager = OutputManager()


# --------------------------------------------------
# BUILD REPORT STRUCTURE
# --------------------------------------------------
def build_report(drc_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Standardize DRC report structure
    """

    errors = drc_result.get("errors", [])
    summary = summarize_errors(errors)

    report = {
        "timestamp": datetime.now().isoformat(),
        "status": drc_result.get("status", "UNKNOWN"),
        "total_errors": drc_result.get("total_errors", len(errors)),
        "summary": summary,
        "errors": errors
    }

    return report


# --------------------------------------------------
# TEXT REPORT
# --------------------------------------------------
def generate_text_report(report: Dict[str, Any]) -> str:
    lines = []

    lines.append("=== PCB DRC REPORT ===")
    lines.append(f"Timestamp: {report['timestamp']}")
    lines.append(f"Status: {report['status']}")
    lines.append(f"Total Errors: {report['total_errors']}")
    lines.append("")

    lines.append("Summary:")
    for k, v in report["summary"].items():
        lines.append(f"  {k}: {v}")

    lines.append("\nDetails:")

    for i, err in enumerate(report["errors"], 1):
        lines.append(f"{i}. [{err.get('severity', 'ERROR')}] {err.get('message')}")

    return "\n".join(lines)


# --------------------------------------------------
# HTML REPORT
# --------------------------------------------------
def generate_html_report(report: Dict[str, Any]) -> str:
    html = f"""
    <html>
    <head>
        <title>PCB DRC Report</title>
        <style>
            body {{ font-family: Arial; }}
            .error {{ color: red; }}
            .warning {{ color: orange; }}
            .info {{ color: blue; }}
        </style>
    </head>
    <body>
        <h1>PCB DRC Report</h1>
        <p><b>Timestamp:</b> {report['timestamp']}</p>
        <p><b>Status:</b> {report['status']}</p>
        <p><b>Total Errors:</b> {report['total_errors']}</p>

        <h2>Summary</h2>
        <ul>
            <li>ERROR: {report['summary'].get('ERROR', 0)}</li>
            <li>WARNING: {report['summary'].get('WARNING', 0)}</li>
            <li>INFO: {report['summary'].get('INFO', 0)}</li>
        </ul>

        <h2>Details</h2>
        <ul>
    """

    for err in report["errors"]:
        severity = err.get("severity", "ERROR").lower()
        html += f"<li class='{severity}'>[{severity.upper()}] {err.get('message')}</li>"

    html += """
        </ul>
    </body>
    </html>
    """

    return html


# --------------------------------------------------
# SAVE REPORTS
# --------------------------------------------------
def save_json_report(report: Dict[str, Any]) -> Path:
    filename = output_manager.generate_filename("drc_report", "json")
    path = output_manager.dirs["logs"] / filename

    write_json(report, path)

    logger.info(f"DRC JSON report saved: {path}")

    return path


def save_text_report(text: str) -> Path:
    filename = output_manager.generate_filename("drc_report", "txt")
    path = output_manager.dirs["logs"] / filename

    with open(path, "w") as f:
        f.write(text)

    logger.info(f"DRC text report saved: {path}")

    return path


def save_html_report(html: str) -> Path:
    filename = output_manager.generate_filename("drc_report", "html")
    path = output_manager.dirs["logs"] / filename

    with open(path, "w") as f:
        f.write(html)

    logger.info(f"DRC HTML report saved: {path}")

    return path


# --------------------------------------------------
# FULL REPORT GENERATION PIPELINE
# --------------------------------------------------
def generate_full_report(drc_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate and save all report formats
    """

    logger.info("Generating full DRC report")

    report = build_report(drc_result)

    text_report = generate_text_report(report)
    html_report = generate_html_report(report)

    json_path = save_json_report(report)
    text_path = save_text_report(text_report)
    html_path = save_html_report(html_report)

    return {
        "report": report,
        "files": {
            "json": str(json_path),
            "text": str(text_path),
            "html": str(html_path)
        }
    }


# --------------------------------------------------
# DEBUG TEST
# --------------------------------------------------
if __name__ == "__main__":
    sample_drc = {
        "status": "FAIL",
        "total_errors": 2,
        "errors": [
            {"type": "OVERLAP", "message": "R1 overlaps C1", "severity": "ERROR"},
            {"type": "TRACE_WIDTH", "message": "Trace too thin", "severity": "WARNING"},
        ]
    }

    result = generate_full_report(sample_drc)

    print("Report generated:")
    print(result)
  
