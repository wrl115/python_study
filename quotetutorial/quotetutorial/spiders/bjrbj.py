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


# 北京市人力资源和社会保障局
class BjrbjSpider(scrapy.Spider):
    index = 15
    name = 'bjrbj'
    allowed_domains = ['www.bjrbj.gov.cn']
    start_urls = ['http://www.bjrbj.gov.cn/xxgk/gsgg/index.html',
                  'http://www.bjrbj.gov.cn/xxgk/zcfg/index.html',
                  'http://www.bjrbj.gov.cn/xxgk/zcjd/index.html',
                  'http://www.bjrbj.gov.cn/xxgk/gzdt/index.html',
                  'http://www.bjrbj.gov.cn/xxgk/ghjh/index.html']
    category_index = {'gsgg': '1', 'zcfg': '2', 'zcjd': '3', 'gzdt': '4', 'ghjh': '5'}
    category_desc = {'gsgg': '通知公告-公示公告', 'zcfg': '政策法规-新法速递', 'zcjd': '政策法规-政策解读', 'gzdt': '工作动态', 'ghjh': '规则计划'}
    url_descs = ['通知公告-公示公告', '政策法规-新法速递', '政策法规-政策解读', '工作动态', '规则计划']
    base_url = 'http://rlsbj.bjxch.gov.cn'

    def parse(self, response):
        print("##########", response.url)
        if response.status == 200:
            id_prefix = ''
            cate = ''
            if response.url in self.start_urls:
                cate_index = self.start_urls.index(response.url)
                id_prefix = str(self.index) + '-' + str(cate_index + 1)
                cate = self.url_descs[cate_index]

                total_count_desc = response.css('div.pages >  script').extract_first()
                # if total_count_desc:
                #     total_count = re.findall('countPage =(.*?)\/\/', total_count_desc)
                #     if total_count:
                #         for page_num in range(1, int(total_count[0].strip())):
                #             url = response.url.replace('index.html', 'index_%s.html' % page_num)
                #             yield scrapy.Request(url, meta={'id_prefix': id_prefix, 'category': cate},
                #                                  callback=self.parse)
            else:
                id_prefix = response.meta['id_prefix']
                cate = response.meta['category']

            links = response.css('div.conright > div.con > ul li')
            for link in links:
                url = response.url[0:response.url.rfind('/')] + link.css('a::attr("href")').extract_first()[1:]
                title = link.css('a::text').extract_first()
                if title:
                    print(url, title)
                    yield scrapy.Request(url, meta={'id_prefix': id_prefix,
                                                    'category': cate,
                                                    'title': title}, callback=self.parse_content)
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

            item['published_date'] = ''
            date = response.css('div.detail  div.info >span::text').extract_first()
            if date:
                item['published_date'] = date.strip()
            item['source'] = ''
            # div.detail  div.detail_con>div.TRS_Editor
            item['content'] = ''
            details = response.css('div.detail  div.detail_con>div.TRS_Editor').extract_first()
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
