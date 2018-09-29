#!/usr/bin/env python
#coding=utf-8

import json
from common import *
from get_data import *
from test_request import *

class RunTest():
	
	def __init__(self):
		self.work_path = os.path.abspath(os.path.dirname(__file__))
		self.names = self.__dict__
	
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
						v = self.names.get(v.replace('$', ''))
					except BaseException as  e:
						logger.error('此变量未被定义：{}'.format(v.replace('$', '')))
				else:
					pass
				change_data(data, v, k)
				
	def main(self):
		logger.info(u'测试开始...')
		# 获取case list
		case_list = GetData(self.work_path).get_case_data()
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
					self.names[key] = str(eval(str(resp[1])+str(value)))
		logger.info('结束测试...')
		
if __name__ == "__main__":
	RunTest().main()
	