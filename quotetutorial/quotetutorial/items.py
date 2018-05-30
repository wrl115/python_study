# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class ScrapyItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    # 编号
    id = scrapy.Field()
    # 标题
    title = scrapy.Field()
    # 来源
    source = scrapy.Field()
    # 发布日期
    published_date = scrapy.Field()
    # 内容
    content = scrapy.Field()
    # 附件
    attchment = scrapy.Field()
    # 附件路径
    attchment_path = scrapy.Field()
    # 分类
    category = scrapy.Field()
    # 路径
    url = scrapy.Field()
    # 浏览次数
    view_count = scrapy.Field()
