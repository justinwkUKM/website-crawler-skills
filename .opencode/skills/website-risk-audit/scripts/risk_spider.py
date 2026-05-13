from urllib.parse import urlparse

import scrapy


class RiskSpider(scrapy.Spider):
    name = "risk_spider"
    handle_httpstatus_all = True

    def __init__(self, start_url=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not start_url:
            raise ValueError("start_url is required")

        self.start_urls = [start_url]
        parsed = urlparse(start_url)
        domain = parsed.hostname or parsed.netloc
        if not domain:
            raise ValueError("start_url must include a valid hostname")
        self.allowed_domains = [domain]

    def parse(self, response):
        text_parts = response.css("body ::text").getall()
        visible_text = " ".join(t.strip() for t in text_parts if t.strip())

        redirect_chain = []
        redirect_urls = response.meta.get("redirect_urls") or []
        if redirect_urls:
            full_chain = list(redirect_urls) + [response.url]
            for idx in range(len(full_chain) - 1):
                redirect_chain.append(
                    {
                        "from": full_chain[idx],
                        "to": full_chain[idx + 1],
                    }
                )

        forms = []
        for form in response.css("form"):
            forms.append(
                {
                    "action": form.css("::attr(action)").get(),
                    "method": form.css("::attr(method)").get(),
                    "input_names": form.css("input::attr(name)").getall(),
                    "input_types": form.css("input::attr(type)").getall(),
                }
            )

        yield {
            "url": response.url,
            "status": response.status,
            "referer": response.request.headers.get("Referer", b"").decode("utf-8", "ignore"),
            "title": response.css("title::text").get(),
            "meta_description": response.css("meta[name='description']::attr(content)").get(),
            "h1": response.css("h1::text").getall(),
            "visible_text": visible_text[:30000],
            "links": response.css("a::attr(href)").getall()[:200],
            "forms": forms,
            "redirect_chain": redirect_chain,
        }

        for href in response.css("a::attr(href)").getall():
            if not href:
                continue
            cleaned = href.strip()
            lowered = cleaned.lower()
            if (
                lowered.startswith("javascript:")
                or lowered.startswith("mailto:")
                or lowered.startswith("tel:")
                or lowered.startswith("#")
            ):
                continue
            yield response.follow(cleaned, callback=self.parse)
