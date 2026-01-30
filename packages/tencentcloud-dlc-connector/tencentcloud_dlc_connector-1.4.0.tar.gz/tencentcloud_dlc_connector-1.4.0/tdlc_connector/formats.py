from datetime import datetime, date, time, timedelta, timezone
from time import localtime
from decimal import Decimal, getcontext
from typing import Sequence
from tdlc_connector import  exceptions, constants


import json
import re
import logging

LOG = logging.getLogger(__name__)

# FORMAT_DATE = "{0.year:04}-{0.month:02}-{0.day:02}"
# FORMAT_TIME = "{0.hour:02}:{0.minute:02}:{0.second:02}"
# FORMAT_TIME_MILLISECOND = FORMAT_TIME + ".{0.microsecond:03}" # DLC 目前只支持到 millisecond
# FORMAT_DATETIME = FORMAT_DATE + " " + FORMAT_TIME
# FORMAT_DATETIME_MILLISECOND = FORMAT_DATE + " " + FORMAT_TIME_MILLISECOND

FORMAT_DATE = "%Y-%m-%d"
FORMAT_TIME = "%H:%M:%S"
FORMAT_TIME_MILLISECOND = FORMAT_TIME + ".%f" # DLC 目前只支持到 millisecond
FORMAT_DATETIME = FORMAT_DATE + " " + FORMAT_TIME
FORMAT_DATETIME_MILLISECOND = FORMAT_DATE + " " + FORMAT_TIME_MILLISECOND


'''
2022-09-23
2022-09-23 07:36:10
2022-09-23 07:36:10.123456
2022-09-23 07:36:10.123
2022-09-23T07:36:10

引擎格式调整
2023-11-16T10:26:42.752+08:00
'''

RESULT_DELIMITER = ','
RESULT_ESCAPE_CHAR = '\\'
RESULT_QUOTE_CHAR = '"'


DATETIME_REGEXP = re.compile(
    r"(\d{1,4})-(\d{1,2})-(\d{1,2})[T ](\d{1,2}):(\d{1,2}):(\d{1,2})(?:[.](\d{1,6}))?(?:[\+](\d{2}):\d{2})?"
)

FORMAT_STRING_NULL = None

RESULT_TYPE = constants.ResultType.CSV


# TODO  
# 当非 null 字段接受到 None 数据， 暂时不抛异常
def _isCompactNull(value):
    if value is None:
        return True
    if isinstance(value, str) and value == "":
        return True
    return False

def checkNull(fn):
   def fn_wrapper(value, *args, **kwargs):
        if _isCompactNull(value):
            value = None
        else:
            try:
                value = fn(value, *args, **kwargs)
            except Exception as e:
                LOG.debug(f"类型转换异常: {e}")
        return value
   return fn_wrapper

def default_converter(value, *args, **kwargs):
    return value

@checkNull
def integer_converter(value, *args, **kwargs):
    return int(value)

@checkNull
def bigint_converter(value, *args, **kwargs): 
    return int(value)

def string_converter(value, *args, **kwargs):
    # TODO
    # 目前判断不出来 字符空 和 NULL
    if FORMAT_STRING_NULL is not None and value == FORMAT_STRING_NULL:
        return None
    return value

@checkNull
def decimal_converter(value, *args, **kwargs):
    return Decimal(value)

@checkNull
def float_converter(value, *args, **kwargs):
    return float(value)

@checkNull
def datetime_converter(value, *args, **kwargs):
    m = DATETIME_REGEXP.match(value)
    if m:
        groups = m.groups()
        d = datetime(year=int(groups[0]), 
                     month=int(groups[1]), 
                     day=int(groups[2]), 
                     hour=int(groups[3]), 
                     minute=int(groups[4]), 
                     second=int(groups[5]))
        
        if len(groups) >= 7 and groups[6]:
            d = d.replace(microsecond=int(groups[6]))
        if len(groups) >= 8 and groups[7]:
            tz = timezone(timedelta(hours=int(groups[7])))
            d = d.replace(tzinfo=tz)
        return d


