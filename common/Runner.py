#!/usr/bin/env python
#coding=utf-8

import time
import unittest
import HTMLTestRunner
from TestRequest import *
from TestData import *
from Func import *
from BeautifulReport import BeautifulReport

report_path = os.path.abspath('..') + '\\report'

class CaseVariable:
	pass

@classmethod
def setUpClass(cls):
	datas = getattr(CaseVariable, 'setup_class')
	try:
		check = test_class(datas,'setUpClass')
		if not check:
			print('setUpClass执行失败')
	except BaseException as e:
		print('setUpClass执行失败: {}'.format(e))
	cls.start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
	print("Start test at {}".format(cls.start_time))

@classmethod
def tearDownClass(cls):
	datas = getattr(CaseVariable, 'teardown_class')
	try:
		check = test_class(datas, 'tearDownClass')
		if not check:
			print('tearDownClass执行失败')
	except BaseException as e:
		print('tearDownClass执行失败: {}'.format(e))
	cls.end_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
	print("End test at {}".format(cls.end_time))
	timestamp = time.mktime(time.strptime(cls.end_time, "%Y-%m-%d %H:%M:%S")) - time.mktime(time.strptime(cls.start_time, "%Y-%m-%d %H:%M:%S"))
	print('\n运行时间：{}秒'.format(timestamp))
	
def test_class(datas, classname):
	for data in datas:
		if data['API Name'] == '' or data['Active'] == 'No':
			print('{}:{}跳过执行'.format(classname, data['Description']))
			continue
		print('{}:{}开始执行'.format(classname, data['Description']))
		Data = GetData()
		# 如果执行函数
		if '${' in  data['API Name']:
			return_data = extract_functions(data['API Name'], CaseVariable)
			print('{}'.format(classname) + '\n')
			print('函数{}执行成功'.format(data['API Name']) + '\n')
			print('return data: {}'.format(return_data))
			print('=========================================================================================================')
			if data['Correlation']:
				setattr(CaseVariable, data['Correlation'],return_data[1])
				continue
		# 根据API NAME找到yml数据
		yml_data = Data.get_yml_data(Data.change_api_name(data['API Name']))
		if yml_data == {}:
			print('{}:{} 未找到yml文件数据：{}'.format(classname, data['Description'],data['API Name']))
			return False
		# yml数据加到case_data中
		for key, value in yml_data.items():
			data[key] = value
		# 有Host信息则替换yml中的url对应的host
		host = str(data['Host']).strip()
		if host != '':
			new_host = Data.get_config_data('Host', host)
			setattr(CaseVariable, host, new_host)
			data['url'] = new_host + '/' + data['url'].split('/', 3)[-1]
		data['Correlation'] = parse_data(data['Correlation'])
		data['Check Point'] = Data.change_check_point(data['Check Point'])
		# 根据Request Headers和Request Data替换case_data中的数据
		for function in [data['Request Headers'], data['Request Data']]:
			function = parse_data(function)
			if function:
				for k, v in function.items():
					k = k.split('.') if '.' in k else [k]
					k = [parse_string_value(x) for x in k]
					# 执行函数
					if '${' in v:
						new_v = parse_string_value(extract_functions(v,CaseVariable))
					# 寻找变量
					elif '$' in v:
						new_v = parse_string_value(getattr(CaseVariable, v.replace('$', ''), None))
					# 字符串
					else:
						new_v = parse_string_value(v)
					change_data(yml_data, new_v, k)
		# 如果没有API NAME信息失败
		method = data['method']
		url = data['url']
		headers = ''
		request_data = ''
		# get方法
		if str(method).lower() == 'get':
			headers = data['headers']
			resp = TestRequest.test_request(url, method, headers=headers)
		# post方法
		elif str(method).lower() == 'post':
			try:
				content_type = data['headers']['content-type']
			except KeyError:
				content_type = ''
			# json和data形式
			if 'multipart/form-data' not in content_type:
				request_data = json.dumps(data['json']) if 'json' in content_type else data['data']
				headers = data['headers']
				resp = TestRequest.test_request(url, method, headers, request_data)
			# 上传文件
			else:
				request_data = parse_data(data['Request Data'])
				headers = data['headers']
				resp = eval('TestRequest.multipart_form_data')(url, headers, request_data)
		# 其他方法，遇到再补充
		else:
			resp = [-1]
			print(method)
		get_summary(url=url, method=method, resp=resp, headers=headers,
		            request_data=request_data)
		correlation = data['Correlation']
		# 取值，保存为类变量
		if correlation:
			for key, value in correlation.items():
				# 区分request和resp，分别取值
				if 'request.' in value:
					if 'json' in value:
						value = parse_string(value.replace('request.json.', ''))
						setattr(CaseVariable, key, eval(str(json.loads(request_data)) + str(value)))
					else:
						value = parse_string(value.replace('request.data.', ''))
						setattr(CaseVariable, key, eval(str(request_data) + str(value)))
				else:
					value = parse_string(value)
					setattr(CaseVariable, key, eval(str(resp[1]) + str(value)))
	return True

