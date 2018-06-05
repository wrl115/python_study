# -*- coding: utf-8 -*-
import scrapy
import re
import time
import random
import hashlib
from quotetutorial.items import ScrapyItem
import requests
import os


class Tax861Spider(scrapy.Spider):
    index = 10
    name = 'tax861'
    allowed_domains = ['shiju.tax861.gov.cn']
    start_urls = ['http://shiju.tax861.gov.cn/xxgk/zyts/zyts_more.asp']
    category_index = {'zyts': '1'}
    category_desc = {'zyts': '通知公告'}
    url_descs = ['通知公告']
    md5 = hashlib.md5()

    def parse(self, response):
        print("********", response.url)
        if response.status == 200:
            id_prefix = ''
            cate = ''
            if response.url in self.start_urls:
                cate_index = self.start_urls.index(response.url)
                id_prefix = str(self.index) + '-' + str(cate_index + 1)
                cate = self.url_descs[cate_index]
                page_num = response.xpath(
                    '//td[contains(@background,"bottom_bj")][contains(@align,"right")]/a[contains(.,"尾页")]/@href').re(
                    'aa=(.*?)&')
                if page_num:
                    for page in range(2, int(page_num[0]) + 1):
                    #for page in [2, 3]:
                        print("$$$$$$", response.url + '?aa=' + str(page))
                        yield scrapy.Request(response.url + '?aa=' + str(page),
                                             meta={'id_prefix': id_prefix, 'category': cate},
                                             callback=self.parse)
                        # time.sleep(random.randint(1, 3))
            else:
                id_prefix = response.meta['id_prefix']
                cate = response.meta['category']
            info_list = response.css('.nr_right table:nth-child(2n+1)')[0:-2]
            for info in info_list:
                # print("#####", info.css('span::text').re('.*\[(.*)\]')[0])
                date = info.css('span::text').re('.*\[(.*)\]')[0]
                # print("#####2", info.css('a::attr("href")').extract_first())
                href = response.url[0:response.url.rfind('/') + 1] + info.css('a::attr("href")').extract_first()
                # print("#####3", info.css('a::text').extract_first())
                title = info.css('a::text').extract_first()

                print('url', href)
                yield scrapy.Request(href, meta={'id_prefix': id_prefix,
                                                 'category': cate,
                                                 'title': title, 'date': date}, callback=self.parse_content)
                time.sleep(random.randint(1, 6))

    def parse_content(self, response):
        print("#########", response.url)
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
            item['content'] = ''
            item['view_count'] = '0'
            view_count = response.css('td#td_degree_2::text').extract_first()
            if view_count:
                item['view_count'] = view_count
            details = response.css('div#div_zhengwen').extract_first()
            if details:
                dr = re.compile(r'<[^>]+>', re.S)
                dd = dr.sub('', details)
                item['content'] = dd.replace(u'\u3000', '').replace(u'\t', '').replace(u'\xa0', '').replace(u'\u2003',
                                                                                                            '').strip()
            item['url'] = response.url
            attach_path_arra = []
            attach_arra = []
            atta_arra = response.css('a[href*=".xls"]') + response.css('s[href*=".doc"]') + response.css(
                's[href*=".pdf"]')
            for attch in atta_arra:
                save_path = ''
                attch_url = response.url[0:response.url.rfind('/') + 1] + attch.css('::attr("href")').extract_first()
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
