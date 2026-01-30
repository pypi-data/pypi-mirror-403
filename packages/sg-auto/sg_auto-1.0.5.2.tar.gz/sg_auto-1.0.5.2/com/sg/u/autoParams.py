from com.sg.u import utils as u
from com.sg.u.dbUtil import dbUtil as db
from com.sg.u.apiHttp import Http


class AutoParams:

    def __init__(self, dbBo, globalParam, resultInfo):
        self.__db_Bo = db(dbBo)
        self.__global_param = globalParam
        self.__result_info = resultInfo
        self.http = Http({})
        self.print_log = False
        self.write_log = False

    def querySql(self, sql):
        if sql is None or sql == '':
            self.setInfo(f"sql为空请检查!")
            return 0

        if self.__db_Bo.checkConnect():
            results = self.__db_Bo.query(sql)
            self.setInfo(f"查找到{len(results)}条数据sql:{sql}")
            return results
        else:
            self.setInfo("数据库未连接不执行sql请检查数据库配置:" + sql)
            return []

    def executeSql(self, sql):
        if sql is None or sql == '':
            self.setInfo(f"sql为空请检查!")
            return 0
        else:
            sql = sql.strip()
        if self.__db_Bo.checkConnect():
            des = '更新'
            if sql.lower().startswith("insert"):
                des = '新增'
            elif sql.lower().startswith("delete"):
                des = '删除'
            count = self.__db_Bo.exec(sql)
            if count is None:
                self.setError(f"未{des}任何数据请检查数据库链接sql:{sql}")
            else:
                self.setWarn(f"{des}{count}条数据sql:{sql}")
            return count
        else:
            self.setInfo("数据库未连接不执行sql请检查数据库配置:" + sql)
            return 0

    def getParam(self, key):
        try:
            return self.__global_param[key]
        except Exception as err:
            return None

    def putParam(self, key, value):
        self.__global_param[key] = value

    def setOut(self, s):
        self.__result_info["infos"].append("out:" + s)
        self.printLog("out:" + s)

    def setInfo(self, s):
        self.__result_info["infos"].append("info:" + s)
        self.printLog("info:" + s)

    def setWarn(self, s):
        self.__result_info["infos"].append("warn:" + s)
        self.printLog("warn:" + s)

    def setError(self, s):
        self.__result_info["errors"].append("error:" + s)
        self.__result_info["success"] = False
        self.__result_info["infos"].append("error:" + s)
        self.printLog("error:" + s)

    def printLog(self, s):
        if self.print_log:
            print(s)
        if self.write_log:
            u.writeLog(s)

    def openWriteLog(self, s):
        self.write_log = s

    def openPrintLog(self):
        self.print_log = True

    def getDbBo(self):
        return self.__db_Bo

    def getResultInfo(self):
        return self.__result_info

    def getGlobal(self):
        return self.__global_param

    def close(self):
        self.__db_Bo.close()

    def httpGet(self, url):
        if u.isEmpty(url):
            self.setWarn("url为空请检查")
            return {'code': 500, 'message': 'url为空请检查'}
        else:
            return self.http.get(url=url, log=self.print_log)

    def httpPost(self, url, json):
        if u.isEmpty(url):
            self.setWarn("url为空请检查")
            return {'code': 500, 'message': 'url为空请检查'}
        else:
            return self.http.post(url=url, json=json, log=self.print_log)

    def httpUpload(self, url, files, data):
        if u.isEmpty(url):
            self.setWarn("url为空请检查")
            return {'code': 500, 'message': 'url为空请检查'}
        else:
            return self.http.upload(url=url, files=files, data=data, log=self.print_log)

    def httpHeader(self, key, value):
        self.http.set_header(key=key, value=value)

    def httpGeHeader(self, key):
        if u.isEmpty(key):
            self.setWarn("key为空请检查")
            return ''
        else:
            return self.http.get_header(key)
