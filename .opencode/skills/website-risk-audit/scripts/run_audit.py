import argparse

from scrapy.crawler import CrawlerProcess

from risk_spider import RiskSpider


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--max-pages", type=int, default=100)
    parser.add_argument("--depth", type=int, default=3)
    parser.add_argument("--output", default="audit_output.jsonl")
    parser.add_argument("--obey-robots", action="store_true")
    args = parser.parse_args()

    process = CrawlerProcess(
        settings={
            "FEEDS": {
                args.output: {
                    "format": "jsonlines",
                    "encoding": "utf8",
                    "overwrite": True,
                }
            },
            "ROBOTSTXT_OBEY": args.obey_robots,
            "USER_AGENT": "WebsiteRiskAuditBot/0.1 (+compliance-review)",
            "DOWNLOAD_DELAY": 2,
            "AUTOTHROTTLE_ENABLED": True,
            "DEPTH_LIMIT": args.depth,
            "CLOSESPIDER_PAGECOUNT": args.max_pages,
            "HTTPERROR_ALLOW_ALL": True,
            "LOG_LEVEL": "INFO",
        }
    )

    process.crawl(RiskSpider, start_url=args.url)
    process.start()


if __name__ == "__main__":
    main()
