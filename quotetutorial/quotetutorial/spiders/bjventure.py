# -*- coding: utf-8 -*-
import scrapy
import re
import time
import random
import hashlib
from quotetutorial.items import ScrapyItem
import requests
import os


# 首都创业孵化生态网
class BjventureSpider(scrapy.Spider):
    index = 20
    name = 'bjventure'
    allowed_domains = ['www.bjventure.com.cn']
    start_urls = [
          'http://www.bjventure.com.cn/www/more/TZGG001.htm',
    #     'http://www.bjventure.com.cn/www/more/KJZC001.htm',
    #     'http://www.bjventure.com.cn/www/more/KJZC002.htm',
    #     'http://www.bjventure.com.cn/www/more/KJZC003.htm'
       ]
    category_index = {'TZGG001': '1',
                      # 'KJZC001': '2', 'KJZC002': '3', 'KJZC003': '4'
                      }
    category_desc = {'TZGG001': '通知公告',
                     # 'KJZC001': '政策法规-国家', 'KJZC002': '政策法规-北京', 'KJZC003': '政策法规-促进发展'
                     }
    url_descs = ['通知公告', '政策法规-国家', '政策法规-北京', '政策法规-促进发展']
    base_url = 'http://www.bjventure.com.cn'

    def parse(self, response):
        print("##########", response.url)
        if response.status == 200:
            id_prefix = ''
            cate = ''
            if response.url in self.start_urls:
                cate_index = self.start_urls.index(response.url)
                id_prefix = str(self.index) + '-' + str(cate_index + 1)
                cate = self.url_descs[cate_index]
                total_count_desc = response.css('div.page a')
                # if len(total_count_desc)>3:
                #     total_num = total_count_desc[-3].css('::text').extract_first().strip()
                #     if total_num:
                #         for page_num in range(2, int(total_num) + 1):
                #             url = response.url+'?currentPage=%s' % page_num
                #             yield scrapy.Request(url, meta={'id_prefix': id_prefix, 'category': cate},
                #                                  callback=self.parse)
                #             time.sleep(random.randint(1, 6))
            else:
                id_prefix = response.meta['id_prefix']
                cate = response.meta['category']

        links = response.css("div.right > div.main ul li")
        for link in links:
            href = link.css('a::attr("href")').extract_first()
            if href.startswith('http'):
                url = href
            else:
                url = self.base_url + href
            title = link.css('a::attr("title")').extract_first().strip()
            date = link.css('span.datelink::text').extract_first().strip()
            print(url, title)
            if url:
                yield scrapy.Request(url, meta={'id_prefix': id_prefix,
                                                'category': cate,
                                                'title': title, 'date': date}, callback=self.parse_content)
                time.sleep(random.randint(1, 6))

    def parse_content(self, response):
        if response.status == 200:
            print("^^^^^^", response.url)
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
            #     # div.detail  div.detail_con>div.TRS_Editor
            item['content'] = ''
            details = response.css('div.center div.content-win').extract_first()
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
                href_attch = attch.css('::attr("href")').extract_first()
                if href_attch.startswith('http'):
                    attch_url = href_attch
                else:
                    attch_url = self.base_url + href_attch
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
