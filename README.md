# Website Risk Audit Skill (OpenCode + Scrapy)

This project contains an OpenCode skill that crawls public web pages and generates an evidence-based risk report for:

- fraud/scam indicators
- gambling indicators
- adult-content indicators
- phishing/impersonation indicators
- suspicious financial/crypto claims
- malware/suspicious download indicators

The output is compliance triage, not a legal conclusion.

## What the scan does

1. **Crawl public pages only**
   - Uses Scrapy with `robots.txt` enabled by default
   - Uses rate limiting and crawl caps (depth/page count)
   - Does not log in, submit forms, bypass controls, or scrape private data
2. **Extract evidence** per page
   - URL, status, title, description, headings, visible text, links, forms
3. **Classify risk indicators**
   - Regex-based keyword matching by risk category
   - Produces category-level `risk` and `confidence`
4. **Generate Markdown report**
   - Includes categories explicitly, evidence snippets, source URLs, limitations, and review steps

## Project structure

```text
.opencode/skills/website-risk-audit/
  SKILL.md
  scripts/
    run_audit.py
    risk_spider.py
    classify_pages.py
    report.py
  references/
    risk-taxonomy.md
  assets/
    report-template.md
Dockerfile
requirements.txt
```

## Docker usage

Build image:

```bash
docker build -t website-risk-audit .
```

Run crawl:

```bash
docker run --rm -v "$PWD:/app" website-risk-audit \
  --url https://example.com \
  --max-pages 10 \
  --depth 1 \
  --output /app/audit_output.jsonl
```

Run classification:

```bash
docker run --rm -v "$PWD:/app" --entrypoint python website-risk-audit \
  /app/.opencode/skills/website-risk-audit/scripts/classify_pages.py \
  --input /app/audit_output.jsonl \
  --output /app/risk_findings.json
```

Generate report:

```bash
docker run --rm -v "$PWD:/app" --entrypoint python website-risk-audit \
  /app/.opencode/skills/website-risk-audit/scripts/report.py \
  --findings /app/risk_findings.json \
  --target https://example.com \
  --max-pages 10 \
  --depth 1 \
  --robots true \
  --output /app/website-risk-report.md
```

Or run the full pipeline with automatic timestamped outputs in `reports/`:

```bash
./scan_in_docker.sh "https://example.com" 100 3
```

This creates:

- `reports/audit_output-YYYYMMDD-HHMMSS.jsonl`
- `reports/risk_findings-YYYYMMDD-HHMMSS.json`
- `reports/website-risk-report-YYYYMMDD-HHMMSS.md`

## Local setup

1. Create and activate a virtual environment.
2. Install dependencies from `requirements.txt`.
3. Run the full pipeline script with a target URL.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Full run with timestamped reports in reports/
./scan_in_docker.sh "https://example.com" 100 3
```

If you want to run scripts directly without Docker, use the Python entry points in `.opencode/skills/website-risk-audit/scripts/`.

## Contributing

- Keep crawler behavior aligned with guardrails (public pages only, robots respected).
- Do not commit generated scan outputs (`reports/`) or local environment files.
- Include clear reproduction steps in pull requests for any behavior changes.
- Prefer small, focused commits with descriptive messages.

## Files produced

- `audit_output.jsonl`: raw crawled page evidence
- `risk_findings.json`: page-level category findings
- `website-risk-report.md`: final human-readable report

## How the report looks

The report includes these sections:

- Target
- Crawl settings
- Executive summary
- Overall risk level
- Category-level findings
- Evidence snippets
- Source URLs
- Confidence levels
- Limitations
- Recommended human review steps

Each category is explicitly listed under **Category-level findings** with:

- Risk (LOW/MEDIUM/HIGH)
- Confidence (LOW/MEDIUM/HIGH)
- Pages with signals
- Total matches

Example shape:

```md
## Overall risk level

- Risk: **MEDIUM**
- Confidence: **MEDIUM**

## Category-level findings

### Gambling

- Risk: **HIGH**
- Confidence: **MEDIUM**
- Pages with signals: 2
- Total matches: 9
```

## OpenCode skill discovery

This skill is defined in:

- `.opencode/skills/website-risk-audit/SKILL.md`

Use OpenCode from project root and prompt it to use `website-risk-audit` for a target domain.

## Guardrails

- Crawl only public pages
- Respect `robots.txt`
- No bypassing anti-bot/access controls
- No form submissions or credential testing
- No definitive legal conclusions

## Notes

- Keyword-based detection can produce false positives/false negatives.
- High-risk findings should be escalated for human compliance/legal review.
