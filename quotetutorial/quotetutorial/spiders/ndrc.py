# -*- coding: utf-8 -*-
import scrapy
import re
import time
import random
import hashlib
from quotetutorial.items import ScrapyItem
import requests


# 国家发改委
class NdrcSpider(scrapy.Spider):
    index = 27
    name = 'ndrc'
    allowed_domains = ['www.ndrc.gov.cn']
    start_urls = ['http://www.ndrc.gov.cn/zwfwzx/tztg/index.html']
    category_index = {'tztg': '1', 'zcfbtz': '2', 'zcfbgg': '3'}
    category_desc = {'tztg': '通知公告', 'zcfbtz': '政策通知', 'zcfbgg': '政策公告'}
    md5 = hashlib.md5()

    def parse(self, response):
        print("********", response.url, response.url.endswith('index.html'))
        # links = response.css('ul.list_02.clearfix li.li a').extract()
        cate = '通知公告'
        cate_index = '1'

        if response.url.endswith('index.html'):
            pageNum = 0
            pageScript = response.css('ul#nomal_pages.pages.clearfix script::text').extract_first().strip()
            pageNumArra = re.findall('\((\d*?),', pageScript)
            cate_desc = re.match('^.*/(.*?)/index.html', response.url)
            cate_index = self.category_index.get(cate_desc.group(1), '0')
            cate = self.category_desc.get(cate_desc.group(1), '')
            if len(pageNumArra) > 0:
                pageNum = pageNumArra[0]
                print('总页数：', pageNum)
            for page in range(1, int(pageNum)):
                nexturl = response.url.replace('index.html', 'index_' + str(page) + '.html')
                # print('page url :', nexturl)
                yield scrapy.Request(nexturl, meta={'cate_index': cate_index, 'cate': cate}, callback=self.parse)
                time.sleep(random.randint(1, 3))
        else:
            cate_index = response.meta['cate_index']
            cate = response.meta['cate']
        hrefs = response.css('ul.list_02.clearfix li.li a::attr("href")').extract()
        # titles = response.css('ul.list_02.clearfix li.li a::text').extract_first()
        for url in hrefs:
            if url.find('http:') == -1:
                yield scrapy.Request(response.url[0:response.url.rfind('/')] + url[1:],
                                     meta={'id_prefix': self.index + '-' + cate_index, 'category': cate},
                                     callback=self.parse_content)
            else:
                yield scrapy.Request(url, callback=self.parse_content)

    def parse_content(self, response):
        self.md5.update(response.url.encode(encoding='utf-8'))
        if response.status == 200:
            print("-------", response.url)
            item = ScrapyItem()
            id_prefix = response.meta['id_prefix']
            item['id'] = id_prefix + "-" + self.md5.hexdigest()
            category = response.meta['category']
            item['category'] = category

            # print('标题：', response.css('div.txt_title1.tleft::text').extract_first().strip())
            item['title'] = response.css('div.txt_title1.tleft::text').extract_first().strip()
            # print('发布日期：', response.css('div.txt_subtitle1.tleft::text').extract_first().strip())
            item['published_date'] = response.css('div.txt_subtitle1.tleft::text').extract_first().strip()
            # print('来源：', response.css('#dSourceText a::text').extract_first())
            item['source'] = response.css('#dSourceText a::text').extract_first().strip()
            dr = re.compile(r'<[^>]+>', re.S)
            dd = dr.sub('', response.css('div.TRS_Editor').extract_first())
            # print('内容：', dd)
            item['content'] = dd
            # print('附件：', re.findall('附件：<a href="(.*?)".*?<font color="blue">(.*?)</font></a>', response.text))
            attchment = re.findall('附件：<a href="(.*?)".*?<font color="blue">(.*?)</font></a>', response.text)
            for attc in attchment:
                print(attc[0], attc[1])

            print(item)

    def download_file(self, url, local_path):
        if os.path.exists(local_path):
            print("the %s exist" % local_path)
        else:
            print("start download the file", url)
            r = requests.get(url)
            print('down loading status ', r.status_code)
            with open(local_path, "wb") as code:
                code.write(r.content)


