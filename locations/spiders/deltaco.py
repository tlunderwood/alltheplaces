# -*- coding: utf-8 -*-
import re
import json

import scrapy

from locations.items import GeojsonPointItem

class del_taco(scrapy.Spider):
    #download_delay = 0.2
    name = "del_taco"
    item_attributes = {'brand': "Del Taco"}
    allowed_domains = ["deltaco.com"]
    start_urls = (
        'https://locations.deltaco.com/us',
    )

    def parse(self, response):
        urls = response.xpath('//li[@class="Directory-listItem"]//a/@href').extract()
        for url in urls:
            urlstart = url[:5]
            yield scrapy.Request(response.urljoin(urlstart), callback=self.parse_state)

    def parse_state(self, response):
        urls = response.xpath('//li[@class="Directory-listItem"]//a/@href').extract()
        for url in urls:
            urlstate = url.split('/')[2]
            urlcity = url.split('/')[3]
            parsedurl = urlstate + '/' + urlcity
            yield scrapy.Request(response.urljoin(parsedurl), callback=self.parse_city)

    def parse_city(self, response):
        urls = response.xpath('//h2[@class="Teaser-title"]//a/@href').extract()
        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_store)

    def parse_store(self, response):

        properties = {
            'ref': response.url,
            'name': 'Del Taco',
            'addr_full': response.xpath('//span[@class="Address-field Address-line1"]/text()').extract_first(),
            'city': response.xpath('//span[@class="Address-field Address-city"]/text()').extract_first(),
            'state': response.xpath('//*[@id="address"]/div[2]/abbr//text()').extract_first(),
            'postcode': response.xpath('//span[@class="Address-field Address-postalCode"]//text()').extract_first(),
            'country': 'US',
            'phone': response.xpath('//a[@class="Phone-link"]//text()').extract_first(),
            'lat': float(response.xpath('normalize-space(//meta[@itemprop="latitude"]/@content)').extract_first()),
            'lon': float(response.xpath('normalize-space(//meta[@itemprop="longitude"]/@content)').extract_first()),
        }

        yield GeojsonPointItem(**properties)
