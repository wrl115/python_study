# -*- coding: utf-8 -*-
import scrapy
import re
import time
import random
import hashlib
from quotetutorial.items import ScrapyItem
import requests
import os


# 国家知识产权局
class SipoSpider(scrapy.Spider):
    index = 25
    name = 'sipo'
    allowed_domains = ['www.sipo.gov.cn']
    start_urls = [
        'http://www.sipo.gov.cn/gztz/index.htm',
        'http://www.sipo.gov.cn/zfgg/index.htm',
        'http://www.sipo.gov.cn/szywn/index.htm',
        'http://www.sipo.gov.cn/dtxx/index.htm',
        'http://www.sipo.gov.cn/mtsd/index.htm'
    ]
    category_index = {'gztz': '1', 'zfgg': '2', 'szywn': '3', 'dtxx': '4', 'mtsd': '5'}
    category_desc = {'gztz': '通知公告-工作通知', 'zfgg': '通知公告-政府公告', 'szywn': '时政要闻', 'dtxx': '地方动态', 'mtsd': '媒体视点' }
    url_descs = ['通知公告-工作通知', '通知公告-政府公告','时政要闻','地方动态','媒体视点' ]
    base_url = 'http://www.sipo.gov.cn'

    def parse(self, response):
        print("**********", response.url)
        if response.status == 200:
            id_prefix = ''
            cate = ''
            if response.url in self.start_urls:
                cate_index = self.start_urls.index(response.url)
                id_prefix = str(self.index) + '-' + str(cate_index + 1)
                cate = self.url_descs[cate_index]

                fenye_num = response.css('form[name="pageForm"] select option:last-child ::text').extract_first()
                if fenye_num:
                    for page in range(1, int(fenye_num)):
                        url = response.url.replace('index.htm', 'index%s.htm' % page)
                        yield scrapy.Request(url, meta={'id_prefix': id_prefix, 'category': cate}, callback=self.parse)
            else:
                id_prefix = response.meta['id_prefix']
                cate = response.meta['category']
        info_list = response.css('div.index_articl_list ul > li')
        for info in info_list:
            date = info.css('span::text').extract_first().strip()
            title = info.css('a::attr("title")').extract_first().strip()
            href = response.url[0:response.url.rfind('/') + 1] + info.css('a::attr("href")').extract_first()

            yield scrapy.Request(href, meta={'id_prefix': id_prefix,
                                             'category': cate,
                                             'title': title, 'date': date}, callback=self.parse_content)
            time.sleep(random.randint(1, 6))

    def parse_content(self, response):
        print("############", response.url)
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
            details = response.css('div.index_art_con p::text').extract()
            if details:
                dd = ''.join(details)
                item['content'] = dd.replace(u'\u3000', '').replace(u'&nbsp', '').replace(u'\t', '').replace(u'\xa0',
                                                                                                             '').replace(
                    u'-->', '').replace(u';', '').replace(u'\n', '').strip()
            item['view_count'] = '0'
            item['url'] = response.url
            attach_path_arra = []
            attach_arra = []
            atta_arra = response.css('a[href*=".xls"]') + response.css('a[href*=".doc"]') + response.css(
                'a[href*=".pdf"]') + response.css('a[href*=".zip"]') + response.css('a[href*=".rar"]')
            for attch in atta_arra:
                save_path = ''
                href_attch = attch.css('::attr("href")').extract_first()
                if href_attch.startswith('http'):
                    attch_url = href_attch
                else:
                    attch_url = self.base_url + href_attch[href_attch.find('/'):]
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
