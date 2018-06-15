# -*- coding: utf-8 -*-
import scrapy
import re
import time
import random
import hashlib
from quotetutorial.items import ScrapyItem
import requests
import os


# 北京市西城区金融服务办公室
class BjxchSpider(scrapy.Spider):
    index = 9
    name = 'bjxch'
    allowed_domains = ['jrb.bjxch.gov.cn']
    base_url = 'http://jrb.bjxch.gov.cn'
    start_urls = ['http://jrb.bjxch.gov.cn/tzgg.html']
    category_index = {'tzgg': '1'}
    category_desc = {'tzgg': '通知公告'}
    url_descs = ['通知公告']


    def parse(self, response):
        if response.status == 200:
            id_prefix = ''
            cate = ''
            if response.url in self.start_urls:
                cate_index = self.start_urls.index(response.url)
                id_prefix = str(self.index) + '-' + str(cate_index + 1)
                cate = self.url_descs[cate_index]
                next_page = response.css('.page_next::attr("href")').extract_first()
                if next_page:
                    yield scrapy.Request(self.base_url + next_page, meta={'id_prefix': id_prefix, 'category': cate},
                                         callback=self.parse)
            else:
                id_prefix = response.meta['id_prefix']
                cate = response.meta['category']

            infolist_selectors = response.css('.infolist ul li')
            for info_selector in infolist_selectors:
                href = self.base_url + info_selector.css('a::attr("href")').extract_first()
                title = info_selector.css('a::text').extract_first()
                date = info_selector.css('span::text').extract_first()
                print(href, ':', title, '::', date)
                yield scrapy.Request(href, meta={'id_prefix': id_prefix,
                                                 'category': cate,
                                                 'title': title, 'date': date}, callback=self.parse_content)

    def parse_content(self, response):
        if response.status == 200:
            md5 = hashlib.md5()
            md5.update(response.url.encode(encoding='utf-8'))
            item = ScrapyItem()
            id_prefix = response.meta['id_prefix']
            item['id'] = id_prefix + "-" + md5.hexdigest()
            category = response.meta['category']
            item['category'] = category
            item['title'] = response.meta['title']
            item['published_date'] = response.meta['date']
            item['source'] = ''
            content_sec = response.css('.xiangqing').extract_first()
            item['content'] = ''
            if content_sec:
                dr = re.compile(r'<[^>]+>', re.S)
                dd = dr.sub('', content_sec)
                if dd:
                    item['content'] = dd.replace(u'\u3000', '').replace(u'\r\n', '').replace(u'\t', '').replace(u'\xa0',
                                                                                                                '').strip()

            item['view_count'] = '0'
            item['url'] = response.url

            attach_path_arra = []
            attach_arra = []

            attchs = response.css('img[src*="doc.gif"] ~ a')
            for attch in attchs:
                save_path = ''
                attch_url = self.base_url + attch.css('::attr("href")').extract_first()
                attach_path_arra.append(attch_url)
                attch_name = attch.css('::text').extract_first()
                attach_arra.append(attch_name)
                if attch_name.rfind('.') == -1:
                    save_path = save_path + attch_name + attch_url[attch_url.rfind('.'):]
                else:
                    save_path = save_path + attch_name
                # print('%%%%', save_path)
                self.download_file(attch_url, save_path)

            item['attchment_path'] = ','.join(attach_path_arra)
            item['attchment'] = ','.join(attach_arra)
            # print(item)
            yield item

    def download_file(self, url, local_path):
        if os.path.exists(local_path):
            print("the %s exist" % local_path)
        else:
            print("start download the file", url)
            r = requests.get(url)
            print('down loading status ', r.status_code)
            with open(local_path, "wb") as code:
                code.write(r.content)
