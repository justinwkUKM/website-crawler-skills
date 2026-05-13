import argparse
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


SCRIPT_DIR = Path(__file__).resolve().parent


def slug_from_url(url):
    parsed = urlparse(url)
    host = parsed.netloc or parsed.path
    host = host.lower().strip()
    host = re.sub(r"[^a-z0-9.-]+", "-", host)
    return host.strip("-") or "target"


def run_cmd(args):
    subprocess.run(args, check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--max-pages", type=int, default=100)
    parser.add_argument("--depth", type=int, default=2)
    parser.add_argument("--reports-dir", default="reports")
    parser.add_argument("--prefix", default="website-risk-report")
    parser.add_argument("--obey-robots", action="store_true")
    args = parser.parse_args()

    reports_dir = Path(args.reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%SZ")
    slug = slug_from_url(args.url)

    crawl_output = reports_dir / f"audit-output-{slug}-{ts}.jsonl"
    findings_output = reports_dir / f"risk-findings-{slug}-{ts}.json"
    report_output = reports_dir / f"{args.prefix}-{slug}-{ts}.md"

    run_cmd(
        [
            "python",
            str(SCRIPT_DIR / "run_audit.py"),
            "--url",
            args.url,
            "--max-pages",
            str(args.max_pages),
            "--depth",
            str(args.depth),
            "--output",
            str(crawl_output),
        ]
        + (["--obey-robots"] if args.obey_robots else [])
    )

    run_cmd(
        [
            "python",
            str(SCRIPT_DIR / "classify_pages.py"),
            "--input",
            str(crawl_output),
            "--output",
            str(findings_output),
        ]
    )

    run_cmd(
        [
            "python",
            str(SCRIPT_DIR / "report.py"),
            "--findings",
            str(findings_output),
            "--target",
            args.url,
            "--max-pages",
            str(args.max_pages),
            "--depth",
            str(args.depth),
            "--robots",
            "true" if args.obey_robots else "false",
            "--output",
            str(report_output),
        ]
    )

    print(str(report_output))


if __name__ == "__main__":
    main()
