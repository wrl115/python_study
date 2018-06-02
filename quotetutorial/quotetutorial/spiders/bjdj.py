# -*- coding: utf-8 -*-
import scrapy
import re
import time
import random
import hashlib
from quotetutorial.items import ScrapyItem

# 北京组工
class BjdjSpider(scrapy.Spider):
    index = 5
    name = 'bjdj'
    allowed_domains = ['bjdj.gov.cn']
    start_urls = ['http://www.bjdj.gov.cn/news/tztg/index.html']
    category_index = {'tztg': '1', 'zcfbtz': '2', 'zcfbgg': '3'}
    category_desc = {'tztg': '通知公告', 'zcfbtz': '政策通知', 'zcfbgg': '政策公告'}
    md5 = hashlib.md5()
    def parse(self, response):
        if response.status == 200:
            print("***********", response.url)
            cate_type = re.match('^.*/(.*?)/index(.*?).html', response.url)
            cate_index = '0'
            cate_desc = ""
            if cate_type and cate_type.group(0):
                cate_index = self.category_index.get(cate_type.group(0), '0')
                cate_desc = self.category_index.get(cate_type.group(0), '0')
            news_list = response.css('div .splb_b .newsList li')
            for news in news_list:
                href = news.css('a::attr("href")').extract_first()
                date = news.css('a span::text').extract_first()
                title = news.css('a::text').extract_first()
                yield scrapy.Request(href, meta={'id_prefix': str(self.index) + '-' + cate_index, 'category': cate_desc,
                                                 'title': title, 'date': date}, callback=self.parse_content)
                time.sleep(random.randint(1, 6))
            baseurl = response.url[0:response.url.rfind('/') + 1]
            if response.css('div.page a[title="下一页"]::attr("href")'):
                next_page = response.css('div.page a[title="下一页"]::attr("href")').extract_first()
                yield scrapy.Request(baseurl + next_page, callback=self.parse)

    def parse_content(self, response):
        self.md5.update(response.url.encode(encoding='utf-8'))
        item = ScrapyItem()
        id_prefix = response.meta['id_prefix']
        item['id'] = id_prefix + "-" + self.md5.hexdigest()
        category = response.meta['category']
        item['category'] = category
        item['title'] = response.meta['title']
        item['published_date'] = response.meta['date']
        item['source'] = ''
        source_desc = re.findall('文章来源：(.*?)</font>', response.text)
        if source_desc:
            # print('来源：', source_desc[0])
            item['source'] = source_desc[0]
        content = response.xpath('/html/body/div/div[4]/div[2]/div[2]/dl/dl/dt')
        dr = re.compile(r'<[^>]+>', re.S)
        dd = ''
        if content:
            dd = dr.sub('', content.extract_first().replace(u'\xa0', '').replace(u'\u3000', '').replace(u'\r\n',
                                                                                                        '').replace(
                u'\t',
                '').strip())
            # print('内容：', dd)
        item['content'] =dd
        item['url'] = response.url
        item['view_count'] = '0'
        item['attchment_path'] = ''
        item['attchment'] = ''

        yield item
