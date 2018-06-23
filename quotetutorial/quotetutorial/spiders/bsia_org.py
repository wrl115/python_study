# -*- coding: utf-8 -*-
import scrapy
import re
import time
import random
import hashlib
from quotetutorial.items import ScrapyItem
import requests
import os


# 北京软件行业协会
class BsiaOrgSpider(scrapy.Spider):
    index = 22
    name = 'bsia_org'
    allowed_domains = ['www.bsia.org.cn']
    start_urls = ['http://www.bsia.org.cn/fro/content-list!data.action?channelId=right01',
                  'http://www.bsia.org.cn/fro/content-list!data.action?channelId=index05']
    category_index = {'right01': '1', 'index05': '2'}
    category_desc = {'right01': '通知公告', 'index05': '政策法规'}
    url_descs = ['通知公告', '政策法规']
    base_url = 'http://www.bsia.org.cn'

    def parse(self, response):
        print("##########", response.url)
        if response.status == 200:
            id_prefix = ''
            cate = ''
            if response.url in self.start_urls:
                cate_index = self.start_urls.index(response.url)
                id_prefix = str(self.index) + '-' + str(cate_index + 1)
                cate = self.url_descs[cate_index]
                total_count_desc = response.css('ul.page li')
                if total_count_desc:
                    total_num = total_count_desc[-2].css('a::text').extract_first()
                    print(total_num)
                    if total_num:
                        for page_num in range(2, int(total_num) + 1):
                            yield scrapy.FormRequest(
                                url=response.url,
                                meta={'id_prefix': id_prefix,
                                      'category': cate},
                                formdata={"pageNo": str(page_num)},
                                callback=self.parse_list_page
                            )
                            time.sleep(random.randint(1, 6))
            else:
                id_prefix = response.meta['id_prefix']
                cate = response.meta['category']

            links = response.css("div.news-list ul.news-list-ul li")
            for link in links:
                href = link.css('a::attr("href")').extract_first()
                if href.startswith('http'):
                    url = href
                else:
                    url = self.base_url + href
                title = link.css('a::text').extract_first().strip()

                date = link.css('p.newlist-p-time::text').extract_first().strip()
                print(url, title)
                if url:
                    yield scrapy.Request(url, meta={'id_prefix': id_prefix,
                                                    'category': cate,
                                                    'title': title, 'date': date}, callback=self.parse_content)
                    time.sleep(random.randint(1, 6))

    def parse_list_page(self, response):
        if response.status == 200:
            print("^^^^^^", response.url)
            id_prefix = response.meta['id_prefix']
            cate = response.meta['category']
            links = response.css("div.news-list ul.news-list-ul li")
            for link in links:
                href = link.css('a::attr("href")').extract_first()
                if href.startswith('http'):
                    url = href
                else:
                    url = self.base_url + href
                title = link.css('a::text').extract_first().strip()

                date = link.css('p.newlist-p-time::text').extract_first().strip()
                print(url, title)
                if url:
                    yield scrapy.Request(url, meta={'id_prefix': id_prefix,
                                                    'category': cate,
                                                    'title': title, 'date': date}, callback=self.parse_content)
                    time.sleep(random.randint(1, 6))

    def parse_content(self, response):
        if response.status == 200:
            print("***********", response.url)
            md5 = hashlib.md5()
            md5.update(response.url.encode(encoding='utf-8'))
            item = ScrapyItem()
            id_prefix = response.meta['id_prefix']
            item['id'] = id_prefix + "-" + md5.hexdigest()
            category = response.meta['category']
            item['category'] = category
            item['title'] = response.meta['title']
            if item['title'].endswith('...'):
                item['title'] = response.css('h1::text').extract_first().strip()
            item['published_date'] = response.meta['date']
            item['source'] = ''
            source_desc = response.css('div.sub-title p::text').extract_first()
            if source_desc:
                source_re = re.findall('来源：(.*?)$', source_desc)
                if source_re:
                    item['source'] = source_re[0].strip()
            item['content'] = ''
            details = response.css('div.contdiv div.essay').extract_first()
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
                'a[href*=".pdf"]') + response.css('a[href*=".zip"]') + response.css('a[href*=".rar"]')
            for attch in atta_arra:
                save_path = ''
                attch_url = self.base_url + attch.css('::attr("href")').extract_first()
                attach_path_arra.append(attch_url)
                attch_name = attch.css('::text').extract_first()
                if not attch_name:
                    attch_name = attch_url[attch_url.rfind("/") + 1:]
                attach_arra.append(attch_name)
                if attch_name.rfind('.') == -1:
                    save_path = save_path + attch_name + attch_url[attch_url.rfind('.'):]
                else:
                    save_path = save_path + attch_name
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
