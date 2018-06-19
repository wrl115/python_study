# -*- coding: utf-8 -*-
import scrapy
import re
import time
import random
import hashlib
from quotetutorial.items import ScrapyItem
import requests
import os


# 中关村企业信用促进会
class EcpaSpider(scrapy.Spider):
    index = 23
    name = 'ecpa'
    allowed_domains = ['ecpa.org.cn']
    start_urls = ['http://www.ecpa.org.cn/html/tzgg/tongzhigonggao/index.html',
                  'http://www.ecpa.org.cn/html/tzgg/xinwenzhongxin/index.html',
                  'http://www.ecpa.org.cn/html/zczq/zhongguancunzhengce/index.html',
                  'http://www.ecpa.org.cn/html/zczq/beijingshizhengce/index.html',
                  'http://www.ecpa.org.cn/html/zczq/geyuanqu/index.html'
                  ]
    base_url = 'http://www.ecpa.org.cn/'
    category_index = {'tongzhigonggao': '1',
                      'xinwenzhongxin': '2',
                      'zhongguancunzhengce': '3',
                      'beijingshizhengce': '4',
                      'geyuanqu': '5'}
    category_desc = {'tongzhigonggao': '通知公告',
                     'xinwenzhongxin': '新闻中心',
                     'zhongguancunzhengce': '中关村政策',
                     'beijingshizhengce': '北京市政策',
                     'geyuanqu': '各园区'}
    category_desc_arra = ['通知公告', '新闻中心', '中关村政策', '北京市政策', '各园区']

    def parse(self, response):
        print('#############', response.url)
        if response.status == 200:
            if response.url in self.start_urls:
                cate_index = self.start_urls.index(response.url)
                cate = self.category_desc_arra[cate_index]
                id_prefix = str(self.index) + '-' + str(cate_index + 1)
                total_count_desc = response.css('p.total_count::text').extract_first()
                if total_count_desc:
                    total_count = re.match(r'^共(.*?)条记录  当前页次(.*?)/(.*?)页', total_count_desc)
                    for pagenum in range(2, int(total_count.group(3))):
                        url = response.url.replace('index.html', 'index_%s.html' % pagenum)
                        yield scrapy.Request(url, meta={'id_prefix': id_prefix, 'category': cate},
                                             callback=self.parse)
                        time.sleep(random.randint(1, 6))

            else:
                id_prefix = response.meta['id_prefix']
                cate = response.meta['category']

            links = response.css('div.list_r li')
            if links:
                for link in links:
                    url = self.base_url + link.css('a::attr("href")').extract_first()
                    title = link.css('a::attr("title")').extract_first()
                    date = '20' + links[0].css('span::text').extract_first()
                    print(title, date)
                    yield scrapy.Request(url, meta={'id_prefix': id_prefix,
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
            details = response.css('div.main_right_con > div.right_content').extract_first()
            if details:
                dr = re.compile(r'<[^>]+>', re.S)
                dd = dr.sub('', details)
                item['content'] = dd.replace(u'\u3000', '').replace(u'\t', '').replace(u'\r', '').replace(u'\xa0', '').replace(u'\n',
                                                                                                '').strip()
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
            item['attchment_path'] = ''
            item['attchment'] = ''
            # print(item)
            yield item
