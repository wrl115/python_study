# -*- coding: utf-8 -*-
import scrapy
import re
import time
import random
import requests
from quotetutorial.items import ScrapyItem
import os


# 北京市经济和信息化委员会
class JxwSpider(scrapy.Spider):
    name = 'jxw'
    index = '4'
    category_index = {'tzgg': '1', 'gjzc': '2', 'bjszc': '3'}
    category_desc = {'tzgg': '通知公告', 'gjzc': '国家政策', 'bjszc': '北京市政策'}

    allowed_domains = ['jxw.beijing.gov.cn']
    start_urls = ['http://jxw.beijing.gov.cn/jxdt/tzgg/index.htm',
                  'http://jxw.beijing.gov.cn/zcjd/zcwj/gjzc/index.htm',
                  'http://jxw.beijing.gov.cn/zcjd/zcwj/bjszc/index.htm']

    def parse(self, response):
        if response.status == 200:

            index_page = re.match('^.*?/index(.*?).htm', response.url)
            # 判断是否索引页面
            if index_page:
                for href in response.css('ol.xxk_txt > li > a::attr("href")'):
                    # time.sleep(random.randint(1, 3))
                    url = response.url[0:response.url.find('/index') + 1] + href.extract()
                    yield scrapy.Request(url, callback=self.parse_detail_contents)
                # 判断是否是首页
                if index_page.group(1).isdigit():
                    pass
                else:
                    for page_num in range(1, len(response.css('.paginglf select option'))):
                        # time.sleep(random.randint(1, 3))
                        url = response.url[0:response.url.find('/index') + 1] + 'index' + str(page_num) + '.htm'
                        yield scrapy.Request(url, callback=self.parse)
            else:
                pass
        else:
            print("page error!!!")

    def parse_detail_contents(self, response):
        index_page = re.match('^.*?/index(.*?).htm', response.url)
        # 过滤index页面
        if index_page:
            print('error page---index url:', response.url)
            return
        if response.status == 200:

            item = ScrapyItem()
            categoryTmp = re.match('^http://jxw.beijing.gov.cn/(.*)/(.*?)/(.*?).htm', response.url)
            try:
                item['id'] = self.index + categoryTmp.group(2) + categoryTmp.group(3)
                item['category'] = self.category_desc.get(categoryTmp.group(2), 'no')
            except AttributeError as error:
                return

            # print("路径：------", response.url)
            item['url'] = response.url

            # print("标题：------", response.css('h4::text').extract_first().strip())
            item['title'] = response.css('h4::text').extract_first().strip()

            short_desc = response.css('.text_ly-lf::text').extract_first()
            # print("来源：------", short_desc[short_desc.find('来源：') + 3:short_desc.find('发布日期：')].strip())
            item['source'] = short_desc[short_desc.find('来源：') + 3:short_desc.find('发布日期：')].strip()

            # print("发布日期：------", short_desc[short_desc.find('发布日期：') + 5:].strip())
            item['published_date'] = short_desc[short_desc.find('发布日期：') + 5:].strip()

            # content
            # print("---------------------------------------------")
            dr = re.compile(r'<[^>]+>', re.S)
            dd = dr.sub('', response.css('.txt').extract_first())
            # dd.replace(u'\xa0', u' ').replace()
            # print("内容：------", dd.strip())
            # print("---------------------------------------------")
            item['content'] = dd.replace(u'\xa0', '').replace(u'\u3000', '').replace(u'\r\n', '').replace(u'\t',
                                                                                                          '').strip()

            # print("附件：--------------------")
            attchment = []
            attchment_path = []
            # item['attchment'] = ''
            # item['attchment_path'] = ''
            for down_url_html in response.css('.downtxt p .clor').extract():
                paras = re.match(r'^<a href="../..(.*?)" class="clor">(.*?)</a>', down_url_html)
                if paras:
                    # print("附件路径：--------------------", self.download_url_prefix + paras.group(1))
                    attchment_path.append(self.download_url_prefix + paras.group(1))
                    # print("附件名称：--------------------", paras.group(2), '****',
                    # paras.group(1)[paras.group(1).rfind('.'):])

                    save_path = ''
                    if paras.group(2).rfind('.') == -1:
                        save_path = save_path + paras.group(2) + paras.group(1)[paras.group(1).rfind('.'):]
                    else:
                        save_path = save_path + paras.group(2)
                    # print("保存路径：--------------------", save_path)
                    attchment.append(save_path)

                    self.download_file(self.download_url_prefix + paras.group(1), save_path)
                    time.sleep(random.randint(1, 3))

            # print("附件：--------------------",
            # response.css('.downtxt    .clor::attr("href")').extract_first(), response.css('.downtxt p .clor::text').extract_first())
            # for down_url in response.css('.downtxt p').extract()
            # print(item)
            item['attchment'] = ','.join(attchment)
            item['attchment_path'] = ','.join(attchment_path)
            yield item
        else:
            print("parse_detail_contents error!!!!")

    def download_file(self, url, local_path):
        if os.path.exists(local_path):
            print("the %s exist" % local_path)
        else:
            print("start download the file", url)
            r = requests.get(url)
            # try:
            # r.raise_for_status()
            print('down loading status ', r.status_code)
            # if r.status_code == 200:
            with open(local_path, "wb") as code:
                code.write(r.content)
                # print("write file success!!")
            # except Exception as exc:
            # print("downloading %s failure!!!" % url)

