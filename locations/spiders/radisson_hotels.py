import json
import re
from typing import List

import scrapy

from locations.items import Feature
from locations.structured_data_spider import extract_email, extract_phone
from locations.user_agents import BROWSER_DEFAULT


class RadissonHotelsSpider(scrapy.Spider):
    name = "radisson_hotels"
    allowed_domains = ["www.radissonhotels.com"]
    start_urls = ["https://www.radissonhotels.com/en-us/destination/"]
    brand_mapping = {
        "rdb": ["Radisson Blu", "Q7281341"],
        "rco": ["Radisson Collection", "Q60716706"],
        "pii": ["Park Inn by Radisson", "Q60711675"],
        "rdr": ["Radisson RED", "Q28233721"],
        "cis": ["Country Inn & Suites by Radisson", "Q5177332"],
        "pph": ["Park Plaza Hotels & Resorts", "Q2052550"],
        "art": ["Art’otel", "Q14516231"],
        "rad": ["Radisson", "Q1751979"],
        # I did not find the sub-brand wikidata so I put None.
        "prz": ["Prizeotel", None],
        "rdi": ["Radisson Individuals", None],
        "ri": ["Radisson Individuals", None],
    }
    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": {
            "Accept": "*/*",
            "User-Agent": BROWSER_DEFAULT,
            "Connection": "keep-alive",
            "Accept-Language": "fr-FR",
        },
    }

    def parse(self, response):
        cities = response.xpath('//*[@class="list-destinations--link font-bold"]/@href').getall()
        for city in cities:
            url = "https://www.radissonhotels.com" + city
            yield scrapy.Request(url=url, callback=self.parse_city)

    def parse_city(self, response):
        try:
            hotels: List[dict] = json.loads("[" + re.search(r'({"code":.*{.*})', response.text).group(1) + "]")
        except AttributeError:
            return
        for hotel in hotels:
            item = Feature()
            item["ref"] = hotel.get("code", None)
            item["name"] = hotel.get("name", None)
            if brand := hotel.get("brand", None):
                item["brand"], item["brand_wikidata"] = self.brand_mapping.get(brand, [None, None])
            item["website"] = "https://www.radissonhotels.com" + hotel.get("overviewPath")

            if coordinates := hotel.get("coordinates", None):
                item["lat"] = coordinates.get("latitude", None)
                item["lon"] = coordinates.get("longitude", None)
            item["street_address"] = hotel.get("address", None)
            try:
                yield scrapy.Request(url=item["website"], callback=self.parse_hotel, cb_kwargs={"item": item})
            except Exception:
                pass

    def parse_hotel(self, response, item):
        item["city"] = response.xpath('//*[@class="t-city"]/text()').get()
        item["postcode"] = response.xpath('//*[@class="t-zip"]/text()').get()
        item["country"] = response.xpath('//*[@class="t-country"]/text()').get()
        extract_phone(item, response)
        extract_email(item, response)
        yield item
