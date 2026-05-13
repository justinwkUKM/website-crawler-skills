import argparse
import json
from collections import defaultdict


RISK_RANK = {
    "none": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
}

CONFIDENCE_RANK = {
    "low": 1,
    "medium": 2,
    "high": 3,
}


def overall_risk(category_summary):
    highest = "none"
    for data in category_summary.values():
        if RISK_RANK[data["risk"]] > RISK_RANK[highest]:
            highest = data["risk"]
    return highest


def overall_confidence(category_summary):
    highest = "low"
    for data in category_summary.values():
        if CONFIDENCE_RANK[data["confidence"]] > CONFIDENCE_RANK[highest]:
            highest = data["confidence"]
    return highest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--findings", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--target", default="unknown")
    parser.add_argument("--max-pages", type=int, default=100)
    parser.add_argument("--depth", type=int, default=3)
    parser.add_argument("--robots", default="true")
    parser.add_argument("--crawl-data", default="")
    args = parser.parse_args()

    with open(args.findings, "r", encoding="utf-8") as f:
        findings = json.load(f)

    crawl_pages = []
    if args.crawl_data:
        with open(args.crawl_data, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                crawl_pages.append(json.loads(line))

    category_summary = defaultdict(
        lambda: {
            "risk": "none",
            "confidence": "low",
            "pages": 0,
            "matches": 0,
            "evidence": [],
        }
    )

    for page in findings:
        for category, data in page.get("findings", {}).items():
            category_summary[category]["pages"] += 1
            category_summary[category]["matches"] += data.get("match_count", 0)

            if RISK_RANK[data["risk"]] > RISK_RANK[category_summary[category]["risk"]]:
                category_summary[category]["risk"] = data["risk"]

            if (
                CONFIDENCE_RANK[data.get("confidence", "low")]
                > CONFIDENCE_RANK[category_summary[category]["confidence"]]
            ):
                category_summary[category]["confidence"] = data.get("confidence", "low")

            for evidence in data.get("evidence", [])[:3]:
                category_summary[category]["evidence"].append(
                    {
                        "url": page.get("url"),
                        "pattern": evidence.get("pattern"),
                        "snippet": evidence.get("snippet"),
                        "reason": f"Matched pattern {evidence.get('pattern')}",
                    }
                )

    report_lines = []
    report_lines.append("# Website Risk Audit Report")
    report_lines.append("")
    report_lines.append("## Target")
    report_lines.append("")
    report_lines.append(f"- URL/Domain: {args.target}")
    report_lines.append("")
    report_lines.append("## Crawl settings")
    report_lines.append("")
    report_lines.append(f"- Max pages: {args.max_pages}")
    report_lines.append(f"- Max depth: {args.depth}")
    report_lines.append(f"- Respect robots.txt: {args.robots}")
    report_lines.append("")
    report_lines.append("## Executive summary")
    report_lines.append("")
    report_lines.append(
        "This report identifies public-web risk indicators only. "
        "It is not a legal conclusion and should be reviewed by a qualified human reviewer."
    )
    report_lines.append("")
    report_lines.append("## Overall risk level")
    report_lines.append("")
    report_lines.append(f"- Risk: **{overall_risk(category_summary).upper()}**")
    report_lines.append(f"- Confidence: **{overall_confidence(category_summary).upper()}**")
    report_lines.append("")
    report_lines.append("## Category-level findings")
    report_lines.append("")

    if not category_summary:
        report_lines.append("No configured high-signal risk indicators were found in the crawled pages.")
        report_lines.append("")
    else:
        for category, data in sorted(category_summary.items()):
            report_lines.append(f"### {category.replace('_', ' ').title()}")
            report_lines.append("")
            report_lines.append(f"- Risk: **{data['risk'].upper()}**")
            report_lines.append(f"- Confidence: **{data['confidence'].upper()}**")
            report_lines.append(f"- Pages with signals: {data['pages']}")
            report_lines.append(f"- Total matches: {data['matches']}")
            report_lines.append("")

    status_groups = {
        "redirects": [],
        "forbidden": [],
        "not_found": [],
        "other_errors": [],
    }
    if crawl_pages:
        seen_urls = set()
        seen_redirects = set()
        for page in crawl_pages:
            url = page.get("url")
            status = page.get("status")
            if not url or status is None:
                continue

            if status == 403 and url not in seen_urls:
                status_groups["forbidden"].append(url)
                seen_urls.add(url)
            elif status == 404 and url not in seen_urls:
                status_groups["not_found"].append(url)
                seen_urls.add(url)
            elif 400 <= status < 600 and url not in seen_urls:
                status_groups["other_errors"].append(f"{status} {url}")
                seen_urls.add(url)

            for hop in page.get("redirect_chain", []):
                source = hop.get("from")
                dest = hop.get("to")
                if not source or not dest:
                    continue
                key = (source, dest)
                if key in seen_redirects:
                    continue
                seen_redirects.add(key)
                status_groups["redirects"].append(f"{source} -> {dest}")

    report_lines.append("## Crawl status summary")
    report_lines.append("")
    report_lines.append(f"- Redirect chains: {len(status_groups['redirects'])}")
    report_lines.append(f"- HTTP 403 pages: {len(status_groups['forbidden'])}")
    report_lines.append(f"- HTTP 404 pages: {len(status_groups['not_found'])}")
    report_lines.append(f"- Other HTTP 4xx/5xx pages: {len(status_groups['other_errors'])}")
    report_lines.append("")

    report_lines.append("## Redirects (3xx)")
    report_lines.append("")
    if status_groups["redirects"]:
        for item in status_groups["redirects"]:
            report_lines.append(f"- {item}")
    else:
        report_lines.append("- No redirects observed.")
    report_lines.append("")

    report_lines.append("## Forbidden pages (403)")
    report_lines.append("")
    if status_groups["forbidden"]:
        for item in status_groups["forbidden"]:
            report_lines.append(f"- {item}")
    else:
        report_lines.append("- No HTTP 403 pages observed.")
    report_lines.append("")

    report_lines.append("## Not found pages (404)")
    report_lines.append("")
    if status_groups["not_found"]:
        for item in status_groups["not_found"]:
            report_lines.append(f"- {item}")
    else:
        report_lines.append("- No HTTP 404 pages observed.")
    report_lines.append("")

    report_lines.append("## Other HTTP errors (4xx/5xx)")
    report_lines.append("")
    if status_groups["other_errors"]:
        for item in status_groups["other_errors"]:
            report_lines.append(f"- {item}")
    else:
        report_lines.append("- No other HTTP 4xx/5xx pages observed.")
    report_lines.append("")

    report_lines.append("## Evidence snippets")
    report_lines.append("")
    has_evidence = False
    for _, data in sorted(category_summary.items()):
        for item in data["evidence"][:8]:
            has_evidence = True
            report_lines.append(f"- Snippet: {item['snippet']}")
            report_lines.append(f"  - Reason: {item['reason']}")
            report_lines.append("")
    if not has_evidence:
        report_lines.append("- No evidence snippets were captured.")
        report_lines.append("")

    report_lines.append("## Source URLs")
    report_lines.append("")
    urls = sorted({page.get("url") for page in findings if page.get("url")})
    if urls:
        for url in urls:
            report_lines.append(f"- {url}")
    else:
        report_lines.append("- No URLs with findings.")
    report_lines.append("")

    report_lines.append("## Confidence levels")
    report_lines.append("")
    if category_summary:
        for category, data in sorted(category_summary.items()):
            report_lines.append(
                f"- {category.replace('_', ' ').title()}: {data['confidence'].upper()}"
            )
    else:
        report_lines.append("- No category confidence levels available.")
    report_lines.append("")

    report_lines.append("## Limitations")
    report_lines.append("")
    report_lines.append("- Crawl covered public pages only.")
    report_lines.append("- No login, payment, account creation, or form submission was performed.")
    report_lines.append("- Some content may be dynamic, geo-specific, blocked, or unavailable to the crawler.")
    report_lines.append("- Keyword signals can produce false positives and false negatives.")
    report_lines.append("")
    report_lines.append("## Recommended human review steps")
    report_lines.append("")
    report_lines.append("- Review high-risk URLs manually.")
    report_lines.append("- Check business registration, licensing, and jurisdiction-specific rules.")
    report_lines.append("- Preserve screenshots or archived evidence if needed.")
    report_lines.append("- Escalate regulated categories to compliance or legal review.")

    with open(args.output, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))


if __name__ == "__main__":
    main()
