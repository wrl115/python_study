# -*- coding: utf-8 -*-
import scrapy
import re
import time
import random
import hashlib
from quotetutorial.items import ScrapyItem
import requests
import os


# 北京12330
class Bj12330Spider(scrapy.Spider):
    index = 27
    name = 'bj12330'
    allowed_domains = ['www.bj12330.com']
    start_urls = ['http://www.bj12330.com/zscq/_15/tzgg/index.html']
    category_index = {'tzgg': '1'}
    category_desc = {'tzgg': '通知公告'}
    url_descs = ['通知公告']
    base_url = "http://www.bj12330.com"


    def parse(self, response):
        print("**********", response.url)
        if response.status == 200:
            id_prefix = ''
            cate = ''
            if response.url in self.start_urls:
                cate_index = self.start_urls.index(response.url)
                id_prefix = str(self.index) + '-' + str(cate_index + 1)
                cate = self.url_descs[cate_index]
                page_num_selector = response.css('div.xw-more input[type="hidden"]::attr("totalpage")')
                if page_num_selector:
                    pages = page_num_selector.extract_first()
                    for page in range(2, int(pages) + 1):
                        # for page in range(2, 3):
                        url = response.url[0:response.url.rfind("/") + 1] + "459491cb-" + str(page) + '.html'
                        yield scrapy.Request(url, meta={'id_prefix': id_prefix, 'category': cate}, callback=self.parse)

                # yield scrapy.Request(response.url,   callback=self.parse)
            else:
                id_prefix = response.meta['id_prefix']
                cate = response.meta['category']

            info_list = response.css('ul.xw-box2 li')
            for info in info_list:
                # print('title :', info.css('a::attr("title")').extract_first())
                title = info.css('a::attr("title")').extract_first()
                # print('href:', info.css('a::attr("href")').extract_first())
                href = self.base_url + info.css('a::attr("href")').extract_first()
                # print('date:', info.css('span.list_time::text').extract_first())
                date = info.css('span::text').extract_first()
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

            xl_info_arra = response.css('.xl-info::text').extract()
            xl_info = ''.join(xl_info_arra)
            if xl_info:
                source = xl_info[0:xl_info.find('更新时间')].strip()
                if source:
                    item['source'] = source

            item['content'] = ''
            details = response.css('.xl-con').extract_first()
            if details:
                dr = re.compile(r'<[^>]+>', re.S)
                dd = dr.sub('', details)
                item['content'] = dd.replace(u'\u3000', '').replace(u'\t', '').replace(u'\xa0', '').replace(u'\n',
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
