import pymysql

from com.sg.u import utils as u


class dbUtil:
    def __init__(self, dbBo: dict):

        self.conn = None if dbBo is None or len(dbBo) == 0 else pymysql.connect(
            host=dbBo['url'].split('?')[0].split('//')[1].split(':')[0],  # 数据库地址
            user=dbBo['userName'],  # 数据库用户名
            password=dbBo['password'],  # 数据库密码
            port=int(dbBo['url'].split('?')[0].split('//')[1].split(':')[1]),
            # db='api_test',
            charset='utf8'
        )
        self.cur = None if self.conn is None else self.conn.cursor()

    #def __del__(self):  # 析构函数，实例删除时触发


    def query(self, sql):
        if self.cur is None:
            return []
        self.cur.execute(sql)
        column_names = [column[0] for column in self.cur.description]
        results = []
        rows = self.cur.fetchall()
        # 遍历每一行
        for row in rows:
            result = {}
            # 遍历每个字段的值
            i = 0
            for field_value in row:
                result[column_names[i]] = field_value
                i += 1
            results.append(result)
        return results

    def queryTableHeader(self, sql):
        self.cur.execute(sql)
        column_names = [column[0] for column in self.cur.description]

        # 打印字段信息
        print('字段信息：')
        for name in column_names:
            print(name)

    def exec(self, sql):
        if self.cur is None:
            return None
        try:
            self.cur.execute(sql)
            self.conn.commit()
            return self.cur.rowcount
        except Exception as e:
            self.conn.rollback()
            u.writeLog(str(e))
            return None

    def checkConnect(self):
        return False if self.conn is None else True

    def close(self):
        if self.cur is not None:
            self.cur.close()
        if self.conn is not None:
            self.conn.close()

if __name__ == '__main__':
    # 创建连接
    url="jdbc:mysql://gz-cdb-3h872lmp.sql.tencentcdb.com:63975?useUnicode=true&characterEncoding=UTF-8&serverTimezone" \
        "=Asia/Shanghai&nullCatalogMeansCurrent=true".split("?")[0].split("//")[1].split(":")
    dbBo = {"domain": url[0],"port":url[1],"user":"otoctest","password":"cYgnuNEeM3"}
    print(dbBo)
    db = dbUtil(dbBo)
    # print(db.queryTableHeader("select * from otoc_store.t_sales_bind_store where store_no='SH202312111345434656'"))
    print(db.query("select * from otoc_store.t_sales_bind_store where store_no='SH202312111345434656'"))
