# -*- coding: utf-8 -*-
import scrapy
import re
import time
import random
import hashlib
from quotetutorial.items import ScrapyItem
import requests
import os


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
        title = response.css('ul.list_02.clearfix li.li a::text').extract_first()
        date = response.css('ul.list_02.clearfix li.li .date').extract_first()
        li_selectors = response.css('ul.list_02.clearfix li.li')
        for li_selector in li_selectors:
            url = li_selector.css('a::attr("href")').extract_first()
            title = li_selector.css('a::text').extract_first()
            date = li_selector.css('.date::text').extract_first().replace('/', '-')
            if url.find('http:') == -1:
                yield scrapy.Request(response.url[0:response.url.rfind('/')] + url[1:],
                                     meta={'id_prefix': str(self.index) + '-' + cate_index, 'category': cate,
                                           'title': title, 'date': date},
                                     callback=self.parse_content)
            else:
                yield scrapy.Request(url, meta={'id_prefix': str(self.index) + '-' + cate_index, 'category': cate,
                                                'title': title, 'date': date}, callback=self.parse_content)

    def parse_content(self, response):
        self.md5.update(response.url.encode(encoding='utf-8'))
        if response.status == 200:
            print("-------", response.url)
            item = ScrapyItem()
            id_prefix = response.meta['id_prefix']
            item['id'] = id_prefix + "-" + self.md5.hexdigest()
            category = response.meta['category']
            item['category'] = category
            item['title'] = response.meta['title']
            item['published_date'] = response.meta['date']

            # print('标题：', response.css('div.txt_title1.tleft::text').extract_first().strip())
            # if response.css('div.txt_title1.tleft::text').extract_first():
            #     item['title'] = response.css('div.txt_title1.tleft::text').extract_first().strip()

            # print('发布日期：', response.css('div.txt_subtitle1.tleft::text').extract_first().strip())
            # if response.css('div.txt_subtitle1.tleft::text').extract_first():
            #     item['published_date'] = response.css('div.txt_subtitle1.tleft::text').extract_first().strip()
            # print('来源：', response.css('#dSourceText a::text').extract_first())
            item['source'] = ''
            if response.css('#dSourceText a::text').extract_first():
                item['source'] = response.css('#dSourceText a::text').extract_first().strip()
            dr = re.compile(r'<[^>]+>', re.S)
            dd = ''

            if response.css('div.TRS_Editor'):
                dd = dr.sub('', response.css('div.TRS_Editor').extract_first())
            elif response.css('.Group2_Left_body .txt1'):
                dd = dr.sub('', response.css('.Group2_Left_body .txt1').extract_first())
            # print('内容：', dd)
            item['content'] = dd.replace(u'\xa0', '').replace(u'\u3000', '').replace(u'\r\n', '').replace(u'\t',
                                                                                                          '').strip()
            # print('附件：', re.findall('附件：<a href="(.*?)".*?<font color="blue">(.*?)</font></a>', response.text))
            attchment = re.findall('附件：<a href="(.*?)".*?<font color="blue">(.*?)</font></a>', response.text)
            attach_path_arra = []
            attach_arra = []
            for attc in attchment:
                file_name = dr.sub('', attc[1]).replace(u'\u3000', '').replace(u'\r\n', '').replace(u'\t', '').strip()
                file_href = attc[0]
                # print('&&&&&&&&&', file_href, file_name)
                save_path = ''
                attach_path_arra.append(file_href)
                attach_arra.append(file_name)
                if file_name.rfind('.') == -1:
                    save_path = save_path + file_name + file_href[file_href.rfind('.'):]
                else:
                    save_path = save_path + file_name
                self.download_file(file_href, save_path)
            item['view_count'] = '0'
            item['url'] = response.url
            item['attchment_path'] = ','.join(attach_path_arra)
            item['attchment'] = ','.join(attach_arra)
            yield (item)

    def download_file(self, url, local_path):

        if os.path.exists(local_path):
            print("the %s exist" % local_path)
        else:
            print("start download the file", url)
            r = requests.get(url)
            print('down loading status ', r.status_code)
            with open(local_path, "wb") as code:
                code.write(r.content)
