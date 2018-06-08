# -*- coding: utf-8 -*-
import scrapy
import re
import time
import random
import hashlib
from quotetutorial.items import ScrapyItem
import requests
import os


# 西城工商分局
class Hd315Spider(scrapy.Spider):
    index = 32
    name = 'hd315'
    allowed_domains = ['www.hd315.gov.cn']
    start_urls = ['http://www.hd315.gov.cn/zwxx/tzgg/index.html']
    category_index = {'tzgg': '1'}
    category_desc = {'tzgg': '通知公告'}
    url_descs = ['通知公告']
    md5 = hashlib.md5()

    def parse(self, response):
        print("**********", response.url)
        if response.status == 200:
            id_prefix = ''
            cate = ''
            if response.url in self.start_urls:
                cate_index = self.start_urls.index(response.url)
                id_prefix = str(self.index) + '-' + str(cate_index + 1)
                cate = self.url_descs[cate_index]
                fenye_desc = response.css('.fenye script').extract_first()
                fenye_num = re.findall('var countPage = (.*?)//共多少页', fenye_desc)
                if fenye_num:
                    for page in range(1, int(fenye_num[0])):
                        # for page in range(2, 3):
                        url = response.url[0:response.url.rfind("/") + 1] + "index_" + str(page) + '.html'
                        yield scrapy.Request(url, meta={'id_prefix': id_prefix, 'category': cate}, callback=self.parse)
            else:
                id_prefix = response.meta['id_prefix']
                cate = response.meta['category']

                # yield scrapy.Request(response.url, callback=self.parse_content)
                # response.css('.list-date02 li').extract()
            info_list = response.css('.list-date02 li')
            for info in info_list:
                date = info.css('::text').extract()[2].strip()
                title = info.css('::text').extract()[1].strip()
                href = response.url[0:response.url.rfind('/') + 1] + info.css('a::attr("href")').extract_first()

                yield scrapy.Request(href, meta={'id_prefix': id_prefix,
                                                 'category': cate,
                                                 'title': title, 'date': date}, callback=self.parse_content)
                time.sleep(random.randint(1, 6))

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
            title = response.css('div.article h1::text').extract_first().strip()
            if title:
                item['title'] = title
            details = response.css('#div_zhengwen').extract_first()
            style = response.css('#div_zhengwen style').extract_first()
            if style:
                details = details.replace(style, '')
            if details:
                dr = re.compile(r'<[^>]+>', re.S)
                dd = dr.sub('', details)
                item['content'] = dd.replace(u'\u3000', '').replace(u'&nbsp', '').replace(u'\t', '').replace(u'\xa0',
                                                                                                             '').replace(
                    u'-->', '').replace(u';', '').replace(u'\n', '').strip()
            item['view_count'] = '0'
            item['url'] = response.url
            attach_path_arra = []
            attach_arra = []
            atta_arra = response.css('a[href*=".xls"]') + response.css('a[href*=".doc"]') + response.css(
                'a[href*=".pdf"]')
            for attch in atta_arra:
                save_path = ''
                attch_url = response.url[0:response.url.rfind("/") + 1] + attch.css('::attr("href")').extract_first()
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
