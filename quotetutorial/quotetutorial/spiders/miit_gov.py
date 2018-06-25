# -*- coding: utf-8 -*-
import scrapy
import re
import math
import time
import random

from attr._make import _AndValidator
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
from quotetutorial.items import ScrapyItem
import os
import hashlib


class MiitGovSpider(scrapy.Spider):
    index = 28
    name = 'miit_gov'
    allowed_domains = ['www.miit.gov.cn']
    start_urls = [
        'http://www.miit.gov.cn/n1146295/n1146557/index.html',
        'http://www.miit.gov.cn/n1146290/n1146392/index.html',
        'http://www.miit.gov.cn/n1146290/n1146397/index.html',
        'http://www.miit.gov.cn/n1146290/n4388791/index.html',
        'http://www.miit.gov.cn/n1146290/n1146402/index.html',
        'http://www.miit.gov.cn/n1146290/n1146407/index.html'
    ]
    category_index = {'n1146557': '1','n1146392': '2','n1146397': '3','n4388791': '４','n1146402': '5','n1146407':'6'}
    category_desc = {'n1146557': '法律法规','n1146392': '时政要闻','n1146397': '领导活动','n4388791': '重点要闻',
                     'n1146402': '工作动态','n1146407':'对外交流'}
    url_descs = ['法律法规','时政要闻','领导活动','重点要闻','工作动态','对外交流']
    base_url = "http://www.miit.gov.cn"

    def parse(self, response):
        if response.status == 200:
            id_prefix = ''
            cate = ''
            if response.url in self.start_urls:
                cate_index = self.start_urls.index(response.url)
                id_prefix = str(self.index) + '-' + str(cate_index + 1)
                cate = self.url_descs[cate_index]
                # all page num
                script_desc = response.css('script').extract()
                if script_desc:
                    page_script = script_desc[-2]
                    all_page_desc = re.findall('maxPageNum = (.*?);',page_script)
                    if all_page_desc:
                        page_num = all_page_desc[0]
                    base_href_desc = re.findall('purl="(.*?)"',page_script)
                    if base_href_desc and page_num:
                        for page_index in range(1,int(page_num)):
                            url = self.base_url+base_href_desc[0][5:]+'_%s'%page_index+'.html'
                            print(url)
                            yield scrapy.Request(url, meta={'id_prefix': id_prefix, 'category': cate},
                                                     callback=self.parse)
                            #
                            time.sleep(random.randint(1,6))
                # driverTmp = webdriver.PhantomJS()
                # driverTmp.get(response.url)
                # try:
                #     WebDriverWait(driverTmp, 10).until(
                #         EC.presence_of_element_located((By.XPATH, '//a[text()="下页"]'))
                #     )
                #     default_pgContainer = driverTmp.find_element_by_id('pag_1274678')
                #     pages = default_pgContainer.find_elements_by_xpath('//a')
                #
                #     for page in pages:
                #         if page.text.isdigit():
                #             href_desc = page.get_attribute('href')
                #             href = re.findall('goPub\(\'(.*?)\'\)', href_desc)
                #             if href:
                #                 print(self.base_url + href[0][5:])
                #                 url = self.base_url + href[0][5:]
                #                 yield scrapy.Request(url, meta={'id_prefix': id_prefix, 'category': cate},
                #                                      callback=self.parse)
                #     driverTmp.close()
                # except Exception as e:
                #     print(e)
                #     driverTmp.close()
            else:
                id_prefix = response.meta['id_prefix']
                cate = response.meta['category']

            links = response.css('div.clist_con li')
            for link in links:
                href = link.css('a:first-child::attr("href")').extract_first()
                if href.startswith('http'):
                    url = href
                else:
                    url = self.base_url + href[5:]
                title = link.css('a:first-child::text').extract_first().strip()
                date = link.css('span>a::text').extract_first().strip()
                print(title,date)
                if url:
                    yield scrapy.Request(url, meta={'id_prefix': id_prefix,
                                                    'category': cate,
                                                    'title': title,
                                                    'date': date}, callback=self.parse_content)
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
            source_desc = response.css('div.cinfo.center>span::text').extract()
            if len(source_desc) >= 2:
                source = re.findall('来源：(.*?)$', source_desc[1])
                if source:
                    item['source'] = source[0].strip()

            item['content'] = ''
            details = response.css('div#con_con').extract_first()
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
                    attch_url = self.base_url + href_attch[11:]
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