def test_generator(case_datas, isSetupOrCase='case'):
	def test(self):
		if type(case_datas) == list:
			for case_data in case_datas:
				case(case_data,self)
		else:
			case(case_datas,self)
	def case(case_data,cls):
		if isSetupOrCase == 'setup' or isSetupOrCase == 'teardown':
			if case_data['API Name'] == '' or case_data['Active'] == 'No':
				print('{}跳过执行'.format(isSetupOrCase))
				return test
		Data = GetData()
		yml_data = None
		if case_data['API Name'] != '':
			# 如果执行函数
			if '${' in  case_data['API Name']:
				return_data = extract_functions(case_data['API Name'], CaseVariable)
				cls.assertTrue(return_data[0])
				print('{}'.format(isSetupOrCase) + '\n')
				print('函数{}执行成功'.format(case_data['API Name']) + '\n')
				try:
					print('return data: {}'.format(return_data[1]))
				except:
					print('return data: {}'.format(return_data))
				print('=========================================================================================================')
				if case_data['Correlation']:
					setattr(CaseVariable, case_data['Correlation'], return_data[1])
				return test
			# 根据API NAME找到yml数据
			yml_data = Data.get_yml_data(Data.change_api_name(case_data['API Name']))
			# 数据不为空
			cls.assertNotEqual(yml_data, {}, '未找到对应的yml文件数据：{}'.format(case_data['API Name']))
			# yml数据加到case_data中
			for key, value in yml_data.items():
				case_data[key] = value
			# 有Host信息则替换yml中的url对应的host
			host = str(case_data['Host']).strip()
			if host != '':
				new_host = Data.get_config_data('Host', host)
				setattr(CaseVariable, host, new_host)
				case_data['url'] = new_host + '/' + case_data['url'].split('/', 3)[-1]
			case_data['Correlation'] = parse_data(case_data['Correlation'])
			case_data['Check Point'] = Data.change_check_point(case_data['Check Point'])
			# 根据Request Headers和Request Data替换case_data中的数据
			for function in [case_data['Request Headers'], case_data['Request Data']]:
				function = parse_data(function)
				if function:
					for k, v in function.items():
						k = k.split('.') if '.' in k else [k]
						k = [parse_string_value(x) for x in k]
						# 执行函数
						if '${' in v:
							new_v = parse_string_value(extract_functions(v,CaseVariable))
							cls.assertIsNotNone(new_v)
						# 寻找变量
						elif '$' in v:
							new_v = parse_string_value(getattr(CaseVariable, v.replace('$', ''), None))
							cls.assertIsNotNone(new_v, '未定义变量{}'.format(v))
						# 字符串
						else:
							new_v = parse_string_value(v)
						change_data(yml_data, new_v, k)
		# 如果没有API NAME信息失败
		cls.assertIsNotNone(yml_data,'没有读取到API NAME信息')
		method = case_data['method']
		url = case_data['url']
		headers = ''
		request_data = ''
		# get方法
		if str(method).lower() == 'get':
			headers = case_data['headers']
			resp = TestRequest.test_request(url, method, headers=headers)
		# post方法
		elif str(method).lower() == 'post':
			try:
				content_type = case_data['headers']['content-type']
			except KeyError:
				content_type = ''
			# json和data形式
			if 'multipart/form-data' not in content_type:
				request_data = json.dumps(case_data['json']) if 'json' in content_type else case_data['data']
				headers = case_data['headers']
				resp = TestRequest.test_request(url, method, headers, request_data)
			# 上传文件
			else:
				request_data = parse_data(case_data['Request Data'])
				headers = case_data['headers']
				resp = eval('TestRequest.multipart_form_data')(url, headers, request_data)
		# 其他方法，遇到再补充
		else:
			resp = [-1]
			print(method)
		# status code为200
		cls.assertEqual(resp[0], 200,'\nrequest: {}\nresponse: {}'.format(request_data, resp))
		get_summary(url=url, method=method, resp=resp, isSetupOrCase=isSetupOrCase, headers=headers,
		            request_data=request_data)
		check_point = case_data['Check Point']
		if check_point:
			for key, value in check_point.items():
				if '${' in key:
					key = parse_string_value(extract_functions(key, CaseVariable))
					cls.assertIsNotNone(key)
				else:
					# 转换形式data1.data2 ==> [data1][data2]
					key = parse_string(key)
				if type(value) == str:
					# 值为字符串直接对比
					new_value = getattr(CaseVariable, value.replace('$', ''), None) if '$' in value else value
					cls.assertIsNotNone(new_value, '未定义变量{}'.format(value))
					if '${' in key:
						cls.assertEqual(key, new_value, '{}值不为{}'.format(key, new_value))
					else:
						cls.assertEqual(eval(str(resp[1]) + str(key)), new_value, '{}值不为{}'.format(key, new_value))
				elif type(value) == list:
					# 值为列表取对比方法
					# 目前支持=、in、not in
					new_value = getattr(CaseVariable, value[0].replace('$', ''), None) if '$' in value[0] else value[0]
					# 不为列表转换为字符串进行对比
					new_value = str(new_value) if type(new_value) != list else new_value
					if '${' in key:
						assert_value = key
					else:
						assert_value = str(eval(str(resp[1]) + str(key))) if type(eval(str(resp[1]) + str(key))) != list else eval(str(resp[1]) + str(key))
					cls.assertIsNotNone(new_value, '未定义变量{}'.format(value))
					assertMethod = value[1]
					if assertMethod == '=':
						cls.assertTrue(assert_value == new_value,  '{}值不为{}'.format(key, new_value))
					elif str(assertMethod).lower() == 'in':
						if type(new_value) == list:
							cls.assertTrue(set(new_value) < set(assert_value), '{}值不在{}中'.format(new_value, key))
						else:
							cls.assertTrue(new_value in assert_value, '{}值不在{}中'.format(new_value, key))
					elif str(assertMethod).lower() == 'notin':
						if type(new_value) == list:
							cls.assertNotTrue(set(new_value) < set(assert_value), '{}值不在{}中'.format(new_value, key))
						else:
							cls.assertTrue(new_value not in eval(str(resp[1]) + str(key)),'{}值在{}中'.format(new_value, key))
					# 错误的断言方法
					else:
						print(check_point)
						cls.assertEqual('Check Point', '断言方法')
				# 错误的断言方法
				else:
					print(check_point)
					cls.assertEqual('Check Point', '断言方法')
		correlation = case_data['Correlation']
		# 取值，保存为类变量
		if correlation:
			for key, value in correlation.items():
				# 区分request和resp，分别取值
				if 'request.' in value:
					if 'json' in value:
						value = parse_string(value.replace('request.json.', ''))
						setattr(CaseVariable, key, eval(str(json.loads(request_data)) + str(value)))
					else:
						value = parse_string(value.replace('request.data.', ''))
						setattr(CaseVariable, key, eval(str(request_data) + str(value)))
				else:
					value = parse_string(value)
					setattr(CaseVariable, key, eval(str(resp[1]) + str(value)))
	return test

