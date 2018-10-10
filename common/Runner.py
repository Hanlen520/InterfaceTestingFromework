#!/usr/bin/env python
#coding=utf-8

import time
import unittest
import HTMLTestRunner
from TestData import *

report_path = os.path.abspath('..') + '\\report'

def test_generator(case_data):
	def test(self):
		print(case_data)
	return test

def test_setup(setup_data):
	def setUp(self):
		print(setup_data)
	return setUp

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
		print('before_class:', before_class)
		print('after_class:', after_class)
		print('setup_data:', setup_data)
		print('teardown_data:', teardown_data)
		print('case_datas:', case_datas)
		print('#####################')
		setup = test_setup(setup_data)
		setattr(TestSequense, 'setUp', setup)
		for n, case_data in enumerate(case_datas):
			test = test_generator(case_data)
			description = case_data['Description']
			setattr(TestSequense, 'test_{}'.format(description), test)
		loaded_testcase = loader.loadTestsFromTestCase(TestSequense)
		loaded_testcases.append(loaded_testcase)
	test_suite = unittest.TestSuite(loaded_testcases)
	now = time.strftime("%Y-%m-%d %H_%M_%S", time.localtime())
	filename = report_path + '/' + now + "_result.html"
	fp = open(filename, 'wb')
	runner = HTMLTestRunner.HTMLTestRunner(
		stream=fp,
		title=u'测试报告',
		description=u'用例执行情况：')
	runner.run(test_suite)
	
if __name__ == "__main__":
	run_test()