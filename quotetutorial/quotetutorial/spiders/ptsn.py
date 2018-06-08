# -*- coding: utf-8 -*-
import scrapy
import re
import time
import random
import hashlib
from quotetutorial.items import ScrapyItem
import requests
import os


class PtsnSpider(scrapy.Spider):
    index = 34
    name = 'ptsn'
    allowed_domains = ['www.ptsn.net.cn']
    start_urls = [
        'http://www.ptsn.net.cn/article_new/list_article.php?categories_id=84120dc6-1f8f-9522-9d4a-44b1bedcc0ab&page_currentPage=1',
        'http://www.ptsn.net.cn/article_new/list_article.php?categories_id=8f5a5e4d-2d74-d647-235b-44b1be7c0bb4&page_currentPage=1',
        'http://www.ptsn.net.cn/article_new/list_article.php?categories_id=46eec597-e1da-8b53-5ca1-44b1be4f7e36&page_currentPage=1',
        'http://www.ptsn.net.cn/article_new/list_article.php?categories_id=e2a2aedd-b3f5-9172-a19e-44b1be617ce6&page_currentPage=1',
        'http://www.ptsn.net.cn/article_new/list_article.php?categories_id=7116d4bc-8017-598d-73ac-44b1be903d12&page_currentPage=1'
    ]
    category_index = {
                      '84120dc6-1f8f-9522-9d4a-44b1bedcc0ab': '1',
                      '8f5a5e4d-2d74-d647-235b-44b1be7c0bb4': '2',
                      '46eec597-e1da-8b53-5ca1-44b1be4f7e36': '3',
                      'e2a2aedd-b3f5-9172-a19e-44b1be617ce6': '4',
                      '7116d4bc-8017-598d-73ac-44b1be903d12': '5'
                      }
    category_desc = {
                     '84120dc6-1f8f-9522-9d4a-44b1bedcc0ab': '标准动态',
                     '8f5a5e4d-2d74-d647-235b-44b1be7c0bb4': '中国通信行业法规',
                     '46eec597-e1da-8b53-5ca1-44b1be4f7e36': '中国国家法律法规',
                     'e2a2aedd-b3f5-9172-a19e-44b1be617ce6': '国际政策法规',
                     '7116d4bc-8017-598d-73ac-44b1be903d12': '技术热点'
                     }
    url_descs = [
                 '标准动态',
                 '中国通信行业法规',
                 '中国国家法律法规',
                 '国际政策法规',
                 '技术热点']
    base_url = "http://www.ptsn.net.cn"
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

                fenye_num = re.findall("共(.*?)条.*第(.*?)/(.*?)页", response.text, re.S)
                if fenye_num && len(fenye_num[0])==3:
                    for page in range(2, int(fenye_num[0][2]) + 1):
                        url = response.url[0:response.url.rfind("=") + 1] + str(page)
                        # print(url)
                        yield scrapy.Request(url, meta={'id_prefix': id_prefix, 'category': cate}, callback=self.parse)
                        time.sleep(3)
            else:
                id_prefix = response.meta['id_prefix']
                cate = response.meta['category']
            # print(len(response.css('body > table:nth-child(6) >  tr > td:nth-child(1) > table >   tr').extract()))
            info_list = response.css('body > table:nth-child(6) >  tr > td:nth-child(1) > table >   tr')[3:]
            for info in info_list:
                date = info.css('font')[1].css('::text').extract_first().strip()[1:-1]
                title = info.css('a::text').extract_first().strip()
                href = self.base_url + info.css('a::attr("href")').extract_first()
                # print(href)
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
            try:
                source = response.xpath('/html/body/table[5]/tr/td')[-3].css('::text').extract_first()
                if source:
                    item['source'] = source
            except:
                print('get source exception!!!', response.url)
            item['view_count'] = '0'
            item['url'] = response.url
            # print(response.css('body > table:nth-child(11)').extract_first())
            details = response.css('body > table:nth-child(11)').extract_first()
            if details:
                dr = re.compile(r'<[^>]+>', re.S)
                dd = dr.sub('', details)
                item['content'] = dd.replace(u'\u3000', '').replace(u'\t', '').replace(u'\r', '').replace(u'\xa0',
                                                                                                          '').replace(
                    u'\n',
                    '').strip()
            attach_path_arra = []
            attach_arra = []
            atta_arra = response.css('a[href*=".xls"]') + response.css('a[href*=".doc"]') + response.css(
                'a[href*=".pdf"]')
            for attch in atta_arra:
                save_path = ''
                attch_url = self.base_url + + attch.css('::attr("href")').extract_first()
                attach_path_arra.append(attch_url)
                attch_name = attch.css('::text').extract_first()
                attach_arra.append(attch_name)
                if attch_name.rfind('.') == -1:
                    save_path = save_path + attch_name + attch_url[attch_url.rfind('.'):]
                else:
                    save_path = save_path + attch_name
                # self.download_file(attch_url, save_path)
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
