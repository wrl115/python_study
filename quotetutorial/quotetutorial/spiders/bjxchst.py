# -*- coding: utf-8 -*-
import scrapy
import re
import time
import random
import hashlib
from quotetutorial.items import ScrapyItem
import requests
import os
import io
import sys


# 西城区科技和信息化委员会
class BjxchstSpider(scrapy.Spider):
    index = 31
    name = 'bjxchst'
    allowed_domains = ['bjxchst.gov.cn']
    base_url = 'http://www.bjxchst.gov.cn'
    start_urls = ['http://www.bjxchst.gov.cn/XCKWtzgg.ycs',
                  'http://www.bjxchst.gov.cn/XCKWzcfg/XCKWgjj.ycs',
                  'http://www.bjxchst.gov.cn/XCKWzcfg/XCKWsj.ycs',
                  'http://www.bjxchst.gov.cn/XCKWzcfg/XCKWqj.ycs']
    category_index = {'XCKWtzgg': '1', 'XCKWgjj': '2', 'XCKWsj': '3', 'XCKWqj': '4'}
    category_desc = {'XCKWtzgg': '通知公告', 'XCKWgjj': '政策法规国家级', 'XCKWsj': '政策法规市级','XCKWqj':'政策法规区级'}
    url_descs = ['通知公告','政策法规国家级','政策法规市级','政策法规区级']
    page_num_cate = ['CNT_1018\/XCKWtzgg\/2559', 'CNT_1018\/XCKWzcfg\/XCKWgjj\/2540',
                     'CNT_1018\/XCKWzcfg\/XCKWsj\/2543',
                     'CNT_1018\/XCKWzcfg\/XCKWqj\/2544']
    detail_care = ['CNT_1018\/XCKWxxxq\/2557']

    def parse(self, response):
        print("##########", response.url)
        if response.status == 200:
            id_prefix = ''
            cate = ''
            if response.url in self.start_urls:
                cate_index = self.start_urls.index(response.url)
                id_prefix = str(self.index) + '-' + str(cate_index + 1)
                cate = self.url_descs[cate_index]
                if response.css('div#CNT_1018\/XCKWtzgg\/2559 tr'):
                    re_desc = 'div#' + self.page_num_cate[cate_index] + ' tr'
                    total_count_desc = response.css(re_desc)[-1].css('font::text').extract_first()
                    if total_count_desc:
                        for pagenum in range(2, int(total_count_desc)):
                            yield scrapy.FormRequest(
                                url=response.url,
                                formdata={"page_num": str(pagenum)},
                                callback=self.parse
                            )
                            time.sleep(random.randint(1, 6))
                else:
                    pass
            else:
                id_prefix = response.meta['id_prefix']
                cate = response.meta['category']

            links = response.css('div#CNT_1018\/XCKWtzgg\/2559 > table > tr')[0:-1]
            for link in links:
                url = self.base_url + link.css('a::attr("href")').extract_first()
                title = link.css('a::text').extract_first()
                date = link.css('a::text').extract()[1]
                print(title, date)
                yield scrapy.Request(url, meta={'id_prefix': id_prefix,
                                                'category': cate,
                                                'title': title, 'date': date}, callback=self.parse_content)
                time.sleep(random.randint(1, 6))

    def parse_content(self, response):
        print("^^^^^^", response.url)
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
            item['content'] = ''
            details = response.css('div#CNT_1018\/XCKWxxxq\/2557').extract_first()
            if details:
                dr = re.compile(r'<[^>]+>', re.S)
                dd = dr.sub('', details)
                item['content'] = dd.replace(u'\u3000', '').replace(u'\t', '').replace(u'\r', '').replace(u'\xa0',
                                                                                                          '').replace(
                    u'\n',
                    '').strip()
            item['view_count'] = '0'
            item['url'] = response.url

            attach_path_arra = []
            attach_arra = []
            atta_arra = response.css('a[href*=".xls"]') + response.css('a[href*=".doc"]') + response.css(
                'a[href*=".pdf"]') + response.css('a[href*=".zip"]')
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
                self.download_file(attch_url, save_path)
            item['attchment_path'] = ','.join(attach_path_arra)
            item['attchment'] = ','.join(attach_arra)
            print(item)
            # yield item

    def download_file(self, url, local_path):
        if os.path.exists(local_path):
            print("the %s exist" % local_path)
        else:
            print("start download the file", url)
            r = requests.get(url)
            print('down loading status ', r.status_code)
            with open(local_path, "wb") as code:
                code.write(r.content)
