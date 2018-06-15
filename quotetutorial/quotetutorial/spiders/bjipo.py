# -*- coding: utf-8 -*-
import scrapy
import re
import time
import random
import hashlib
from quotetutorial.items import ScrapyItem
import requests
import os

# 国家知识产权局北京代办处
class BjipoSpider(scrapy.Spider):
    index = 36
    name = 'bjipo'
    allowed_domains = ['daibanchu.bjipo.gov.cn']
    start_urls = [
        'http://daibanchu.bjipo.gov.cn/nlist.aspx?c=03&Page=1',
        'http://daibanchu.bjipo.gov.cn/nlist.aspx?c=04&Page=1',
        'http://daibanchu.bjipo.gov.cn/nlist.aspx?c=05&Page=1',
        'http://daibanchu.bjipo.gov.cn/nlist.aspx?c=06&Page=1',
        'http://daibanchu.bjipo.gov.cn/nlist.aspx?c=07&Page=1',
        'http://daibanchu.bjipo.gov.cn/nlist.aspx?c=08&Page=1',
    ]
    category_index = {
        '03': '1',
                      '04': '2', '05': '3', '06': '4', '07': '5', '08': '6'}
    category_desc = {
        '03': '通知公告',
                     '04': '法律法规', '05': '司法解释', '06': '相关政策', '07': '国际条约', '08': '规章办法'}
    url_descs = [
        '通知公告' ,
        '法律法规','司法解释','相关政策','国际条约','规章办法']
    base_url = 'http://daibanchu.bjipo.gov.cn'


    def parse(self, response):
        print("**********", response.url)
        if response.status == 200:
            id_prefix = ''
            cate = ''
            if response.url in self.start_urls:
                cate_index = self.start_urls.index(response.url)
                id_prefix = str(self.index) + '-' + str(cate_index + 1)
                cate = self.url_descs[cate_index]
                page_num_desc = response.css(
                    'div.fanye ul.fanye_li li[title="末页"] a::attr("href")').extract_first().strip()
                if page_num_desc:
                    pages = page_num_desc[page_num_desc.rfind("=") + 1:]
                    for page in range(2, int(pages) + 1):
                        url = response.url[0:response.url.rfind("=") + 1] + str(page)
                        yield scrapy.Request(url, meta={'id_prefix': id_prefix, 'category': cate}, callback=self.parse)
            else:
                id_prefix = response.meta['id_prefix']
                cate = response.meta['category']

            # print(response.css('div.sub_ri1.w_r ul.srlb li').extract())
            info_list = response.css('div.sub_ri1.w_r ul.srlb li')
            for info in info_list:
                title = info.css('a::text').extract_first().replace(u'\xa0', '')
                if title.find('[置顶]') != -1:
                    title = title[title.find('[置顶]') + 8:].strip()
                href = self.base_url + info.css('a::attr("href")').extract_first()
                date = info.css('span::text').extract_first().strip()[1:-1]
                print("title:", title, 'href:', href, 'date:', date)
                yield scrapy.Request(href, meta={'id_prefix': id_prefix,
                                                 'category': cate,
                                                 'title': title, 'date': date}, callback=self.parse_content)
                time.sleep(random.randint(1, 6))

        # print(response.css('div.sub_ri1.w_r ul.srlb li').extract())
        # page_num_desc = response.css('div.fanye ul.fanye_li li[title="末页"] a::attr("href")').extract_first().strip()
        # print(page_num_desc[page_num_desc.rfind("=")+1:])
        # print(response.css('div.fanye ul.fanye_li li[title="末页"] a::attr("href")').extract_first())

    def parse_content(self, response):
        # print("#########", response.css('div.detail_content.clearfix').extract())
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
            details = response.css('div.detail_content.clearfix').extract_first()
            if details:
                dr = re.compile(r'<[^>]+>', re.S)
                dd = dr.sub('', details)
                item['content'] = dd.replace(u'\u3000', '').replace(u'\t', '').replace(u'\xa0', '').replace(u'\n',
                                                                                                            '').strip()
            item['view_count'] = '0'
            item['url'] = response.url
            attach_path_arra = []
            attach_arra = []
            atta_arra = response.css('a[href*=".xls"]') + response.css('a[href*=".doc"]') + response.css(
                'a[href*=".pdf"]')
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
