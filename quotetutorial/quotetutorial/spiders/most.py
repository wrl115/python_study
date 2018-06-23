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


# 科学技术部
class MostSpider(scrapy.Spider):
    index = 12
    name = 'most'
    allowed_domains = ['www.most.gov.cn']
    start_urls = [
        'http://www.most.gov.cn/tztg/index.htm']
    category_index = {'tztg': '1'}
    category_desc = {'tztg': '通知公告-通知通告'}
    url_descs = ['通知公告-通知通告']

    def parse(self, response):
        print("##########", response.url)
        if response.status == 200:
            id_prefix = ''
            cate = ''
            if response.url in self.start_urls:
                cate_index = self.start_urls.index(response.url)
                id_prefix = str(self.index) + '-' + str(cate_index + 1)
                cate = self.url_descs[cate_index]
                total_count_desc = re.findall('countPage =(.*?)//共多少页', response.text)
                print('*********', total_count_desc)
                if total_count_desc:
                    for page_num in range(1, int(total_count_desc[0].strip())):
                        url = response.url.replace('index.htm', 'index_%s.htm' % page_num)
                        yield scrapy.Request(url, meta={'id_prefix': id_prefix, 'category': cate},
                                             callback=self.parse)
                        time.sleep(random.randint(1, 6))
            else:
                id_prefix = response.meta['id_prefix']
                cate = response.meta['category']

            links = response.css("td.STYLE30")
            for link in links:
                href = link.css('a::attr("href")').extract_first()
                url = ""
                if href.find('/') == 1:
                    url = response.url[0:response.url.rfind('/')] + link.css('a::attr("href")').extract_first()[1:]
                elif href.find('/') == 2:
                    url = response.url[0:response.url[0:response.url.rfind('/')].rfind('/')] + href[2:]
                title = link.css('a::text').extract_first().strip()
                print(url, title)
                if url:
                    yield scrapy.Request(url, meta={'id_prefix': id_prefix,
                                                    'category': cate,
                                                    'title': title}, callback=self.parse_content)
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

            item['published_date'] = ''
            date_desc = response.css('div.gray12.lh22::text').extract_first()
            if date_desc:
                print("##########", date_desc)
                date = re.findall('日期：(.*?)$', date_desc)
                if date:
                    date_str = date[0].strip()
                    timeStruct = time.strptime(date_str, "%Y年%m月%d日")
                    strTime = time.strftime("%Y-%m-%d", timeStruct)
                    item['published_date'] = strTime
            item['source'] = '科技部'
            # div.detail  div.detail_con>div.TRS_Editor
            item['content'] = ''
            conten_p = response.css('div.trshui13.lh22 p::text').extract()
            if conten_p:
                content_desc = ''.join(conten_p)
                item['content'] = content_desc.replace(u'\u3000', '').replace(u'\t', '').replace(u'\r', '').replace(
                    u'\xa0',
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
                attch_url = response.url[0:response.url.rfind("/")] + attch.css('::attr("href")').extract_first()[1:]
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
