# -*- coding: utf-8 -*-
import scrapy
import re
import time
import random
import hashlib
from quotetutorial.items import ScrapyItem
import requests
import os


class ZgcDsSpider(scrapy.Spider):
    index = 31
    name = 'zgc-ds'
    allowed_domains = ['www.zgc-ds.gov.cn']
    md5 = hashlib.md5()
    start_urls = ['http://www.zgc-ds.gov.cn/cenep/newds/channelpage/content_slip.jsp?categoryCode=140&currentPage=1',
                  'http://www.zgc-ds.gov.cn/cenep/newds/channelpage/content_slip.jsp?categoryCode=120&currentPage=1',
                  'http://www.zgc-ds.gov.cn/cenep/newds/channelpage/content_slip.jsp?categoryCode=200100&currentPage=1',
                  'http://www.zgc-ds.gov.cn/cenep/newds/channelpage/content_slip.jsp?categoryCode=200120&currentPage=1',
                  'http://www.zgc-ds.gov.cn/cenep/newds/channelpage/content_slip.jsp?categoryCode=200140&currentPage=1',
                  'http://www.zgc-ds.gov.cn/cenep/newds/channelpage/content_slip.jsp?categoryCode=200160&currentPage=1'
                  ]
    category_index = {'140': '1', '120': '2', '200100': '3', '200120': '4', '200140': '5', '200160': '6'}
    category_desc = {'140': '通知公告', '120': '园区动态', '200100': '国家政策', '200120': '北京市政策', '200140': '中关村管委会政策',
                     '200160': '西城区政策'}
    url_descs = ['通知公告', '园区动态', '国家政策', '北京市政策', '中关村管委会政策', '西城区政策']
    base_url = 'http://www.zgc-ds.gov.cn'
    download_base_url = 'http://www.zgc-ds.gov.cn/cenep/'
    custom_settings = {
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en',
            "Host": "www.zgc-ds.gov.cn",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3",
            "Accept-Encoding": "gzip, deflate",
            "Referer": "http://onlinelibrary.wiley.com/journal/10.1002/(ISSN)1521-3773",
            "Connection": "keep-alive"
        },
    }

    def parse(self, response):
        print("**********", response.url)
        if response.status == 200:
            id_prefix = ''
            cate = ''
            if response.url in self.start_urls:
                cate_index = self.start_urls.index(response.url)
                id_prefix = str(self.index) + '-' + str(cate_index + 1)
                cate = self.url_descs[cate_index]
                last_page = response.xpath('//a[contains(.,"尾页")]/@href').extract_first()
                last_page_num = last_page[last_page.find('(') + 1:last_page.find(')')]
                for page in range(2, int(last_page_num) + 1):
                    # for page in range(2, 3):
                    url = response.url[0:response.url.rfind("=") + 1] + str(page)
                    yield scrapy.Request(url, meta={'id_prefix': id_prefix, 'category': cate},
                                         callback=self.parse)
            else:
                id_prefix = response.meta['id_prefix']
                cate = response.meta['category']

            info_list = response.css('tr[valign="top"]')
            for info in info_list:
                title = info.css('a::text').extract_first()
                href = info.css('a::attr("href")').extract_first()
                date = info.css('td.page_font1::text').extract_first()
                yield scrapy.Request(self.base_url + href[href.find('cateUrl=') + 8:], meta={'id_prefix': id_prefix,
                                                                                             'category': cate,
                                                                                             'title': title,
                                                                                             'date': date},
                                     callback=self.parse_content)

    def parse_content(self, response):
        print("############", response.url)
        if response.status == 200:
            self.md5.update(response.url.encode(encoding='utf-8'))
            item = ScrapyItem()
            id_prefix = response.meta['id_prefix']
            item['id'] = id_prefix + "-" + self.md5.hexdigest()
            category = response.meta['category']
            item['category'] = category
            item['title'] = response.meta['title']
            item['published_date'] = response.meta['date']
            item['source'] = ''
            item['content'] = ''
            details = response.css('#fontzoom').extract_first()
            if details:
                dr = re.compile(r'<[^>]+>', re.S)
                dd = dr.sub('', details)
                item['content'] = dd.replace(u'\u3000', '').replace(u'\t', '').replace(u'\xa0', '').replace(u'\r',
                                                                                                            '').replace(
                    u'\n',
                    '').strip()
            item['view_count'] = '0'
            item['url'] = response.url
            attach_path_arra = []
            attach_arra = []
            atta_arra = response.css('a[href*=".xls"]') + response.css('a[href*=".doc"]') + response.css(
                'a[href*=".pdf"]')
            for attch in atta_arra:
                save_path = ''
                attch_url = self.download_base_url + attch.css('::attr("href")').extract_first()
                attach_path_arra.append(attch_url)
                attch_name = attch.css('::text').extract_first()
                attach_arra.append(attch_name)
                if attch_name.rfind('.') == -1:
                    save_path = save_path + attch_name + attch_url[attch_url.rfind('.'):]
                else:
                    save_path = save_path + attch_name
                self.download_file(attch_url, save_path)
            item['attchment_path'] = ','.join(attach_path_arra)
            item['attchment'] = ','.join(attach_arra)
            #print(item)
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