def get_summary(**kwargs):
	try:
		print('{}'.format(kwargs['isSetupOrCase']))
	except:
		pass
	print('url: {}'.format(kwargs['url']))
	print('method: {}'.format(kwargs['method']))
	print('headers: {}'.format(kwargs['headers']))
	print('request data: {}'.format(kwargs['request_data']))
	print('status code: {}'.format(kwargs['resp'][0]))
	print('response: {}'.format(kwargs['resp'][1]))
	print('response time: {}'.format(kwargs['resp'][2]))
	print('=========================================================================================================')
	
def get_sheetdata():
	all_caseinfo = GetData().get_case_data()
	for excel_datas in all_caseinfo:
		for sheet_datas in excel_datas:
			yield sheet_datas
	
def run_test():
	sheet_datas = get_sheetdata()
	loaded_testcases = []
	loader = unittest.TestLoader()
	username = GetData().get_config_data('Host', 'username')
	password = GetData().get_config_data('Host', 'password')
	setattr(CaseVariable, 'username', username)
	setattr(CaseVariable, 'password', password)
	for sheet_data in sheet_datas:
		sheet_name = sheet_data['sheet_name']
		setup_class = sheet_data['setupclass']
		teardown_class = sheet_data['teardownclass']
		setattr(CaseVariable, 'setup_class', setup_class)
		setattr(CaseVariable, 'teardown_class', teardown_class)
		TestSequense = type(sheet_name, (unittest.TestCase,), {})
		TestSequense.setUpClass = setUpClass
		TestSequense.tearDownClass = tearDownClass
		setup_data = sheet_data['setup']
		teardown_data = sheet_data['teardown']
		case_datas = sheet_data['testcase']
		setup = test_generator(setup_data,'setup')
		teardown = test_generator(teardown_data, 'teardown')
		setattr(TestSequense, 'setUp', setup)
		setattr(TestSequense, 'tearDown', teardown)
		for n, case_data in enumerate(case_datas):
			test = test_generator(case_data)
			description = case_data['Description']
			setattr(TestSequense, 'test_{:03d}_{}'.format(n, description), test)
		loaded_testcase = loader.loadTestsFromTestCase(TestSequense)
		loaded_testcases.append(loaded_testcase)
	test_suite = unittest.TestSuite(loaded_testcases)
	now = time.strftime("%Y-%m-%d %H_%M_%S", time.localtime())
	# filename = report_path + '/' + now + "_result.html"
	filename = now + "_result.html"
	# fp = open(filename, 'wb')
	# runner = HTMLTestRunner.HTMLTestRunner(
	# 	stream=fp,
	# 	title=u'测试报告',
	# 	description=u'用例执行情况：')
	# runner.run(test_suite)
	
	# runner = unittest.TextTestRunner()
	# result = runner.run(test_suite)
	# print(result)
	
	result = BeautifulReport(test_suite)
	result.report(filename= filename, description ='接口测试', log_path =report_path)


if __name__ == "__main__":
	run_test()