# -*- coding: utf-8 -*-
import scrapy
import re
import time
import random
import hashlib
from quotetutorial.items import ScrapyItem
import requests
import os


class CttlSpider(scrapy.Spider):
    name = 'cttl'
    index = 6

    allowed_domains = ['www.cttl.cn']
    start_urls = ['http://www.cttl.cn/news/index.htm']
    category_index = {'news': '1'}
    category_desc = {'news': '新闻动态'}
    url_descs = ['新闻动态']
    md5 = hashlib.md5()

    def parse(self, response):
        # print('###!!!!', response.status)
        if response.status == 200:
            id_prefix = ''
            cate = ''
            if response.url.endswith('index.htm'):
                page_tail = response.css('.flickr a#pagenav_tail')
                if page_tail:
                    page_num = int(page_tail.css('::attr("href")').re('index[_](\d?).htm')[0]) + 1
                    for page in range(1, page_num):
                        url = response.url.replace('index.htm', 'index_%s.htm' % page)
                        cate_index = self.start_urls.index(response.url)
                        id_prefix = str(self.index) + '-' + str(cate_index + 1)
                        cate = self.url_descs[cate_index]
                        print('*********', url)
                        yield scrapy.Request(url, meta={'id_prefix': id_prefix, 'category': cate}, callback=self.parse)
                        time.sleep(random.randint(1, 6))
                else:
                    pass
            content_table = response.xpath('/html/body/div/table[3]/tr/td[2]/div/table/tr/td/table')
            if content_table:
                content_trs = content_table.css('tr:nth-child(2n)')
                for content_tr in content_trs:
                    if not id_prefix:
                        id_prefix = response.meta['id_prefix']
                    if not cate:
                        cate = response.meta['category']

                    if content_tr.css('a::attr("href")').extract_first():
                        url = response.url[0:response.url.rfind('/')] + content_tr.css(
                            'a::attr("href")').extract_first()[content_tr.css('a::attr("href")').extract_first().find(
                            '/'):]
                        print('连接：', url)
                        title = ''
                        date = ''
                        if content_tr.css('a::attr("title")').extract_first():
                            title = content_tr.css('a::attr("title")').extract_first()
                            # print('标题：', title)
                        if content_tr.css('td span::text').extract_first():
                            date = content_tr.css('td span::text').extract_first()
                            # print('发布日期', date)
                        yield scrapy.Request(url, meta={'id_prefix': id_prefix,
                                                        'category': cate,
                                                        'title': title, 'date': date}, callback=self.parse_content)
                    else:
                        print('failture :', response.url)

    def parse_content(self, response):
        print(response.url)
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
            source_desc = response.xpath(
                '/html/body/div/table[3]/tr/td[2]/div/table/tr[3]/td/table/tr[4]/td/text()').extract_first()
            if source_desc:
                item['source'] = source_desc.split(' ')[0].strip()

            # content_selectors = response.css('.Custom_UnionStyle')
            content = ''
            dr = re.compile(r'<[^>]+>', re.S)
            dd = ''
            content_desc = response.css('.STYLE2').extract_first()
            if content_desc:
                if content_desc.find('<style') != -1:
                    content_raw = re.match('^.*</style>(.*)', content_desc, re.S)
                    if content_raw:
                        content = content_raw.group(1)
                        dd = dr.sub('', content)
                else:
                    dd = dr.sub('', content_desc)

                        # print("*****", len(content_selectors))
            # if len(content_selectors) >= 1:
            #     dd = ''
            #     for content_selector in content_selectors:
            #         dd = dr.sub('', content_selector.extract_first()).strip()
            #         print("########", dd)
            #         if len(dd) == 0:
            #             continue
            #         else:
            #             content = dd.replace(u'\u3000', '').replace(u'\r\n', '').replace(u'\t', '').strip()
            #             break;
            #     else:
            #         pass
            item['content'] = dd.replace(u'\u3000', '').replace(u'\r\n', '').replace(u'\t', '').strip()
            item['view_count'] = '0'
            item['url'] = response.url
            item['attchment_path'] = ''
            item['attchment'] = ''
            # print(item)
            yield item
