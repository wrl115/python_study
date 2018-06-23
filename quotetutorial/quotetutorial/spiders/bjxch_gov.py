# -*- coding: utf-8 -*-
import scrapy
import re
import time
import random
import hashlib
from quotetutorial.items import ScrapyItem
import requests
import os
import io
import sys


# 西城区政府的网站
class BjxchGovSpider(scrapy.Spider):
    index = 14
    name = 'bjxch_gov'
    allowed_domains = ['www.bjxch.gov.cn']
    start_urls = ['http://www.bjxch.gov.cn/xxgk/tzgg/pnpagenumpv1.html']
    category_index = {'tzgg': '1'}
    category_desc = {'tzgg': '通知公告'}
    url_descs = ['通知公告']
    base_url = 'http://www.bjxch.gov.cn'

    def parse(self, response):
        print("##########", response.url)
        if response.status == 200:
            id_prefix = ''
            cate = ''
            if response.url in self.start_urls:
                cate_index = self.start_urls.index(response.url)
                id_prefix = str(self.index) + '-' + str(cate_index + 1)
                cate = self.url_descs[cate_index]
                total_count_desc = response.css('ul.pagination li:last-child>a::text').extract_first()
                if total_count_desc:
                    total_num = re.findall('共(.*?)页', total_count_desc)
                    if total_num:
                        for page_num in range(2, int(total_num[0].strip())+1):
                            url = response.url[0:response.url.rfind('/')+1]+'pnpagenumpv%s.html'% page_num
                            yield scrapy.Request(url, meta={'id_prefix': id_prefix, 'category': cate},
                                                 callback=self.parse)
                    time.sleep(random.randint(1, 6))
            else:
                id_prefix = response.meta['id_prefix']
                cate = response.meta['category']

            links = response.css("div.list > div.zt")
            for link in links:
                href = link.css('a::attr("href")').extract_first()
                if href.startswith('http'):
                    url = href
                else:
                    url = self.base_url + href
                title = link.css('a span::text').extract_first().strip()
                date = link.css('div.time::text').extract_first().strip()
                print(url, title)
                if url:
                    yield scrapy.Request(url, meta={'id_prefix': id_prefix,
                                                    'category': cate,
                                                    'title': title, 'date': date}, callback=self.parse_content)
                    time.sleep(random.randint(1, 6))
    def parse_content(self, response):
        if response.status == 200:
            print("^^^^^^", response.url)
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
            #     # div.detail  div.detail_con>div.TRS_Editor
                item['content'] = ''
                details = response.css('div.xiangqing').extract_first()
                if details:
                    dr = re.compile(r'<[^>]+>', re.S)
                    dd = dr.sub('', details)
                    item['content'] = dd.replace(u'\u3000', '').replace(u'\t', '').replace(u'\r', '').replace(u'\xa0',
                                                                                                              '').replace(
                        u'\n',
                        '').strip()
                item['view_count'] = '0'
                item['url'] = response.url
                attach_path_arra = []
                attach_arra = []
                atta_arra = response.css('a[href*=".xls"]') + response.css('a[href*=".doc"]') + response.css(
                    'a[href*=".pdf"]') + response.css('a[href*=".zip"]') + response.css('a[href*=".rar"]')
                for attch in atta_arra:
                    save_path = ''
                    attch_url = self.base_url + attch.css('::attr("href")').extract_first()
                    attach_path_arra.append(attch_url)
                    attch_name = attch.css('::text').extract_first()
                    if not attch_name:
                        attch_name = attch_url[attch_url.rfind("/") + 1:]
                    attach_arra.append(attch_name)
                    if attch_name.rfind('.') == -1:
                        save_path = save_path + attch_name + attch_url[attch_url.rfind('.'):]
                    else:
                        save_path = save_path + attch_name
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
