from flask import request, jsonify, Blueprint
from com.sg.u.autoParams import AutoParams as Param
import traceback
from com.sg.u import utils as u
import importlib

testxx = Blueprint("open", __name__)


@testxx.route('/test', methods=['POST', 'GET'])
def test():
    try:
        projectName = request.args.get('projectName', '')
        return {"a": u.randomxx(1, 10), "b": projectName}
    except Exception as err:
        return jsonify(result=None, error=f'{err}', code=500)

@testxx.route('/execute', methods=['POST', 'GET'])
def executeRun():

    api = request.json['api']
    globalMap = request.json["globalMap"]
    resultBuilder = request.json["resultBuilder"]
    dbUtil = request.json["dbBo"]
    config = {}
    #    u.writeLog(f"当前时间:{u.get_now_time( '' )} api= {api} ,globalMap={globalMap}进来了 ,dbUtil={dbUtil} ,resultBuilder={resultBuilder}")
    u.writeLog(f"当前时间:{u.get_now_time( '' )} api= {api} ,globalMap={globalMap}进来了")
    #print(request.headers)
    try:
        projectName = request.args.get('projectName', '')
        try:
            config = request.json["config"]
        except Exception as errl:
            u.writeLog(f"当前时间:{u.get_now_time('')}未获取到配置信息执行忽略操作:{errl}")
        #print("-------flask login----------projectName=" + projectName)
        if "#" in api["params"]:
          method= api["params"].split("#")
          api["method"]=method[1]
          methodPath=method[0].split(".")
          api["className"]=methodPath[len(methodPath)-1]
          api["params"]=method[0][0:len(method[0])-(len(api["className"])+1)]
          #api["params"] = method[0]

        class_name = api["className"]
        class_func_name = api["method"]
        xx1_module = importlib.import_module(api["params"])
        method = getattr(getattr(xx1_module, class_name)(), class_func_name)
        autoParams=Param(dbUtil,globalMap,resultBuilder)
        autoParams.setInfo(f"开始执行{class_name}......{u.get_now_time()}")
        autoParams.openWriteLog(s=config.get("openWriteLog",False))
        try:
            result = method(autoParams)
        except Exception as err:
            # 获取堆栈信息
            stack_trace = traceback.format_exc()
            u.writeLog(f"当前时间:{u.get_now_time('')}执行异常:{stack_trace}")
            autoParams.setError(f"{err}")
        autoParams.close()
        return {"a": u.randomxx(1, 10),"code": "200","data":{"api":None,"globalMap":autoParams.getGlobal(),"resultBuilder":autoParams.getResultInfo(),"dbBo":None}}
    except Exception as err:
        # 获取堆栈信息
        stack_trace = traceback.format_exc()
        u.writeLog(f"当前时间:{u.get_now_time('')}异常:{stack_trace}")
        return {"msg": err, "code": "500", "data": {"api": api}}
