# -*- coding: utf-8 -*-
import scrapy
from urllib import parse
from scrapy.http import Request
import re
from quotetutorial.items import ScrapyItem
import os
import requests


# 中关村国家自主创新示范区
class JobboleSpider(scrapy.Spider):
    name = 'zgc_noticeBulletin'
    index = '1'
    category_index = {'tzgg': '1', 'gj': '2', 'bjs': '3', 'sfq': '4', 'sfqzcjd': '5', 'gzdt': '6'}
    category_desc = {'tzgg': '通知公告', 'gj': '国家政策法规', 'bjs': '政策法规', 'sfq': '示范区政策法规', 'sfqzcjd': '政策解读', 'gzdt': '工作动态'}
    allowed_domains = ['www.zgc.gov.cn/']
    download_url_prefix = 'http://www.zgc.gov.cn'
    start_urls = ['http://www.zgc.gov.cn/zgc/zwgk/tzgg/index.html',
                  'http://www.zgc.gov.cn/zgc/zwgk/zcfg18/gj/index.html',
                  'http://www.zgc.gov.cn/zgc/zwgk/zcfg18/bjs/index.html',
                  'http://www.zgc.gov.cn/zgc/zwgk/zcfg18/sfq/index.html',
                  'http://www.zgc.gov.cn/zgc/zwgk/zcfg18/sfqzcjd/index.html',
                  'http://www.zgc.gov.cn/zgc/yw/gzdt/index.html']

    # start_urls = ['http://www.zgc.gov.cn/zgc/yw/gzdt/index.html']

    def parse(self, response):
        pt_urls = response.xpath('//div[@class="w_ul_list"]/ul/li')
        for url in pt_urls:
            a_text = url.css("span a::text").extract()
            a_url = url.css("span a::attr(href)").extract()
            long_url = parse.urljoin(response.url, a_url[0])
            date_text = url.css(".fr::text").extract()
            # print('标题：' + a_text[0] + '  发布日期：' + date_text[0] + '  url：' + long_url)
            yield Request(url=long_url, callback=self.parse_detail_contents, dont_filter=True)

        # 取下一页URL
        next_url = response.xpath("//div[@class=' windex']/a[3]").css("::attr(tagname)").extract_first("")
        next_url = parse.urljoin(response.url, next_url)
        print("next_url:" + next_url)
        if next_url:
            yield Request(url=parse.urljoin(response.url, next_url), callback=self.parse, dont_filter=True)

    def parse_detail_contents(self, response):
        item = ScrapyItem()
        #print("****", response.url)
        item['url'] = response.url
        cate_match = re.match('^http://(.*)/(.*?)/(.*?)/index.htm', response.url)
        item['id'] = self.index + '-'+str(self.category_index.get(cate_match.group(2)))+'-' + cate_match.group(3)
        item['category'] = self.category_desc.get(cate_match.group(2), 'no')
        describe = response.css('.easysite-news-describe').extract_first()
        #print("发布日期：", describe[describe.find('发布时间：') + 5:describe.find('信息来源：')].strip())
        item['published_date'] = describe[describe.find('发布时间：') + 5:describe.find('信息来源：')].strip()

        #print("信息来源：", describe[describe.find('信息来源：') + 5:describe.find('字体')].strip())
        item['source'] = describe[describe.find('信息来源：') + 5:describe.find('字体')].strip()

        #print("标题：", response.css('h2::text').extract_first())
        item['title'] = response.css('h2::text').extract_first().strip()

        dr = re.compile(r'<[^>]+>', re.S)
        dd = dr.sub('', response.css('.easysite-news-text').extract_first())
        #print("内容：", dd.replace(u'\xa0', '').replace(u'\u3000', '').replace(u'\n', '').replace(u'\t', '').replace(' ',
                                                                                                                  #'').strip())
        item['content'] = dd.replace(u'\xa0', '').replace(u'\u3000', '').replace(u'\n', '').replace(u'\t', '').replace(
            ' ', '').strip()

       # print("附件：", response.css('.easysite-news-text p a::text').extract())
        #attch_arra = response.css('.easysite-news-text p a::text').extract()
        attch_path_arra = response.css('.easysite-news-text p a').extract()
        temp_attch_path_arra=[]
        temp_attch_arra=[]
        for a_path in attch_path_arra:
            tmp=re.match(r'^<a href="(.*?)">(.*?)</a>', a_path)
            if tmp:
                #print(tmp.group(2)+"::" + dr.sub('', tmp.group(2)).strip())
                temp_attch_path_arra.append(self.download_url_prefix+tmp.group(1))
                temp_attch_arra.append(dr.sub('', tmp.group(2)).strip())

                self.download_file(self.download_url_prefix+tmp.group(1), dr.sub('', tmp.group(2)).strip())

        item['attchment'] = ','.join(temp_attch_arra)
        item['attchment_path'] = ','.join(temp_attch_path_arra)
        item['view_count'] = '0'
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