@checkNull
def datetime_converter_v2(value, *args, **kwargs):
    """
    新版本datetime转换器
    - 支持datetime/字符串输入
    - 正确处理微秒补齐
    - 解析失败时返回原值
    """
    # 如果已经是datetime类型，直接返回
    if isinstance(value, datetime):
        return value
    
    m = DATETIME_REGEXP.match(str(value))
    if m:
        groups = m.groups()
        microsecond = 0
        if groups[6]:
            # 补齐到6位微秒
            ms_str = groups[6].ljust(6, '0')[:6]
            microsecond = int(ms_str)
        
        d = datetime(year=int(groups[0]), 
                     month=int(groups[1]), 
                     day=int(groups[2]), 
                     hour=int(groups[3]), 
                     minute=int(groups[4]), 
                     second=int(groups[5]),
                     microsecond=microsecond)
        
        if groups[7]:
            tz = timezone(timedelta(hours=int(groups[7])))
            d = d.replace(tzinfo=tz)
        return d
    
    # 正则不匹配时，尝试使用标准格式解析
    try:
        return datetime.strptime(str(value), FORMAT_DATETIME)
    except ValueError:
        pass
    try:
        return datetime.strptime(str(value), FORMAT_DATETIME_MILLISECOND)
    except ValueError:
        pass
    
    # 无法解析，返回原值
    return value


@checkNull
def date_converter(value, *args, **kwargs):
    return datetime.strptime(value, FORMAT_DATE)


@checkNull
def date_converter_v2(value, *args, **kwargs):
    """
    新版本日期转换器
    - 返回 datetime 类型（而非 date 类型）
    - 支持 datetime/date/字符串输入
    """
    if isinstance(value, (datetime, date)):
        return value
    return datetime.strptime(str(value), FORMAT_DATE)


@checkNull
def time_converter(value, *args, **kwargs):
    return value

@checkNull
def boolean_converter(value, *args, **kwargs):
    """布尔类型转换器"""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes')
    return bool(value)

@checkNull
def struct_converter(value, *args, **kwargs):
    return json.loads(value)


@checkNull
def struct_converter_v2(value, *args, **kwargs):
    """
    新版本struct转换器
    - 支持dict/字符串输入
    - 解析失败时返回原值
    """
    if isinstance(value, dict):
        return value
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value

@checkNull
def array_converter(value, *args, **kwargs):
    return value


@checkNull
def array_converter_v2(value, *args, **kwargs):
    """
    新版本数组类型转换器
    - 如果已是list/tuple，转换为list返回
    - 否则尝试JSON解析
    - 解析结果不是list时，返回原值
    """
    if isinstance(value, (list, tuple)):
        return list(value)
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return parsed
        # 如果解析结果不是list，返回原值
        return value
    except (json.JSONDecodeError, TypeError):
        return value

@checkNull
def map_converter(value, *args, **kwargs):
    """
    Map类型转换器
    - 如果已是dict，直接返回
    - 否则尝试JSON解析
    - 返回类型始终为dict或原始值（解析失败时）
    """
    if isinstance(value, dict):
        return value
    try:
        parsed = json.loads(value)
        if isinstance(parsed, dict):
            return parsed
        return value
    except (json.JSONDecodeError, TypeError):
        return value



'''
TODO
python3 / 需要注意

DLC 支持 bigint/int    smallint/tinyint 会转化成 int
bigint      -2^63 (-9223372036854775808) 到 2^63-1 (9223372036854775807) 
int         -2^31 (-2,147,483,648) 到 2^31 - 1 (2,147,483,647)
smallint    -2^15 (-32,768) 到 2^15 - 1 (32,767)
tinyint     0 到 255 


date
timestamp  yyyy-mm-dd hh:mm:ss

'''


