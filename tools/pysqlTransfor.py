# -*- coding: utf-8 -*-
import pymysql

# 打开数据库连接
db = pymysql.connect(host='localhost', user='root', password='123456', database='dcreation', charset='utf8')

# db_org = pymysql.connect(host='172.27.35.1', user='root', password='123465', database='dcreation',charset='utf8')
# 使用 cursor() 方法创建一个游标对象 cursor
# cursor = db.cursor()
# cursor_org = db_org.cursor()

# 使用 execute()  方法执行 SQL 查询
# cursor.execute("select * from scrapy_item limit 10")
# result=cursor.fetchall()
# for row in result:
#         print(row[0], row[1], row[2], row[3], row[7],row[8], row[9], row[10], row[11], row[12], row[13], row[14],sep='\t')
# db.close()
# cursor_org.execute("select * from scrapy_item")
try:
    cursor=db.cursor()
    sql="select * from scrapy_item"
    cursor.execute(sql)
    result=cursor.fetchall()
    for row in result:
        print(row[0],':',row[8],':',row[9])
        cursor.execute(
                """select * from scrapy_data where url = %s""",row[8])
        # 是否有重复数据
        repetition = cursor.fetchone()
        # 重复
        if repetition:
            print('*************',row)
            pass
        else:
            cursor.execute(
                        """insert into scrapy_data(id, title, source, published_date, content, attchment, attchment_path, category, url, author,view_count,praise_num,pl_num,share_num)
                        value (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                        (row[14],
                         row[1],
                         row[2],
                         row[3],
                         row[4],
                         row[5],
                         row[6],
                         row[7],
                         row[8],
                         row[9],
                         row[10],
                         row[11],
                         row[12],
                         row[13]
                         ))
            db.commit()

finally:
    db.close();

# try:
#     with db_org.cursor() as cursor_org:
#         sql="select * from scrapy_item limit 10"
#         cursor_org.execute(sql)
#         result=cursor_org.fetchall()
#     for row in result:
#             print(row[0], row[1], row[2], row[3], sep='\t')
# finally:
#     db_org.close()


# 使用 fetchone() 方法获取单条数据.
# data = cursor.fetchone()
#
#
# print("Database version : %s " % data)

# 关闭数据库连接
# db.close()
