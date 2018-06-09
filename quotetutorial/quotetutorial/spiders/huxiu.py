# -*- coding: utf-8 -*-
import scrapy
import re
import time
import random
import hashlib
from quotetutorial.items import ScrapyItem
import requests
import os
import json
from bs4 import BeautifulSoup


# http://www.wendaoxueyuan.com/post/detail/684
class HuxiuSpider(scrapy.Spider):
    index = 24
    name = 'huxiu'
    allowed_domains = ['www.huxiu.com']
    start_urls = ['https://www.huxiu.com/']
    category_index = {'tzgg': '1'}
    category_desc = {'tzgg': '通知公告'}
    url_descs = ['通知公告']

    def parse(self, response):
        print("**********", response.url, response.url in self.start_urls)
        if response.status == 200:
            id_prefix = ''
            cate = ''
            hash_code = ''
            if response.url in self.start_urls:
                cate_index = self.start_urls.index(response.url)
                # id_prefix = str(self.index) + '-' + str(cate_index + 1)
                # cate = self.url_descs[cate_index]
                id_prefix = str(self.index) + '-1'
                cate = '咨询'
                hash_code = response.text[
                            response.text.find('huxiu_hash_code') + 17:response.text.find('huxiu_hash_code') + 49]
                data_inf = response.css('div[data-last_dateline]')
                if data_inf:
                    url = "https://www.huxiu.com/v2_action/article_list"
                    current_page = data_inf.css('::attr("data-cur_page")').extract_first()
                    last_dateline = data_inf.css('::attr("data-last_dateline")').extract_first()
                    nextFormData = {'huxiu_hash_code': hash_code,
                                    'page': str(int(current_page) + 1),
                                    'last_dateline': last_dateline}
                    yield scrapy.FormRequest(url, method='POST', formdata=nextFormData,
                                             meta={'id_prefix': id_prefix, 'category': cate,
                                                   'huxiu_hash_code': hash_code, 'page': str(int(current_page) + 1)},
                                             callback=self.parse_next_list)
                    time.sleep(3)
                else:
                    pass
            else:
                id_prefix = response.meta['id_prefix']
                cate = response.meta['category']
                hash_code = response.meta['huxiu_hash_code']

            info_list = response.css('.mod-info-flow div[data-aid]::attr("data-aid")').extract()
            for info in info_list:
                href = "https://www.huxiu.com/article/" + str(info) + ".html"
            yield scrapy.Request(href, meta={'id_prefix': id_prefix,
                                             'category': cate}, callback=self.parse_content)
            time.sleep(random.randint(1, 6))

    def parse_content(self, response):
        # print("############", response.url)
        if response.status == 200:
            pass

    def parse_next_list(self, response):

        if response.status == 200:
            id_prefix = response.meta['id_prefix']
            cate = response.meta['category']
            hash_code = response.meta['huxiu_hash_code']
            page = response.meta['page']
            # nextFormData = {'huxiu_hash_code': hash_code,
            #                 'page': str(int(current_page) + 1),
            #                 'last_dateline': last_dateline}
            jsobj = json.loads(response.body)
            soup = BeautifulSoup(jsobj['data'], 'lxml')
            for title in soup.select('div[data-aid]'):
                href = "https://www.huxiu.com/article/" + title.get('data-aid') + ".html"
                yield scrapy.Request(href, meta={'id_prefix': id_prefix,
                                                 'category': cate}, callback=self.parse_content)
