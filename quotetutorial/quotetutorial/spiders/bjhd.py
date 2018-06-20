# -*- coding: utf-8 -*-
import scrapy
import re
import time
import random
import hashlib
from quotetutorial.items import ScrapyItem
import requests
import os


# 海淀科技园管委会
class BjhdSpider(scrapy.Spider):
    index = 17
    name = 'bjhd'
    page_num = 0
    allowed_domains = ['hdy.bjhd.gov.cn']
    start_urls = ['http://hdy.bjhd.gov.cn/yqdt2014/tzgg/index.htm']
    category_index = {'tzgg': '1', 'gjjzc': '2', 'bjszc': '3', 'hdqzc': '4',
                      'zcjd': '5', 'xyqyw': '6', 'qyzx': '7', 'mtbd': '8'}
    category_desc = {'tzgg': '通知公告', 'gjjzc': '政策法规国家级', 'bjszc': '政策法规北京市',
                     'hdqzc': '政策法规海淀区', 'zcjd': '政策法规解读', 'xyqyw': '园区要闻', 'qyzx': '前沿资讯', 'mtbd': '媒体报道'}
    url_descs = ['通知公告', '政策法规国家级', '政策法规北京市', '政策法规海淀区', '政策法规解读', '园区要闻', '前沿资讯', '媒体报道']
    base_url = 'http://hdy.bjhd.gov.cn'


    def parse(self, response):
        print("##########", response.url)
        if response.status == 200:
            id_prefix = ''
            cate = ''
            if response.url in self.start_urls:
                cate_index = self.start_urls.index(response.url)
                id_prefix = str(self.index) + '-' + str(cate_index + 1)
                cate = self.url_descs[cate_index]
                total_count_desc = response.css('span#page script::text').extract_first()
                if total_count_desc:
                    total_count = re.findall('countPage = (.*?)\/\/', total_count_desc)
                    print(total_count)
                    if total_count:
                        for pagenum in range(1, int(total_count[0])):
                            url = response.url.replace('index.htm', 'index_%s.htm' % pagenum)
                            yield scrapy.Request(url, meta={'id_prefix': id_prefix, 'category': cate},
                                                 callback=self.parse)
            else:
                id_prefix = response.meta['id_prefix']
                cate = response.meta['category']
            links = response.css('dl.Newslist dd')
            if links:
                for link in links:
                    url = link.css('a::attr("href")').extract_first().strip()
                    title = link.css('a::attr("title")').extract_first()
                    date = link.css('span::text').extract_first().strip()[1:-1]
                    if not url.startswith('http'):
                        url = response.url[0:response.url.rfind('/')] + url[1:]
                    print(url, title, date)
                    yield scrapy.Request(url, meta={'id_prefix': id_prefix,
                                                    'category': cate,
                                                    'title': title, 'date': date}, callback=self.parse_content)
                    time.sleep(random.randint(1, 6))

    def parse_content(self, response):
        print("^^^^^^", response.url)
        if response.status == 200:
            self.page_num = self.page_num + 1
            print("page num:", self.page_num)
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

            source_desc = response.css('div.main_ct p::text').extract_first()
            if source_desc:
                source_content = re.findall('信息来源：(.*)$', source_desc)
                if source_content:
                    item['source'] = source_content[0]

            item['content'] = ''
            details = response.css('div.zhengwen').extract_first()
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
                attch_url = response.url[0:response.url.rfind('/')] + attch.css(
                    '::attr("href")').extract_first().strip()[1:]
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
