# -*- coding: utf-8 -*-
import scrapy
import re
import math
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
from quotetutorial.items import ScrapyItem
import os


# 北京市科学技术委员会
class BjkwSpider(scrapy.Spider):
    name = 'bjkw'
    index = '3'
    allowed_domains = ['bjkw.gov.cn']
    category_index = {'col19': '1', 'col363': '2', 'col362': '3', 'col982': '4', 'col365': '5',
                      'col366': '6'}
    category_desc = {'col19': '通知公告', 'col363': '央地协同', 'col362': '三城一区', 'col982': '高精尖产业', 'col365': '开放创新',
                     'col366': '深化改革'}
    base_url = 'http://www.bjkw.gov.cn'
    download_url_prefix = 'http://jxw.beijing.gov.cn'
    start_urls = [
    'http://www.bjkw.gov.cn/col/col19/index.html',
                  'http://www.bjkw.gov.cn/col/col363/index.html',
                  'http://www.bjkw.gov.cn/col/col362/index.html',
                  'http://www.bjkw.gov.cn/col/col982/index.html',
                  'http://www.bjkw.gov.cn/col/col365/index.html',
                  'http://www.bjkw.gov.cn/col/col366/index.html'
                  ]
    allnum = 0
    allindexnum = 0

    def parse(self, response):
        if response.status == 200:
            detail_page_arra = []
            if response.url.endswith('index.html'):
                index_page = re.match('.*/(.*?)/index.htm', response.url)
                print(self.category_index.get(index_page.group(1), '0')+"::"+str(index_page))
                id_prefix = ''
                category = ''
                if index_page:
                    try:
                        id_prefix = self.index + "-" + self.category_index.get(index_page.group(1), '0')
                        category = self.category_desc.get(index_page.group(1), '')
                    except AttributeError as error:
                        return

                uid = re.findall('unitid:\'(.*?)\',', response.text)
                totalRecord = re.findall('totalRecord:(.*?),', response.text)
                perPage = re.findall('perPage:(.*?),', response.text)
                print(response.url, "uid:", uid[0], "总条数:", totalRecord[1], " 每页条数：", perPage[1], " 总页数：",
                      math.ceil(int(totalRecord[1]) / int(perPage[1])))
                all_page_num = math.ceil(int(totalRecord[1]) / int(perPage[1]))
                # for pageNum in range(1, all_page_num + 1):
                pageNum = 1
                while pageNum < all_page_num+1:
                    # for pageNum in range(1, 5):
                    driverTmp = webdriver.PhantomJS()
                    url = response.url
                    if pageNum != 1:
                        url = response.url + '?uid=' + uid[0] + "&pageNum=" + str(pageNum)
                    try:
                        driverTmp.get(url)
                        print("*********", url)
                        try:
                            element = WebDriverWait(driverTmp, 10).until(
                                EC.presence_of_element_located((By.CLASS_NAME, "default_pgContainer"))
                            )
                        except Exception as errorTmp:
                            print("++++++++++++++++", errorTmp)
                            continue
                        default_pgContainer = driverTmp.find_element_by_class_name('default_pgContainer')

                        # time.sleep(random.randint(1,3))
                        try:
                            element = WebDriverWait(driverTmp, 3).until(
                                EC.presence_of_element_located((By.TAG_NAME, "a"))
                            )
                        except Exception as errorTmp2:
                            print("++++++++++++++++", errorTmp2)
                            continue
                        tt = default_pgContainer.find_elements_by_tag_name('a')
                        if len(tt) == 0:
                            print(driverTmp.page_source)
                            time.sleep(random.randint(1, 3))
                            continue
                        for ele in tt:
                            try:
                                detail_page_arra.append(ele.get_attribute('href'))
                            except Exception as error1:
                                print(error1)
                        time.sleep(random.randint(1, 3))
                    except Exception as error2:
                        print("..........", error2)
                    driverTmp.close()
                    pageNum = pageNum + 1
                    time.sleep(random.randint(1, 6))
            print(len(detail_page_arra))
            for part_url in detail_page_arra:
                yield scrapy.Request(part_url, meta={'id_prefix': id_prefix, 'category': category},
                                     callback=self.parse_detail_contents)
        else:
            pass

    def parse_detail_contents(self, response):
        if response.status == 200:
            item = ScrapyItem()

            id_prefix = response.meta['id_prefix']
            self.allnum = self.allnum + 1
            print(self.allnum, response.url)
            item['id'] = id_prefix + "-" + str(self.allnum)

            category = response.meta['category']
            item['category'] = category

            item['url'] = response.url

            title = re.findall('标题]>begin-->(.*?)<', response.text, re.S)
            print('标题：', title[0])
            item['title'] = title[0]

            desc = re.findall('发布日期：(.*?)<td align="center">信息来源：.*?信息来源]>begin-->(.*?)<.*?</td>', response.text, re.S)
            if desc:
                #print('发布日期：', re.sub('\r|\n|\t|</td>', '', desc[0][0]))
                item['published_date'] = re.sub('\r|\n|\t|</td>', '', desc[0][0])
                #print('来源：', desc[0][1])
                item['source'] = desc[0][1]
            else:
                item['published_date'] = ''
                item['source'] = ''

            dr = re.compile(r'<[^>]+>|end-->|begin-->', re.S)
            content = dr.sub('', response.css('.bt_content').extract_first())
            #print("内容：", content)
            item['content'] = content.strip().dd.replace(u'\xa0', '').replace(u'\u3000', '').replace(u'\r\n', '').replace(u'\t','')

           # print("___________________________________________________________")
            #print("附件：")
            href_arra = response.css('.bt_content p a::attr("href")').extract()
            attach_arra = response.css('.bt_content p a::text').extract()
            attach_path_arra = []
            i = 0
            while i < len(href_arra):
                attach_path_arra.append(self.base_url + href_arra[i])
                save_path = ''
                print(i, href_arra, attach_arra)
                if len(attach_arra)>0:
                    if attach_arra[i].rfind('.') == -1:
                        save_path = save_path + attach_arra[i] + href_arra[i][href_arra[i].rfind('.'):]
                    else:
                        save_path = save_path + attach_arra[i]

                    self.download_file(self.base_url + href_arra[i], save_path)
                else:
                    pass
                i = i + 1



            #print(attach_path_arra)
            item['attchment_path'] = ','.join(attach_path_arra)
            #print(attach_arra)
            item['attchment'] = ','.join(attach_arra)


            view_url = response.css('#c tr span script::attr("src")').extract_first()

            if view_url:
                view_rq = requests.get(self.base_url + view_url)
                if view_rq.status_code == 200:
                    view_desc = re.match('.*?\"(\d*?)\"', view_rq.text)
                    view_count = view_desc.group(1)
                    #print('浏览次数:', view_count)
                    item['view_count'] = view_count
                else:
                    print('查询浏览次数失败')
                    item['view_count'] = '0'
            else:
                print('无法获取浏览次数')
                item['view_count'] = '0'
            #yield item

        else:
            pass

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
