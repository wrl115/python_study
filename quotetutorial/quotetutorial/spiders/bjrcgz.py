# -*- coding: utf-8 -*-
import scrapy
import re
import time
import random
import hashlib
from quotetutorial.items import ScrapyItem
import requests
import os


# 北京人才工作网
class BjrcgzSpider(scrapy.Spider):
    index = 18
    name = 'bjrcgz'
    allowed_domains = ['www.bjrcgz.gov.cn']
    start_urls = [
        'http://www.bjrcgz.gov.cn/sword?tid=SwordCMSService_catalog&catalogId=3e328dd7b2484c82a4f7b8562764fc58&themePath=theme1&isGrid=true']
    category_index = {'3e328dd7b2484c82a4f7b8562764fc58': '1'}
    category_desc = {'3e328dd7b2484c82a4f7b8562764fc58': '通知公告'}
    url_descs = ['通知公告']

    def parse(self, response):
        print("**********", response.text)
        # print(len(response.css('div.sGrid_data_div ul').extract()))
        # print(response.css('div.sGrid_data_div ul').extract())
        print('##############', response.css('label#SearchGrid_sGrid_console_totalPage_lable::text').extract_first())
        if response.status == 200:
            id_prefix = ''
            cate = ''
            if response.url in self.start_urls:
                cate_index = self.start_urls.index(response.url)
                id_prefix = str(self.index) + '-' + str(cate_index + 1)
                cate = self.url_descs[cate_index]
                fenye_num = response.css('label#SearchGrid_sGrid_console_totalPage_lable::text').extract_first()
                if fenye_num:
                    for page in range(2, int(fenye_num)+1):
                        nextFormData = {'huxiu_hash_code': hash_code,
                                        'page': str(int(current_page) + 1),
                                        'last_dateline': last_dateline}
                        yield scrapy.FormRequest(url, method='POST', formdata=nextFormData,
                                                 meta={'id_prefix': id_prefix, 'category': cate,
                                                       'huxiu_hash_code': hash_code,
                                                       'page': str(int(current_page) + 1)},
                                                 callback=self.parse_next_list)


            else:
                id_prefix = response.meta['id_prefix']
                cate = response.meta['category']
