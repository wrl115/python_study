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
import math


class A8610hrSpider(scrapy.Spider):
    index = 19
    name = '8610hr'
    allowed_domains = ['www.8610hr.cn']
    start_urls = ['http://www.8610hr.cn/docs/more/tzgg_2016_index_tzgg/index_morenews1.html',
                  'http://www.8610hr.cn/docs/more/zcfg_2016_yc_index01/index_morenews1.html']
    category_index = {'tzgg': '1', 'zcfg_yc_index01': '2', 'zcfg_cx_index02': '3', 'zcfg_cy_index03': '4',
                      'zcfg_qt_index04': '5'}
    category_desc = {'tzgg': '通知公告', 'zcfg_yc_index01': '政策法规综合', 'zcfg_cx_index02': '政策法规创新',
                     'zcfg_cy_index03': '政策法规创业', 'zcfg_qt_index04': '政策法规其他'}
    url_descs = ['通知公告', '政策法规综合', '政策法规创新', '政策法规创业','政策法规其他']
    base_url = 'http://www.8610hr.cn'

    def parse(self, response):
        print("##########", response.url)
        if response.status == 200:
            id_prefix = ''
            cate = ''
            if response.url in self.start_urls:
                cate_index = self.start_urls.index(response.url)
                id_prefix = str(self.index) + '-' + str(cate_index + 1)
                cate = self.url_descs[cate_index]
                total_count_desc = response.css('div.turnPage form::text').extract_first().strip()
                if total_count_desc:
                    total_count = re.match(r'^共(.*?)条， 列出第(.*?)到第(.*?)条', total_count_desc)
                    if total_count:
                        pages = 2
                        if math.fmod(int(total_count.group(1)), int(total_count.group(3))) == 0:
                            pages = int(int(total_count.group(1)) / int(total_count.group(3)))
                        else:
                            pages = int(int(total_count.group(1)) / int(total_count.group(3))) + 1

                        # pages = int(total_count)/
                        for pagenum in range(2, pages):
                            # print(pagenum)
                            url = response.url.replace('index_morenews1.html', 'index_morenews%s.html' % pagenum)
                            yield scrapy.Request(url, meta={'id_prefix': id_prefix, 'category': cate},
                                                 callback=self.parse)
                            # yield scrapy.FormRequest(
                            #     url=response.url,
                            #     formdata={"page_num": str(pagenum)},
                            #     callback=self.parse
                            # )
                            # time.sleep(random.randint(1, 6))
            else:
                id_prefix = response.meta['id_prefix']
                cate = response.meta['category']

            links = response.css('div.list1 ul li')
            if links:
                for link in links:
                    url = link.css('a::attr("href")').extract_first()
                    title = link.css('a::attr("title")').extract_first()
                    date = links[0].css('span::text').extract_first()
                    print(url, title, date)
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
            source_desc = response.css('div.info-from::text').extract_first()
            if source_desc:
                source_content = re.findall('信息来源：(.*)', source_desc)
                if source_content:
                    item['source'] = source_content[0]

            item['content'] = ''
            details = response.css('div.content_p').extract_first()
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
                attch_name = attch_url[attch_url.rfind("/") + 1:]
                attach_arra.append(attch_name)
                if attch_name.rfind('.') == -1:
                    save_path = save_path + attch_name + attch_url[attch_url.rfind('.'):]
                else:
                    save_path = save_path + attch_name
                self.download_file(attch_url, save_path)
            item['attchment_path'] = ','.join(attach_path_arra)
            item['attchment'] = ','.join(attach_arra)
            print(item)
            # yield item

    def download_file(self, url, local_path):
        if os.path.exists(local_path):
            print("the %s exist" % local_path)
        else:
            print("start download the file", url)
            r = requests.get(url)
            print('down loading status ', r.status_code)
            with open(local_path, "wb") as code:
                code.write(r.content)
