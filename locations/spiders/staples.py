import re

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature
from locations.spiders.vapestore_gb import clean_address


class StaplesSpider(scrapy.Spider):
    name = "staples"
    item_attributes = {"brand": "Staples", "brand_wikidata": "Q785943"}
    allowed_domains = ["stores.staples.com"]
    start_urls = ("https://stores.staples.com/",)

    def parse_hours(self, elements):
        opening_hours = OpeningHours()

        for elem in elements:
            day = elem.xpath('.//td[@class="c-hours-details-row-day"]/text()').extract_first()
            intervals = elem.xpath('.//td[@class="c-hours-details-row-intervals"]')

            if intervals.xpath("./text()").extract_first() == "Closed":
                continue
            if intervals.xpath("./span/text()").extract_first() == "Open 24 hours":
                opening_hours.add_range(day=day, open_time="0:00", close_time="23:59")
            else:
                start_time = elem.xpath(
                    './/span[@class="c-hours-details-row-intervals-instance-open"]/text()'
                ).extract_first()
                end_time = elem.xpath(
                    './/span[@class="c-hours-details-row-intervals-instance-close"]/text()'
                ).extract_first()
                opening_hours.add_range(day=day, open_time=start_time, close_time=end_time, time_format="%I:%M %p")

        return opening_hours

    def parse_store(self, response):
        ref = re.search(r".+/(.+)$", response.url).group(1)

        address1 = response.xpath('//span[@class="c-address-street-1"]/text()').extract_first()
        address2 = response.xpath('//span[@class="c-address-street-2"]/text()').extract_first() or ""

        properties = {
            "street_address": clean_address([address1, address2]),
            "phone": response.xpath('//span[@itemprop="telephone"]/text()').extract_first(),
            "city": response.xpath('//span[@class="c-address-city"]/text()').extract_first(),
            "state": response.xpath('//abbr[@itemprop="addressRegion"]/text()').extract_first(),
            "postcode": response.xpath('//span[@itemprop="postalCode"]/text()').extract_first(),
            "country": response.xpath('//abbr[@itemprop="addressCountry"]/text()').extract_first(),
            "ref": ref,
            "website": response.url,
            "lat": float(response.xpath('//meta[@itemprop="latitude"]/@content').extract_first()),
            "lon": float(response.xpath('//meta[@itemprop="longitude"]/@content').extract_first()),
            "name": response.xpath('//h1[@itemprop="name"]/text()').extract_first(),
        }

        hours = self.parse_hours(response.xpath('//table[@class="c-hours-details"]//tbody/tr'))

        if hours:
            properties["opening_hours"] = hours

        yield Feature(**properties)

    def parse(self, response):
        urls = response.xpath('//a[@class="Directory-listLink"]/@href').extract()
        is_store_list = response.xpath('//section[contains(@class,"LocationList")]').extract()

        if not urls and is_store_list:
            urls = response.xpath('//a[contains(@class,"Teaser-titleLink")]/@href').extract()

        for url in urls:
            if re.search(r".{2}/.+/.+", url):
                yield scrapy.Request(response.urljoin(url), callback=self.parse_store)
            else:
                yield scrapy.Request(response.urljoin(url))
