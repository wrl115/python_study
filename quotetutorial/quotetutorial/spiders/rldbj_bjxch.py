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

# 西城区人力资源和社会保障局
class RldbjBjxchSpider(scrapy.Spider):
    index = 16
    name = 'rldbj_bjxch'
    allowed_domains = ['rlsbj.bjxch.gov.cn']
    start_urls = ['http://rlsbj.bjxch.gov.cn/RLSBJxwzx/RLSBJgggg.ycs',
                  'http://rlsbj.bjxch.gov.cn/RLSBJflfg.ycs']
    category_index = {'RLSBJgggg': '1', 'RLSBJflfg': '2'}
    category_desc = {'RLSBJgggg': '通知公告', 'RLSBJflfg': '政策法规' }
    url_descs = ['通知公告', '政策法规' ]
    base_url = 'http://rlsbj.bjxch.gov.cn'
    content_div_id = ['CNT_1055\/RLSBJxwzx\/RLSBJgggg\/14909\/14912\/14920', 'CNT_1055\/RLSBJflfg\/14860\/14863\/14890']

    def parse(self, response):
        print("##########", response.url)
        if response.status == 200:
            id_prefix = ''
            cate = ''
            if response.url in self.start_urls:
                cate_index = self.start_urls.index(response.url)
                id_prefix = str(self.index) + '-' + str(cate_index + 1)
                cate = self.url_descs[cate_index]
                total_count_id = 'div#' + self.content_div_id[cate_index] + '>table:nth-child(2) form font::text'
                total_count_desc = response.css(total_count_id).extract_first()
                if total_count_desc:
                    for pagenum in range(2, int(total_count_desc)):
                        yield scrapy.FormRequest(
                            url=response.url,
                            formdata={"page_num": str(pagenum)},
                            callback=self.parse
                        )
                        time.sleep(random.randint(1, 6))
                    pass
            else:
                id_prefix = response.meta['id_prefix']
                cate = response.meta['category']
            link_id = 'div#' + self.content_div_id[self.url_descs.index(cate)] + '>table:nth-child(1)>tr'
            links = response.css(link_id)
            print(link_id, len(links))
            for link in links:
                url = self.base_url + link.css('a')[0].css('::attr("href")').extract_first()
                title = link.css('a')[0].css('::text').extract_first()
                date = link.css('a')[1].css('::text').extract_first()
                print(title, date)
                yield scrapy.Request(url, meta={'id_prefix': id_prefix,
                                                'category': cate,
                                                'title': title, 'date': date}, callback=self.parse_content)
                time.sleep(random.randint(1, 6))

    def parse_content(self, response):
        print("^^^^^^", response.url)
        # CNT_1055\/RLSBJxinxixiangxi\/6641
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
            details = response.css('div#CNT_1055\/RLSBJxinxixiangxi\/6641').extract_first()
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
