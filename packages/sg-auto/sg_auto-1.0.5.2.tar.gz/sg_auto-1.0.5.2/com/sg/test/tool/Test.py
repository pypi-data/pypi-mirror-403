from com.sg.u.autoParams import AutoParams


class Test:

    def changeRiskTool(self, request: AutoParams):
        print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        request.setInfo("hahhahahahhahahahha")
        request.putParam("aaaa", "12345678")
        re = request.querySql("select * from otoc_store.t_sales_bind_store where store_no='SH202312111345434656'")
        request.putParam("query", re)


if __name__ == '__main__':
    sql='INSERT INTO otoc_store.t_sales_bin'
    des='新增' if sql.strip().lower().startswith("insert") else '更新'
    print(des)
