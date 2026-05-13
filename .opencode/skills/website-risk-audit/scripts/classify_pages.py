import argparse
import json
import re
from collections import defaultdict


RISK_PATTERNS = {
    "fraud_scam": [
        r"\bguaranteed returns?\b",
        r"\bdouble your money\b",
        r"\brisk[- ]free investment\b",
        r"\bact now\b",
        r"\bwire transfer\b",
        r"\bgift cards?\b",
        r"\bcrypto recovery\b",
        r"\bwithdrawal fee\b",
    ],
    "gambling": [
        r"\bcasino\b",
        r"\bslots?\b",
        r"\bsportsbook\b",
        r"\bbetting\b",
        r"\bodds\b",
        r"\broulette\b",
        r"\bblackjack\b",
        r"\bwagering\b",
        r"\bdeposit bonus\b",
    ],
    "adult_content": [
        r"\bporn\b",
        r"\bxxx\b",
        r"\badult videos?\b",
        r"\bescort\b",
        r"\bcam girls?\b",
        r"\b18\+\b",
    ],
    "phishing_impersonation": [
        r"\bverify your account\b",
        r"\bsuspended account\b",
        r"\bpassword reset\b",
        r"\blogin immediately\b",
        r"\baccount locked\b",
    ],
    "suspicious_financial_crypto": [
        r"\bguaranteed profit\b",
        r"\b100% profit\b",
        r"\bforex signals?\b",
        r"\bcrypto investment\b",
        r"\bno kyc\b",
        r"\bpassive income\b",
    ],
    "malware_suspicious_downloads": [
        r"\bdownload now\b",
        r"\bfree crack\b",
        r"\bkeygen\b",
        r"\bfake update\b",
        r"\bsecurity patch required\b",
    ],
}


def risk_level(match_count):
    if match_count >= 8:
        return "high"
    if match_count >= 3:
        return "medium"
    if match_count >= 1:
        return "low"
    return "none"


def confidence_level(match_count):
    if match_count >= 8:
        return "high"
    if match_count >= 3:
        return "medium"
    return "low"


def snippet_around(text, start, end, window=160):
    left = max(start - window, 0)
    right = min(end + window, len(text))
    return " ".join(text[left:right].split())


def classify_page(page):
    text = " ".join(
        [
            page.get("title") or "",
            page.get("meta_description") or "",
            " ".join(page.get("h1") or []),
            page.get("visible_text") or "",
        ]
    )

    lowered = text.lower()
    category_findings = defaultdict(list)

    for category, patterns in RISK_PATTERNS.items():
        for pattern in patterns:
            for match in re.finditer(pattern, lowered, re.IGNORECASE):
                category_findings[category].append(
                    {
                        "pattern": pattern,
                        "snippet": snippet_around(text, match.start(), match.end()),
                    }
                )

    result = {
        "url": page.get("url"),
        "status": page.get("status"),
        "findings": {},
        "forms": page.get("forms", []),
    }

    for category, findings in category_findings.items():
        matches = len(findings)
        result["findings"][category] = {
            "risk": risk_level(matches),
            "confidence": confidence_level(matches),
            "match_count": matches,
            "evidence": findings[:10],
        }

    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    pages_with_findings = []

    with open(args.input, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue

            page = json.loads(line)
            result = classify_page(page)

            if result["findings"]:
                pages_with_findings.append(result)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(pages_with_findings, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
