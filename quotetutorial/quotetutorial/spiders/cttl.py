# -*- coding: utf-8 -*-
import scrapy
import re
import time
import random
import hashlib
from quotetutorial.items import ScrapyItem
import requests
import os


class CttlSpider(scrapy.Spider):
    name = 'cttl'
    index = 6

    allowed_domains = ['www.cttl.cn']
    start_urls = ['http://www.cttl.cn/news/index.htm']
    category_index = {'news': '1'}
    category_desc = {'news': '新闻动态'}
    url_descs = ['新闻动态']
    md5 = hashlib.md5()

    def parse(self, response):

        if response.status == 200:
            id_prefix = ''
            cate = ''
            if response.url.endswith('index.htm'):
                page_tail = response.css('.flickr a#pagenav_tail')
                if page_tail:
                    page_num = int(page_tail.css('::attr("href")').re('index[_](\d?).htm')[0]) + 1
                    for page in range(1, page_num):
                        url = response.url.replace('index.htm', 'index_%s.htm' % page)
                        cate_index = self.start_urls.indexof(response.url)
                        id_prefix = str(self.index) + '-' + str(cate_index + 1)
                        cate = self.url_descs[cate_index]
                        print('*********', url)
                        yield scrapy.Request(url, meta={'id_prefix': id_prefix, 'category': cate}, callback=self.parse)
                        time.sleep(random.randint(1, 6))
                else:
                    pass
            content_table = response.xpath('/html/body/div/table[3]/tr/td[2]/div/table/tr/td/table')
            if content_table:
                content_trs = content_table.css('tr:nth-child(2n)')
                for content_tr in content_trs:
                    if not id_prefix:
                        id_prefix = response.meta['id_prefix']
                    if not cate:
                        cate = response.meta['category']

                    print('连接：', content_tr.css('a::attr("href")').extract_first())
                    print('标题：', content_tr.css('a::attr("title")').extract_first())
                    print('发布日期', content_tr.css('td span::text').extract_first())
