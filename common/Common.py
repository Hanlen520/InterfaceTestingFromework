#!/usr/bin/env python
#coding=utf-8

import re
import ast
import pymysql
from Func import *
from TestLogger import *

function_regexp = r"\$\{([\w_]+\([\$\w\.\-/_ =,]*\))\}"


def extract_functions(content,cls=None):
    '''
    :param content: ${abc(1,2)}
    :return: 执行abc(1,2)函数返回值
    '''
    try:
        content = re.findall(function_regexp, content)[0]
    except TypeError:
        return
    pattern = re.compile('\((.*?)\)')
    params = re.findall(pattern,content)[0]
    params = params.split(',') if ',' in params else [params]
    for n, p in enumerate(params):
        if '$' in p:
            p = parse_string_value(getattr(cls, p.replace('$', ''), 'not_defined'))
            params[n] = repr(p)
    if len(params) == 1:
        params = params[0]
        content = content.split('(')[0]
        try:
            return eval(content)(params)
        except BaseException as e:
            logger.error(u'参数输入错误：{}, {}'.format(params, e))
            return
    else:
        params = '(' + ','.join(params) + ')'
        content = content.split('(')[0] + params
        # print(content)
        try:
            return eval(content)
        except BaseException as e:
            logger.error(u'参数输入错误：{}, {}'.format(params, e))
            return
        
def parse_string_value(str_value):
    '''
    :param str_value: str, 如：3, [1,2,3], {a:1, b:2}
    :return: str==>int, str==>list, str==> dict
    '''
    if str_value is None:return None
    try:
        return ast.literal_eval(str_value)
    except ValueError:
        return str_value
    except SyntaxError:
        return str_value

def parse_data(data):
    '''
    :param function: 字符串：data1.0.data2=3;data4=5
    :return: {data1.0.data2:3, data4:5}
    '''
    if not isinstance(data, dict):
        data = data.split(';') if data != '' else ''
        data = {i.split('=')[0]: i.split('=')[1] for i in data} if data != '' else ''
    return data

def change_data(data, value, k, i=0):
    '''
    :param data: 要修改的数组, 列表和字典的多层嵌套，如{'a':1, 'b':[{'c':2}, {'c':3}]}
    :param value: 要修改的值
    :param k: 要修改的数据坐标, list形式，如['a', 0, 'c']
    :param i: 不需要填，缺省为0
    '''
    if not isinstance(k, list):
        logger.warning('参数输入错误: {}'.format(k))
        return
    if i == len(k) - 1:
        data[k[i]] = value
        return
    change_data(data[k[i]], value, k, i + 1)

def change_str(string):
    new_str = parse_string_value(string)
    return repr(new_str) if type(new_str) == str else new_str
    
def parse_string(str_value):
    '''
    data ==> [data]
    data1.data2 ==> [data1][data2]
    '''
    return ''.join(["[{}]".format(change_str(i)) for i in str_value.split('.')]) if '.' in str_value else [str_value]

def parse_function(function, data):
    '''
    :param function: 如：data.password=1
    :param data: 要改变的数据
    :return: 改变后的数据
    '''
    # 转换function形式为字典
    function = parse_data(function)
    if function:
        for k, v in function.items():
            k = k.split('.') if '.' in k else [k]
            k = [parse_string_value(x) for x in k]
            change_data(data, v, k)

# 数据库操作
def manipulate_database(host, user, password, sql):
    try:
        db = pymysql.connect(host, user, password)
    except BaseException as e:
        logger.error('连接数据库失败：{}'.format(e))
        return
    cursor = db.cursor()
    try:
        cursor.execute(sql)
        db.commit()
        results = cursor.fetchall()
        logger.info('sql语句执行结果: {}'.format(results))
    except BaseException as e:
        logger.error("unable to fetch data",e)
        db.rollback()
    db.close()

