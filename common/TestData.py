#!/usr/bin/env python
#coding=utf-8


import yaml
import xlrd
import json
import configparser
from Common import *

class GetData:

	def __init__(self):
		self.work_path = os.path.abspath('.')
		self.yml_path = os.path.abspath('..') + '\\api'
		self.excel_path = os.path.abspath('..') + '\\testCases'
	
	def change_api_name(self, apiname):
		'''
		:param apiname: /api/user/login,  api_user_login
		:return:  统一转换为api_user_login
		'''
		return '_'.join(apiname.lstrip('/').split('/')).strip('\r').strip('\n') if  '/' in apiname else apiname
	
	def change_request_info(self, operation, *args):
		'''
		:param operation: excel数据
		:param args: 要改变的数据，如：data.password=1
		:return: 被替换的yml数据
		'''
		# 根据excel找到yml文件数据
		if operation['API Name'] != '':
			yml_data = self.get_yml_data(self.change_api_name(operation['API Name']))
			if not yml_data:
				logger.warning(u'没有对应的yml数据：{}'.format(self.change_api_name(operation['API Name'])))
			# 逐个替换数据
			for i in args:
				parse_function(i, yml_data)
			return yml_data
		return {}
		
	def list_all_files(self, rootdir):
		'''
		:param rootdir: 根目录
		:return: 目录下所有的文件
		'''
		_files = []
		list = os.listdir(rootdir)
		for i in range(0, len(list)):
			path = os.path.join(rootdir, list[i])
			if os.path.isdir(path):
				_files.extend(self.list_all_files(path))
			if os.path.isfile(path):
				_files.append(path)
		return _files
	
	def get_config_data(self, section, option=None):
		'''
		:param section: 配置文件section
		:param option: 配置文件option
		:return: section下对应option值或者section下所有option值
		'''
		config_path = self.work_path + '/config.ini'
		config = configparser.ConfigParser()
		config.read(config_path)
		if option:
			try:
				value = config.get(section, option)
			except BaseException as e:
				logger.error(u'未找到相应的配置文件信息： section:{}, option:{}'.format(section, option), e)
				value = ''
		else:
			try:
				options = config.options(section)
				value = {option: config.get(section, option) for option in options}
			except BaseException as e:
				logger.error(u'未找到相应的配置文件信息： section:{}'.format(section), e)
				value = ''
		return value
	
	def get_yml_data(self, name):
		'''
		:param name: api的名称
		:return: 对应的数据 {name:{}}
		'''
		yml=[]
		yml_files = self.list_all_files(self.yml_path)
		for yml_file in yml_files:
			if name + '.yml' in yml_file:
				yml = yml_file
				break
		if not yml:
			logger.warning('yml文件不存在：{}'.format(self.yml_path))
			return {}
		with open(yml, 'rb') as f:
			api_data = yaml.load(f)
		try:
			return api_data[name]
		except BaseException as e:
			logger.error('API不存在:{}'.format(e))
			return {}
		
	def get_excel_files(self):
		excel_files = self.list_all_files(self.excel_path)
		# 根据配置文件信息寻找需要的excel名
		excel_names = self.get_config_data('CaseInfo', 'excel_name').split(',')
		if excel_names == '':
			return excel_files
		files = []
		for excel_name in excel_names:
			for excel_file in excel_files:
				if excel_name + '.xlsx' in excel_file:
					files.append(excel_file)
		return files
	
	def change_check_point(self, check_point):
		try:
			check_point = check_point.split(';') if check_point != '' else ''
		except BaseException as e:
			logger.error('check point填写错误：{}'.format(check_point))
		# 如："Check Point": { "code": ["0","=" ], "data.ord_id": [ "1","in"],"msg": ["\u6210\u529f","="]
		check_point = {re.split('\s.*?\s', c)[1]:[re.split('\s.*?\s', c)[0], re.findall('\s(.*?)\s', c)[0]] for c in check_point} if check_point != '' else ''
		return check_point
		
	def change_case_info(self, case):
		yml_data = self.change_request_info(case, case['Request Headers'], case['Request Data'])
		# yml数据加到case信息中
		for key, value in yml_data.items():
			case[key] = value
		case.pop('Request Headers')
		case.pop('Request Data')
		# 有Host信息则替换yml中的url对应的host
		host = str(case['Host']).strip()
		if host != '':
			host = self.get_config_data('Host', host)
			case['url'] = host + '/' + case['url'].split('/',3)[-1]
		case['Correlation'] = parse_data(case['Correlation'])
		case['Check Point'] = self.change_check_point(case['Check Point'])
		return case
		
	def get_case_data(self):
		'''
		:return: excel中所有case的数据 [[{}]],一层为excel,二层为sheet，三层为sheet内信息
		'''
		files = self.get_excel_files()
		if not files:
			return {}
		all_caseinfo = []
		# 遍历所有要执行的excel
		for file in files:
			filename = os.path.split(file)[1].replace('.xlsx','')
			test_case = xlrd.open_workbook(file)
			sheets = test_case.sheet_names()
			sheetinfo = []
			# 遍历所有sheet
			for sheet in sheets:
				test_data = {}
				table = test_case.sheet_by_name(sheet)
				test_data['sheet_name'] = filename + '_' +sheet
				test_data['Active'] = table.cell(10, 1).value      # Active
				# Active为No则跳过执行
				if test_data['Active'] == 'No':
					continue
				test_data['case_name'] = table.cell(0, 1).value    # 名称
				test_data['priority'] = table.cell(1, 1).value     # 优先级
				
				before_class = {}                                  # 前置条件
				before_class['operation'] = table.cell(2, 2).value
				# 前置操作为数据库操作
				if before_class['operation'] == '数据库操作':
					before_class['db_name'] = table.cell(4, 2).value.strip()
					# 数据库操作不为空则去配置文件获取相应信息
					if before_class['db_name'] != '':
						before_class['host'] = self.get_config_data(before_class['db_name'], 'host')
						before_class['user'] = self.get_config_data(before_class['db_name'], 'user')
						before_class['password'] = self.get_config_data(before_class['db_name'], 'password')
						before_class['sql'] = table.cell(5, 2).value
				# 前置操作为API形式
				else:
					before_class['API Name'] = self.change_api_name(table.cell(3, 2).value)
					before_class['request_data'] = table.cell(4, 2).value
					# 根据excel数据替换yml文件数据
					yml_data = self.change_request_info(before_class, before_class['request_data'])
					# yml文件数据添加到excel数据中
					for key, value in yml_data.items():
						before_class[key] = value
					before_class['response'] = parse_data(table.cell(5, 2).value)
					before_class.pop('request_data')
				test_data['beforeClass'] = before_class
				
				after_class = {}                                    # 后置条件
				after_class['operation'] = table.cell(6, 2).value
				if after_class['operation'] == '数据库操作':
					after_class['db_name'] = table.cell(8, 2).value.strip()
					if after_class['db_name'] != '':
						after_class['host'] = self.get_config_data(after_class['db_name'], 'host')
						after_class['user'] = self.get_config_data(after_class['db_name'], 'user')
						after_class['password'] = self.get_config_data(after_class['db_name'], 'password')
						after_class['sql'] = table.cell(9, 2).value
				else:
					after_class['API Name'] = self.change_api_name(table.cell(7, 2).value)
					after_class['request_data'] = table.cell(8, 2).value
					yml_data = self.change_request_info(after_class, after_class['request_data'])
					for key, value in yml_data.items():
						after_class[key] = value
					after_class['response'] = parse_data(table.cell(5, 2).value)
					after_class.pop('request_data')
				test_data['afterClass'] = after_class
				# 获取case列表的title
				title = {i: str(table.cell(12, i).value).strip().strip('\r').strip('\n') for i in range(table.ncols)}
				# setup信息
				setup = {title[i]: str(table.cell(13, i).value).strip().strip('\r').strip('\n') for i in range(table.ncols)}
				setup = self.change_case_info(setup)
				# teardown信息
				teardown = {title[i]: str(table.cell(14, i).value).strip().strip('\r').strip('\n') for i in range(table.ncols)}
				teardown = self.change_case_info(teardown)
				caselist = []
				# 所有的case信息
				for j in range(15, table.nrows):
					case = {title[i] : str(table.cell(j, i).value).strip().strip('\r').strip('\n') for i in range(table.ncols)}
					if case['Active'] == 'No':
						continue
					case = self.change_case_info(case)
					caselist.append(case)
				test_data['setup'] = setup
				test_data['teardown'] = teardown
				test_data['testcase'] = caselist
				sheetinfo.append(test_data)
			all_caseinfo.append(sheetinfo)
		return all_caseinfo
	
if __name__ == '__main__':
	p = GetData().get_case_data()
	print(json.dumps(p, sort_keys=True, indent=2))