#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <target-url> [max-pages] [depth]"
  exit 1
fi

TARGET_URL="$1"
MAX_PAGES="${2:-100}"
DEPTH="${3:-3}"

mkdir -p reports
TS="$(date +"%Y%m%d-%H%M%S")"

docker run --rm -v "$PWD:/app" website-risk-audit \
  --url "$TARGET_URL" \
  --max-pages "$MAX_PAGES" \
  --depth "$DEPTH" \
  --output "/app/reports/audit_output-${TS}.jsonl"

docker run --rm -v "$PWD:/app" --entrypoint python website-risk-audit \
  /app/.opencode/skills/website-risk-audit/scripts/classify_pages.py \
  --input "/app/reports/audit_output-${TS}.jsonl" \
  --output "/app/reports/risk_findings-${TS}.json"

docker run --rm -v "$PWD:/app" --entrypoint python website-risk-audit \
  /app/.opencode/skills/website-risk-audit/scripts/report.py \
  --findings "/app/reports/risk_findings-${TS}.json" \
  --crawl-data "/app/reports/audit_output-${TS}.jsonl" \
  --target "$TARGET_URL" \
  --max-pages "$MAX_PAGES" \
  --depth "$DEPTH" \
  --robots true \
  --output "/app/reports/website-risk-report-${TS}.md"

echo "Saved report: reports/website-risk-report-${TS}.md"
