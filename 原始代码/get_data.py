#!/usr/bin/env python
#coding=utf-8

import os
import sys
import yaml
import xlrd
from test_logger import logger

class GetData:

	def __init__(self, work_path):
		self.work_path = work_path
		self.yml_path = self.work_path + '\\TestData\\api_data.yml'
		self.excel_path = self.work_path + '\\TestCase\\TestCase.xlsx'
		
	def get_yml_data(self, name):
		'''
		:param name: api的名称
		:return: 对应的数据 {name:{}}
		'''
		if not os.path.exists(self.yml_path):
			logger.warning('yml文件不存在：{}'.format(self.yml_path))
			sys.exit(5)
		with open(self.yml_path, 'rb') as f:
			api_data = yaml.load(f)
		try:
			return api_data[name]
		except BaseException as e:
			logger.error('API不存在:{}'.format(e))
			return False
	
	def get_case_data(self):
		'''
		:return: excel中所有case的数据 [{},{}]
		'''
		if not os.path.exists(self.excel_path):
			logger.warning('case文件不存在：{}'.format(self.excel_path))
			sys.exit(5)
		test_case = xlrd.open_workbook(self.excel_path)
		table = test_case.sheet_by_index(0)
		if table.nrows < 2:
			logger.warning('case信息不足一条')
			sys.exit(5)
		title = {i : str(table.cell(0, i).value).strip().strip('\r').strip('\n') for i in range(table.ncols)}
		caselist = []
		for j in range(1, table.nrows):
			case = {title[i] : str(table.cell(j, i).value).strip().strip('\r').strip('\n') for i in range(table.ncols)}
			caselist.append(case)
		return caselist
