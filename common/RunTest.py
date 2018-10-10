#!/usr/bin/env python
#coding=utf-8

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "..")))
import json
import time
import unittest
from common import HTMLTestRunner
from common import *
from common.TestData import *
from common.TestRequest import *

class RunTest:
	
	def __init__(self):
		self.work_path = os.path.abspath(os.path.dirname(__file__))
		
	def parse_function(self, function, data):
		function = parse_data(function)
		if function:
			for k, v in function.items():
				k = k.split('.') if '.' in k else [k]
				k = [parse_string_value(x) for x in k]
				if '${' in v:
					try:
						v = extract_functions(v)
					except BaseException as e:
						logger.error('没有此函数：{}, {}'.format(v, e))
				elif '$' in v:
					try:
						name = v.replace('$', '')
						v = getattr(self, name)
					except BaseException as  e:
						logger.error('此变量未被定义：{}'.format(v.replace('$', '')))
				else:
					pass
				change_data(data, v, k)
				
	def gen_testsuit(self):
		# 获取case list
		case_list = GetData(self.work_path).get_case_data()
		loader = unittest.TestLoader()
		loaded_testcases = []
		for n, caseinfo in enumerate(case_list):
			# 跳过执行
			if caseinfo['Active'] == 'No':
				logger.info(u'跳过执行此case：{}'.format(caseinfo['API Purpose']))
				continue
			# 根据url寻找对应的yml数据
			api_name = '_'.join(caseinfo['Request URL'].lstrip('/').split('/')).strip('\r').strip('\n')
			yml_data = GetData(self.work_path).get_yml_data(api_name)
			if not yml_data:
				logger.warning(u'没有对应的yml数据：{}'.format(api_name))
				continue
			content_type = yml_data['headers']['content-type']
			# 解析case中的request data，替换yml文件数据
			self.parse_function(caseinfo['Request Data'], yml_data)
			request_data = json.dumps(yml_data['json']) if 'json' in content_type else yml_data['data']
			# 解析case中的request headers，替换yml文件数据
			self.parse_function(caseinfo['Request Headers'], yml_data)
			headers = yml_data['headers']
			url = caseinfo['API Host'] + caseinfo['Request URL']
			method = yml_data['method']
			test = test_generator(url, method, headers, request_data, caseinfo)
			TestSequense = type('TestSequense', (unittest.TestCase,), {})
			setattr(TestSequense, 'test_{}'.format(url), test)
			loaded_testcase = loader.loadTestsFromTestCase(TestSequense)
			loaded_testcases.append(loaded_testcase)
		test_suite = unittest.TestSuite(loaded_testcases)
		return test_suite
		
def test_generator(url, method, headers, request_data, caseinfo):
	def test(self):
		resp = TestRequest().test_request(url, method, headers, request_data)
		print(resp)
		logger.info('\ncase name: {}, \nrequest data: {}, \nresponse: {}\n==================================================='
		            .format(caseinfo['API Purpose'], request_data, resp))
		assert resp[0] == 200
		check_point = parse_data(caseinfo['Check Point'])
		if check_point:
			for key, value in check_point.items():
				key = parse_string(key)
				assert str(eval(str(resp[1])+str(key))) == value
		correlation = parse_data(caseinfo['Correlation'])
		if correlation:
			for key, value in correlation.items():
				value = parse_string(value)
				setattr(RunTest, key, str(eval(str(resp[1])+str(value))))
				print(getattr(RunTest, key))
	return test
	
if __name__ == "__main__":
	suite = RunTest().gen_testsuit()
	now = time.strftime("%Y-%m-%d %H_%M_%S", time.localtime())
	filename = now + "_result.html"
	fp = open(filename, 'wb')
	runner = HTMLTestRunner.HTMLTestRunner(
		stream=fp,
		title=u'测试报告',
		description=u'用例执行情况：')
	runner.run(suite)
	
	