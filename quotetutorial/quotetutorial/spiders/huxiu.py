# -*- coding: utf-8 -*-
import scrapy
import re
import time
import random
import hashlib
from quotetutorial.items import ScrapyItem
import requests
import os
import json
from bs4 import BeautifulSoup


# 虎嗅网
# http://www.wendaoxueyuan.com/post/detail/684
class HuxiuSpider(scrapy.Spider):
    index = 24
    name = 'huxiu'
    allowed_domains = ['www.huxiu.com']
    start_urls = ['https://www.huxiu.com/']
    category_index = {'article': '1'}
    category_desc = {'article': '新闻咨询'}
    url_descs = ['新闻咨询']
    total_page = 0
    md5 = hashlib.md5()

    def parse(self, response):
        print("**********", response.url, response.url in self.start_urls)
        if response.status == 200:
            id_prefix = ''
            cate = ''
            hash_code = ''
            if response.url in self.start_urls:
                cate_index = self.start_urls.index(response.url)
                # id_prefix = str(self.index) + '-' + str(cate_index + 1)
                # cate = self.url_descs[cate_index]
                id_prefix = str(self.index) + '-1'
                cate = '新闻咨询'
                hash_code = response.text[
                            response.text.find('huxiu_hash_code') + 17:response.text.find('huxiu_hash_code') + 49]
                data_inf = response.css('div[data-last_dateline]')
                if data_inf:
                    url = "https://www.huxiu.com/v2_action/article_list"
                    current_page = data_inf.css('::attr("data-cur_page")').extract_first()
                    last_dateline = data_inf.css('::attr("data-last_dateline")').extract_first()
                    nextFormData = {'huxiu_hash_code': hash_code,
                                    'page': str(int(current_page) + 1),
                                    'last_dateline': last_dateline}
                    yield scrapy.FormRequest(url, method='POST', formdata=nextFormData,
                                             meta={'id_prefix': id_prefix, 'category': cate,
                                                   'huxiu_hash_code': hash_code, 'page': str(int(current_page) + 1)},
                                             callback=self.parse_next_list)
                    time.sleep(3)
                else:
                    pass
            else:
                id_prefix = response.meta['id_prefix']
                cate = response.meta['category']
                hash_code = response.meta['huxiu_hash_code']

            info_list = response.css('.mod-info-flow div[data-aid]::attr("data-aid")').extract()
            for info in info_list:
                href = "https://www.huxiu.com/article/" + str(info) + ".html"
            yield scrapy.Request(href, meta={'id_prefix': id_prefix,
                                             'category': cate}, callback=self.parse_content)
            time.sleep(random.randint(1, 6))

    def parse_content(self, response):
        # print("############", response.url)
        if response.status == 200:
            self.md5.update(response.url.encode(encoding='utf-8'))
            item = ScrapyItem()
            id_prefix = response.meta['id_prefix']
            item['id'] = id_prefix + "-" + self.md5.hexdigest()
            category = response.meta['category']
            item['category'] = category
            item['source'] = ''
            item['view_count'] = '0'
            item['url'] = response.url
            item['attchment_path'] = ''
            item['attchment'] = ''
            # 标题
            # print("title:", response.css('.t-h1::text').extract_first().strip())
            item['title'] = response.css('.t-h1::text').extract_first().strip()
            # 作者
            # print("author:", response.css('.author-name a::text').extract_first().strip())
            item['author'] = response.css('.author-name a::text').extract_first().strip()
            date_desc = response.css('span.article-time.pull-left')
            item['published_date'] = ''
            # 日期有两种形式
            if date_desc:
                # print("date:", response.css('span.article-time.pull-left::text').extract_first())
                item['published_date'] = response.css('span.article-time.pull-left::text').extract_first()
            else:
                # print("other date:", response.css('.article-time::text').extract_first().strip())
                item['published_date'] = response.css('.article-time::text').extract_first()
            # 收藏
            share_desc = response.css('span.article-share.pull-left::text').extract_first()
            item['share_num'] = '0'
            if share_desc:
                share_m = re.match('^收藏(\d)', share_desc)
                if share_m:
                    print("share:", share_m.group(1))
                    item['share_num'] = share_m.group(1)
            # 评论
            pl_desc = response.css('span.article-pl.pull-left::text').extract_first()
            item['pl_num'] = '0'
            if pl_desc:
                pl_m = re.match('^评论(\d)', pl_desc)
                if pl_m:
                    # print("pl_num:", pl_m.group(1))
                    item['pl_num'] = pl_m.group(1)

            # 内容
            details = response.css('.article-content-wrap').extract_first()
            item['content'] = ''
            if details:
                dr = re.compile(r'<[^>]+>', re.S)
                dd = dr.sub('', details)
                tt = dd.replace(u'\n', '').replace(u'\xa0', '')
                if tt.find('文章为作者独立观点') != -1:
                    content = tt[0:tt.find('文章为作者独立观点') - 1].strip()
                else:
                    content = tt
                item['content'] = content
            # 点赞
            praise_num = response.css('.num::text').extract_first()
            item['praise_num'] = 0
            if praise_num:
                # print('praise_num', praise_num)
                item['praise_num'] = praise_num

            # print(item)
            yield item
        else:
            print(response.url, 'request error')

    def parse_next_list(self, response):

        if response.status == 200:
            id_prefix = response.meta['id_prefix']
            cate = response.meta['category']
            hash_code = response.meta['huxiu_hash_code']
            page = response.meta['page']
            # print('current page:', page, 'hash_code', hash_code)
            # nextFormData = {'huxiu_hash_code': hash_code,
            #                 'page': str(int(current_page) + 1),
            #                 'last_dateline': last_dateline}
            # print(type(response.body.decode('utf-8')), response.body.decode('utf-8'))
            jsobj = json.loads(response.body.decode('utf-8'))
            if self.total_page == 0:
                print('total_page', jsobj['total_page'])
                self.total_page = int(jsobj['total_page'])

            last_dateline = jsobj['last_dateline']
            soup = BeautifulSoup(jsobj['data'], 'lxml')
            print(page, 'last_dateline', jsobj['last_dateline'], 'data-aid', len(soup.select('div[data-aid]')))
            for title in soup.select('div[data-aid]'):
                href = "https://www.huxiu.com/article/" + title.get('data-aid') + ".html"
                yield scrapy.Request(href, meta={'id_prefix': id_prefix,
                                                 'category': cate}, callback=self.parse_content)
                time.sleep(3)

            if page != 0 and int(page) < self.total_page:
                nextFormData = {'huxiu_hash_code': hash_code,
                                'page': str(int(page) + 1),
                                'last_dateline': last_dateline}
                url = "https://www.huxiu.com/v2_action/article_list"
                yield scrapy.FormRequest(url, method='POST', formdata=nextFormData,
                                         meta={'id_prefix': id_prefix, 'category': cate,
                                               'huxiu_hash_code': hash_code, 'page': str(int(page) + 1)},
                                         callback=self.parse_next_list)
                time.sleep(6)
