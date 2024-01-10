import scrapy
from scrapy.selector import Selector
import json

from bs4 import BeautifulSoup


def innertext(selector):
    html = selector.get()
    soup = BeautifulSoup(html, 'html.parser')
    return soup.get_text().strip()


class SpiderSpider(scrapy.Spider):
    name = "spider"
    allowed_domains = ["ai-online.com"]

    def start_requests(self):
        for year, month in zip(range(2003, 2025), range(1, 13)):
            yield scrapy.Request(
                url=f"https://www.ai-online.com/wp-admin/admin-ajax.php?action=newsium_load_more&nonce=0c541007ce&page=1&year={year}&month={month}&day=0",
                callback=self.parse_month, meta={"page": 1, "year": year, "month": month})

    def parse_month(self, response):
        result = json.loads(response.body)
        success = result.get("success")
        more_post = result.get("data").get("more_post")
        content = result.get("data").get("content")
        if success:
            for article in content:
                url = Selector(text=article).css("h4 a").attrib["href"]
                yield scrapy.Request(url=url, callback=self.parse_article)

            if more_post:
                page = response.meta.get("page")
                year = response.meta.get("year")
                month = response.meta.get("month")
                yield scrapy.Request(
                    url=f"https://www.ai-online.com/wp-admin/admin-ajax.php?action=newsium_load_more&nonce=0c541007ce&page={page + 1}&year={year}&month={month}&day=0",
                    callback=self.parse_month, meta={"page": page + 1, "year": year, "month": month})

    def parse_article(self, response):
        title = response.css(".entry-title::text").get()
        date = response.css(".elementor-post-info__item--type-date::text").get().strip()
        content = innertext(response.css('[data-widget_type="theme-post-content.default"]'))
        yield {
            "title": title,
            "date": date,
            "content": content
        }
