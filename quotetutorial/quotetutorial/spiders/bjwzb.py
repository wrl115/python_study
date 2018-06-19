# -*- coding: utf-8 -*-
import scrapy
import re
import time
import random
import hashlib
from quotetutorial.items import ScrapyItem
import requests
import os


# 北京市文资办
class BjwzbSpider(scrapy.Spider):
    index = 28
    name = 'bjwzb'
    allowed_domains = ['www.bjwzb.gov.cn']
    start_urls = ['http://www.bjwzb.gov.cn/xxdt/tzgg/index.html',
                  'http://www.bjwzb.gov.cn/zcfg/gjwhcyfczc/index.html',
                  'http://www.bjwzb.gov.cn/zcfg/bjswhcycyzc/index.html',
                  'http://www.bjwzb.gov.cn/zcfg/jgzd/index.html',
                  'http://www.bjwzb.gov.cn/zcfg/zcjd/index.html']
    category_index = {'tzgg': '1', 'gjwhcyfczc': '2', 'bjswhcycyzc': '3', 'jgzd': '4', 'zcjd': '5'}
    category_desc = {'tzgg': '通知公告', 'gjwhcyfczc': '国家文化产业扶持政策',
                     'bjswhcycyzc': '北京市文化创意产业政策', 'jgzd': '国有文化企业改革和国资监管政策制度', 'zcjd': '政策解读'}
    url_descs = ['通知公告', '国家文化产业扶持政策', '北京市文化创意产业政策', '国有文化企业改革和国资监管政策制度', '政策解读']
    base_url = 'http://www.bjwzb.gov.cn'


    def parse(self, response):
        print("**********", response.url)
        if response.status == 200:
            id_prefix = ''
            cate = ''
            if response.url in self.start_urls:
                cate_index = self.start_urls.index(response.url)
                id_prefix = str(self.index) + '-' + str(cate_index + 1)
                cate = self.url_descs[cate_index]
                page_desc = response.css('div.pageSty::text').extract_first()
                if page_desc:
                    page_info = re.match('.*?每页(.*?)条记录/共(.*?)条记录 当前第(.*?)页/共(.*?)页', page_desc)
                    if page_info:
                        print('总页数：', page_info.group(4))
                        for page in range(1, int(page_info.group(4))):
                            url = response.url[0:response.url.rfind('/') + 1] + 'index_' + str(page) + '.html'
                            print('#########', url)
                            yield scrapy.Request(url, meta={'id_prefix': id_prefix, 'category': cate},
                                                 callback=self.parse)
            else:
                id_prefix = response.meta['id_prefix']
                cate = response.meta['category']

            page_list = response.css('div.listRig#listr ul li')
            for page_info_desc in page_list:
                if page_info_desc.css('a::text'):
                    # print("date: ", page_info_desc.css('span::text').extract_first())
                    date = page_info_desc.css('span::text').extract_first()[1:-1]
                    # print('title:', page_info_desc.css('a::text').extract_first())
                    title = page_info_desc.css('a::text').extract_first()
                    # print('href :', self.base_url+page_info_desc.css('a::attr("href")').extract_first())
                    href = self.base_url + page_info_desc.css('a::attr("href")').extract_first()
                    yield scrapy.Request(href, meta={'id_prefix': id_prefix,
                                                     'category': cate,
                                                     'title': title, 'date': date}, callback=self.parse_content)
                    time.sleep(random.randint(1, 6))

    def parse_content(self, response):
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
            item['content'] = ''
            details = response.css('#Zoom').extract_first()
            if details:
                dr = re.compile(r'<[^>]+>', re.S)
                dd = dr.sub('', details)
                item['content'] = dd.replace(u'\u3000', '').replace(u'\t', '').replace(u'\r', '').replace(u'\xa0',
                                                                                                          '').replace(
                    u'\n', '').strip()
            item['view_count'] = '0'
            item['url'] = response.url
            attach_path_arra = []
            attach_arra = []
            atta_arra = response.css('a[href*=".xls"]') + response.css('a[href*=".doc"]') + response.css(
                'a[href*=".pdf"]')
            for attch in atta_arra:
                save_path = ''
                attch_url = self.base_url + attch.css('::attr("href")').extract_first()
                attach_path_arra.append(attch_url)
                attch_name = attch_url[attch_url.rfind("/") + 1:]
                attach_arra.append(attch_name)
                if attch_name.rfind('.') == -1:
                    save_path = save_path + attch_name + attch_url[attch_url.rfind('.'):]
                else:
                    save_path = save_path + attch_name
                # print('%%%%', save_path)
                # self.download_file(attch_url, save_path)
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
