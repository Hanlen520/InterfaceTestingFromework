#!/usr/bin/env python
#coding=utf-8

import time
import unittest
import HTMLTestRunner
from TestRequest import *
from TestData import *
from BeautifulReport import BeautifulReport

report_path = os.path.abspath('..') + '\\report'

def test_generator(case_data, isSetupOrCase='case'):
	def test(self):
		Data = GetData()
		yml_data = None
		if case_data['API Name'] != '':
			yml_data = Data.get_yml_data(Data.change_api_name(case_data['API Name']))
			self.assertNotEqual(yml_data, {})
			for key, value in yml_data.items():
				case_data[key] = value
			# 有Host信息则替换yml中的url对应的host
			host = str(case_data['Host']).strip()
			if host != '':
				host = Data.get_config_data('Host', host)
				case_data['url'] = host + '/' + case_data['url'].split('/', 3)[-1]
			case_data['Correlation'] = parse_data(case_data['Correlation'])
			case_data['Check Point'] = Data.change_check_point(case_data['Check Point'])
			for function in [case_data['Request Headers'], case_data['Request Data']]:
				function = parse_data(function)
				if function:
					for k, v in function.items():
						k = k.split('.') if '.' in k else [k]
						k = [parse_string_value(x) for x in k]
						if '${' in v:
							v = extract_functions(v)
							self.assertIsNotNone(v)
						elif '$' in v:
							v = getattr(self, v.replace('$', ''), None)
							self.assertIsNotNone(v)
						else:
							pass
						change_data(yml_data, v, k)
		self.assertIsNotNone(yml_data)
		for key, value in yml_data.items():
			case_data[key] = value
		content_type = case_data['headers']['content-type']
		request_data = json.dumps(case_data['json']) if 'json' in content_type else case_data['data']
		url = case_data['url']
		method = case_data['method']
		headers = case_data['headers']
		resp = TestRequest().test_request(url, method, headers, request_data)
		# print(resp)
		self.assertEqual(resp[0], 200)
		check_point = case_data['Check Point']
		if check_point:
			for key, value in check_point.items():
				key = parse_string(key)
				if type(value) == str:
					self.assertEqual(str(eval(str(resp[1]) + str(key))), value)
				elif type(value) == list:
					assertMethod = value[1]
					if assertMethod == '=':
						self.assertEqual(str(eval(str(resp[1]) + str(key))), value[0])
					elif str(assertMethod).lower() == 'in':
						self.assertTrue(value[0] in str(eval(str(resp[1]) + str(key))))
					elif str(assertMethod).lower() == 'not in':
						self.assertTrue(value[0] not in str(eval(str(resp[1]) + str(key))))
					else:
						print(check_point)
						self.assertEqual('Check Point', '断言方法')
				else:
					print(check_point)
					self.assertEqual('Check Point', '断言方法')
		correlation = case_data['Correlation']
		if correlation:
			for key, value in correlation.items():
				value = parse_string(value)
				setattr(self, key, str(eval(str(resp[1]) + str(value))))
		get_summary(url, method, headers, request_data, resp, isSetupOrCase)
	return test

def get_summary(url, method, headers, data, resp, isSetupOrCase):
	print('{}: \n'
	      'url: {}\n'
	      'method: {}\n'
	      'headers: {}\n'
	      'data: {}\n'
	      'status_code: {}\n'
	      'response: {}\n'
	      'response time: {}\n'
	      '########################################################'.format(
		isSetupOrCase, url, method, headers, data, resp[0], resp[1], resp[2]))

def get_sheetdata():
	all_caseinfo = GetData().get_case_data()
	for excel_datas in all_caseinfo:
		for sheet_datas in excel_datas:
			yield sheet_datas
		
def run_test():
	sheet_datas = get_sheetdata()
	loaded_testcases = []
	loader = unittest.TestLoader()
	for sheet_data in sheet_datas:
		sheet_name = sheet_data['sheet_name']
		TestSequense = type(sheet_name, (unittest.TestCase,), {})
		before_class = sheet_data['beforeClass']
		after_class = sheet_data['afterClass']
		setup_data = sheet_data['setup']
		teardown_data = sheet_data['teardown']
		case_datas = sheet_data['testcase']
		setup = test_generator(setup_data,'setup')
		setattr(TestSequense, 'setUp', setup)
		for n, case_data in enumerate(case_datas):
			test = test_generator(case_data)
			description = case_data['Description']
			setattr(TestSequense, 'test_{}'.format(description), test)
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
	# print(get_summary(result))
	
	result = BeautifulReport(test_suite)
	result.report(filename= filename, description ='接口测试', log_path =report_path)
if __name__ == "__main__":
	run_test()