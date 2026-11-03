import json
from datetime import datetime, timezone
from pathlib import Path


def generate_report(result, output_path="reports/audit_report.json"):
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "framework": "KAMAR-META-AGENT",
        "result": result
    }

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    return path
