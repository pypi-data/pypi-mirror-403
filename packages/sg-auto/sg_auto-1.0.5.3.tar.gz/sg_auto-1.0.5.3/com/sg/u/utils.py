import hashlib
import random
import json
from datetime import datetime, timedelta
import uuid
from dateutil.relativedelta import relativedelta
import os
import decimal

def randomxx(a, b):
    return random.uniform(a, b)


def writeText(path, dataList):
    file = open(path, "w")
    for s in dataList:
        file.write(s + '\n')
    file.close()


def writePfText(path, dataList):
    file = open(path, "w")
    for s in dataList:
        req = json.loads(s['req'])
        file.write(req[0] + '\n')
    file.close()


def writePfTextOne(path, text):
    file = open(path, "a")
    file.write(text + '\n')
    file.close()


def writeLog(text):
    print(text)
    # 1. 获取当前文件的绝对路径
    current_path = os.path.abspath(__file__)
    # 2. 获取当前文件所在的目录（项目根目录）
    project_root = os.path.dirname(current_path)
    # 3. 获取上一级目录
    parent_dir = os.path.dirname(project_root)
    # 4. 拼接 log 文件夹路径
    file_path = os.path.join(parent_dir, 'logs/python')
    # 5. 创建文件夹（如果不存在）
    os.makedirs(file_path, exist_ok=True)
    if os.path.exists(file_path):
        file = open(f"{file_path}/python-log{get_now_time('%Y%m%d')}.log", "a", encoding='utf-8')
        file.write(text + '\n')
        file.close()


def readText(path):
    data = []
    with open(path, 'r') as file:
        lines = file.readlines()
        for index, line in enumerate(lines):
            # print(line)
            if index != 0:
                data.append(line.replace('\n', ''))
    return data


def isEmpty(s):
    try:
        if s is None:
            return True
        elif not s:
            return True
        elif is_number(s):
            return False
        elif is_object(s):
            return len(s) == 0
        elif s.strip() == "":
            return True
        else:
            return False
    except:
        if len(s) == 0:
            return True
        else:
            return False


def isEmptyObject(s):
    if s is None:
        return True
    else:
        return False

def is_number(var):
    return type(var) in (int, float, complex) or type(var) is decimal.Decimal


def is_datetime(var):
    return type(var) is datetime


def is_str(var):
    return type(var) is str

def is_object(var):
    return type(var) in (list, dict, map, tuple)

def md5_hash(input_string):
    # 创建一个md5对象
    hash_object = hashlib.md5(input_string.encode())
    # 获取md5哈希的16进制字符串表示
    hex_dig = hash_object.hexdigest()
    return hex_dig


def get_now_time(format='%Y-%m-%d %H:%M:%S'):
    if format == '' or format == None:
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    else:
        return datetime.now().strftime(format)


def bu_zero(s, num):
    return str(s).zfill(num)


def get_timestamp():
    return int(datetime.now().timestamp())


def get_time_by_day(format, day=0):
    if day == '' or day == None:
        day = 0
    # 当前日期
    current_date = datetime.now()
    # 计算前day天的日期
    five_days_ago = current_date + timedelta(days=day)
    if format == '' or format == None:
        return five_days_ago.strftime('%Y-%m-%d %H:%M:%S')
    else:
        return five_days_ago.strftime(format)

def get_time_by_month(format, month=0):
    if month == '' or month == None:
        month = 0
    # 当前日期
    current_date = datetime.now()
    # 计算前day天的日期
    five_days_ago = current_date + relativedelta(months=month)
    if format == '' or format == None:
        return five_days_ago.strftime('%Y-%m-%d %H:%M:%S')
    else:
        return five_days_ago.strftime(format)

def uuid4(replace=""):
    return str(uuid.uuid4()).replace("-", replace)
