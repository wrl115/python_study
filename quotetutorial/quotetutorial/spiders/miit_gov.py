# -*- coding: utf-8 -*-
import scrapy


class MiitGovSpider(scrapy.Spider):
    index = 28
    name = 'miit_gov'
    allowed_domains = ['www.miit.gov.cn']
    start_urls = ['http://www.miit.gov.cn/n1146295/n1146557/index.html']
    category_index = {'n1146557': '1'}
    category_desc = {'n1146557': '法律法规'}
    url_descs = ['法律法规']
    base_url = "http://www.bj12330.com"

    def parse(self, response):
        pass
