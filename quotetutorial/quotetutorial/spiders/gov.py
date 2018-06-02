# -*- coding: utf-8 -*-
import scrapy
import re
import time
import random
import hashlib
from quotetutorial.items import ScrapyItem
import requests
import os


class GovSpider(scrapy.Spider):
    index = 26
    name = 'gov'
    allowed_domains = ['www.gov.cn', 'sousuo.gov.cn']
    start_urls = [  'http://www.gov.cn/guowuyuan/xinwen.htm',
                  # 'http://www.gov.cn/zhengce/zuixin.htm',
                  # 'http://www.gov.cn/zhengce/jiedu/bumen.htm',
                  # 'http://www.gov.cn/zhengce/jiedu/zhuanjia.htm',
                  # 'http://www.gov.cn/zhengce/jiedu/meiti.htm'
                  ]
    category_index = {'guowuyuan': '1',
                      'zhengce_zuixin': '2',
                      'zhengce_jiedu_bumen': '3',
                      'zhengce_jiedu_zhuanjia': '4',
                      'zhengce_jiedu_meiti': '5'}
    category_desc = {'guowuyuan': '国务院动态',
                     'zhengce_zuixin': '政策最新',
                     'zhengce_jiedu_bumen': '政策解读部门',
                     'zhengce_jiedu_zhuanjia': '政策解读专家',
                     'zhengce_jiedu_meiti': '政策解读媒体'}
    category_desc_arra = ['国务院动态', '政策最新', '政策解读部门', '政策解读专家', '政策解读媒体']

    md5 = hashlib.md5()

    def parse(self, response):
        print('+++++++++', response.url)
        if response.status == 200:
            if response.url in self.start_urls:
                first_page = response.css('.shortId .zl_more::attr("href")').extract_first()
                if first_page:
                    cate_index = self.start_urls.index(response.url) + 1
                    cate = self.category_desc_arra[cate_index]
                    yield scrapy.Request(first_page,
                                         meta={'cate_index': str(self.index) + '-' + str(cate_index), 'cate': cate},
                                         callback=self.parse)
            else:
                page_desc = re.match('(.*)/(.*?).htm', response.url)
                print(page_desc.group(), page_desc.group(2) == '0')

                page_all_num = 0
                # 分析页面内容
                title = ''
                date = ''
                href = ''
                page_selectors = response.css('ul.listTxt li:not(.line)')
                for page_selector in page_selectors:
                    if page_selector.css('h4 a::text').extract_first():
                        title = page_selector.css('h4 a::text').extract_first()
                    if page_selector.css('h4 span.date::text').extract_first():
                        date = page_selector.css('h4 span.date::text').extract_first().replace('.', '-')
                    if page_selector.css('h4 a::attr("href")').extract_first():
                        href = page_selector.css('h4 a::attr("href")').extract_first()
                    yield scrapy.Request(href,
                                         meta={'id_prefix': response.meta['cate_index'],
                                               'category': response.meta['cate'],
                                               'title': title, 'date': date},
                                         callback=self.parse_content)

                # 分析首页页面信息
                if page_desc.group() and page_desc.group(2) == '0':
                    all_page_num = response.css('#toPage li::text').extract_first()
                    page_num = re.findall('共(.*?)页', all_page_num)
                    if page_num:
                        print('总页数：', page_num[0])
                        page_all_num = int(page_num[0])
                        for i in range(1, page_all_num):
                            url = page_desc.group(1) + '/' + str(i) + '.htm'
                            yield scrapy.Request(url, meta={'cate_index': response.meta['cate_index'],
                                                            'cate': response.meta['cate']}, callback=self.parse)
                            time.sleep(random.randint(1, 3))
                else:
                    pass


    def parse_content(self, response):
        # print(response.url, '#', response.meta['id_prefix'], '##', response.meta['category'], '##', response.meta['title'], "##",
        #       response.meta['date'])
        self.md5.update(response.url.encode(encoding='utf-8'))
        if response.status == 200:
            item = ScrapyItem()
            id_prefix = response.meta['id_prefix']
            item['id'] = id_prefix + "-" + self.md5.hexdigest()
            category = response.meta['category']
            item['category'] = category
            item['title'] = response.meta['title']
            item['published_date'] = response.meta['date']
            item['source'] = ''
            source_desc = response.css(".pages-date>span::text").extract_first()
            if source_desc:
                source = re.findall('来源：(.*)', source_desc)
                print('来源：',source[0].strip())
                item['source'] = source[0].strip()
            dr = re.compile(r'<[^>]+>', re.S)
            dd = ''
            if response.css('.pages_content'):
                dd = dr.sub('', response.css('.pages_content').extract_first())
            item['content'] = dd.replace(u'\xa0', '').replace(u'\u3000', '').replace(u'\r\n', '').replace(u'\t',
                                                                                                          '').strip()
            item['url'] = response.url
            item['view_count'] = '0'
            item['attchment_path'] = ''
            item['attchment'] = ''
            yield item





