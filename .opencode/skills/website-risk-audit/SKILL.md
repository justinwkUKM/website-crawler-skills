---
name: website-risk-audit
description: Crawls public websites with Scrapy and produces an evidence-based compliance risk report for possible fraud, gambling, adult content, phishing, suspicious financial claims, impersonation, malware indicators, or deceptive behavior. Use when the user asks to audit, investigate, classify, screen, scrape, or risk-check a website or domain.
---

# Website Risk Audit

Use this skill to perform a lawful, public-web risk assessment of a website.

## Important rules

- Crawl only public pages.
- Respect robots.txt by default.
- Use rate limits.
- Do not bypass login pages, CAPTCHAs, paywalls, bot protection, or access controls.
- Do not submit forms.
- Do not create accounts.
- Do not make purchases, deposits, bets, or adult-content interactions.
- Do not download suspicious executables.
- Do not collect unnecessary personal data.
- Do not say a website is definitely illegal.
- Report observable risk indicators with evidence, confidence level, and source URLs.

## Refuse or limit the task when

- The user asks to bypass anti-bot systems, CAPTCHAs, login, paywalls, or access controls.
- The user asks to scrape private data.
- The user asks to submit forms or test stolen credentials.
- The user asks to evade detection.
- The user asks to mass-scan many unrelated domains without authorization.
- The user asks for a definitive legal judgment instead of a risk assessment.

## Default crawl limits

- Max pages: 100
- Max depth: 3
- Download delay: 2 seconds
- Respect robots.txt: true

## Workflow

### 1. Confirm target

Identify:
- Target URL or domain
- Jurisdiction, if provided
- Risk categories requested
- Crawl limit, if provided

If not specified, use the default crawl limits.

### 2. Run crawler

```bash
python .opencode/skills/website-risk-audit/scripts/run_audit.py \
  --url TARGET_URL \
  --max-pages 100 \
  --depth 3 \
  --output audit_output.jsonl
```

### 3. Classify pages

```bash
python .opencode/skills/website-risk-audit/scripts/classify_pages.py \
  --input audit_output.jsonl \
  --output risk_findings.json
```

### 4. Generate report

```bash
python .opencode/skills/website-risk-audit/scripts/report.py \
  --findings risk_findings.json \
  --output website-risk-report.md
```

## Required report sections

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

## Wording rules

Do not write:

`This website is illegal.`

Write:

`The crawl found high-risk indicators consistent with gambling promotion, including betting terminology, deposit language, and bonus wagering references. This requires human compliance or legal review.`

## Escalate to human review when

- Risk is high
- Evidence involves regulated activity
- The site requests payment, credentials, identity documents, deposits, or crypto transfers
- The site appears to target minors
- Jurisdiction is unclear