_TYPE_CODES = constants.DataType.ENUMS()

def getTypeCode(type_str):
    type_str = type_str.replace(' ', '_')
    return _TYPE_CODES.get(type_str.upper(), constants.DataType.OTHER)


_CONVERTERS = {
    # ============================================
    # 老版本类型映射（保持向后兼容）
    # ============================================
    'INTEGER': integer_converter,
    'BIGINT': bigint_converter,
    'DECIMAL': decimal_converter,
    'DATE': date_converter,
    'TIMESTAMP': datetime_converter,
    'VARCHAR': string_converter,
    'STRING': string_converter,
    'FLOAT': float_converter,
    'DOUBLE': float_converter,
    'LONG': bigint_converter,

    # 不处理嵌套结构
    'STRUCT': struct_converter,

    # 'ARRAY'
    # 'MAP'

    'CHAR': string_converter,

    # ============================================
    # 新版本类型映射（带 _TYPE 后缀）
    # 使用优化后的转换器，功能更完善
    # ============================================
    # 整数类型
    'TINYINT_TYPE': integer_converter,
    'SMALLINT_TYPE': integer_converter,
    'INT_TYPE': integer_converter,
    'BIGINT_TYPE': bigint_converter,

    # 浮点数类型
    'FLOAT_TYPE': float_converter,
    'DOUBLE_TYPE': float_converter,
    'DECIMAL_TYPE': decimal_converter,

    # 字符串类型
    'STRING_TYPE': string_converter,
    'VARCHAR_TYPE': string_converter,
    'CHAR_TYPE': string_converter,

    # 日期时间类型（新版本返回正确的类型）
    'DATE_TYPE': date_converter_v2,           # 返回datetime类型
    'TIMESTAMP_TYPE': datetime_converter_v2,  # 完善的解析逻辑
    'INTERVAL_YEAR_MONTH_TYPE': string_converter,
    'INTERVAL_DAY_TIME_TYPE': string_converter,

    # 布尔类型
    'BOOLEAN_TYPE': boolean_converter,

    # 嵌套结构类型
    'STRUCT_TYPE': struct_converter_v2,
    'ARRAY_TYPE': array_converter_v2,
    'MAP_TYPE': map_converter,
}

def getConvert(name):
    return _CONVERTERS.get(name.upper(), default_converter)

_trans = [chr(x) for x in range(128)]
_trans[ord("'")] = "\\'"

def string_literal(value: str):
    return "'" + value.translate(_trans) + "'"

def default_literal(value):
    if value is None:
        return 'null'
    return str(value)

def dict_literal(value: dict):
    n = {}
    for k, v in value.items():
        n[k] = literal(v)
    return n

def sequence_literal(value: Sequence):
    return "(" + ",".join([literal(item) for item in value]) + ")"

def set_literal(value: set):
    return  ",".join([literal(item) for item in value])

def datetime_literal(value: datetime):
    fmt = FORMAT_DATETIME
    if value.microsecond:
        fmt = FORMAT_DATETIME_MILLISECOND
    return "'" + value.strftime(fmt)  + "'"

def date_literal(value: date):
    return "'" + value.strftime(FORMAT_DATE) + "'"

_literals = {
    'int': default_literal,
    'str': string_literal,
    'dict': dict_literal,
    'list': sequence_literal,
    'tuple': sequence_literal,
    'set': set_literal,
    'date': date_literal,
    'datetime': datetime_literal,
#    'timestamp'
}

def literal(value):
    return _literals.get(type(value).__name__, default_literal)(value)




Date = date
Time = time
TimeDelta = timedelta
Timestamp = datetime


def DateFromTicks(ticks):
    return date(*localtime(ticks)[:3])


def TimeFromTicks(ticks):
    return time(*localtime(ticks)[3:6])


def TimestampFromTicks(ticks):
    return datetime(*localtime(ticks)[:6])


def Binary(x):
    return bytes(x)