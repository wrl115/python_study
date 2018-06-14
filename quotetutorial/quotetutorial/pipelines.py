# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import pymysql

class QuotetutorialPipeline(object):

    def process_item(self, item, spider):
        return item


class DBPipeline(object):
    def __init__(self):
        # 连接数据库
        self.connect = pymysql.connect(
            host='localhost',
            port=3306,
            db='dcreation',
            user='root',
            passwd='123465',
            charset='utf8',
            use_unicode=True)

        # 通过cursor执行增删查改
        self.cursor = self.connect.cursor();

    def process_item(self, item, spider):

        print(item)
        try:
            # 查重处理
            self.cursor.execute(
                """select * from scrapy_item where id = %s""",
                item['id'])
            # 是否有重复数据
            repetition = self.cursor.fetchone()
            # 重复
            if repetition:
                pass
            else:
                # 插入数据
                if not item['praise_num']:
                    self.cursor.execute(
                        """insert into scrapy_item(id, title, source, published_date, content, attchment, attchment_path, category, url, view_count)
                        value (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                        (item['id'],
                         item['title'],
                         item['source'],
                         item['published_date'],
                         item['content'],
                         item['attchment'],
                         item['attchment_path'],
                         item['category'],
                         item['url'],
                         item['view_count']))
                else:
                    print("****************insert huxiu data")
                    self.cursor.execute(
                        """insert into scrapy_item(id, title, source, published_date, content, attchment, attchment_path, category, url, view_count,author,praise_num,pl_num,share_num)
                        value (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                        (item['id'],
                         item['title'],
                         item['source'],
                         item['published_date'],
                         item['content'],
                         item['attchment'],
                         item['attchment_path'],
                         item['category'],
                         item['url'],
                         item['view_count'],
                         item['author'],
                         item['praise_num'],
                         item['pl_num'],
                         item['share_num']
                         ))

            # 提交sql语句
            self.connect.commit()

        except Exception as error:
            # 出现错误时打印错误日志
           print("********", error)
        return item
