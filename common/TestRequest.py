#!/usr/bin/env python
#coding=utf-8

import requests
import random
from TestLogger import *
from requests_toolbelt.multipart.encoder import MultipartEncoder

file_path = os.path.abspath('..') + '\\file'

class TestRequest:
	
	@staticmethod
	def test_request(url, method, headers=None, data=None):
		'''
		:param url: request地址
		:param method: 方法get、post
		:param headers: 请求头
		:param data: 请求数据
		:return: [resp.status_code, resp.json()]
		'''
		if str(method).lower() == 'get':
			resp = requests.get(url, headers=headers)
		elif str(method).lower() == 'post':
			resp = requests.post(url, headers=headers, data=data)
		else:
			logger.error('method错误：{}'.format(method))
			return [-1]
		return [resp.status_code, resp.json(), resp.elapsed.total_seconds()]
	
	@staticmethod
	def multipart_form_data(url, headers, request_data):
		'''
		:param url: 请求url
		:param headers: 包含token的请求头
		:param request_data: file=aaa.xlsx，isAdd=0
		:return:
		'''
		if not 'file' in request_data.keys():
			print('file字段缺失')
			return [-1]
		file = file_path + '\\' + request_data['file']
		filename = os.path.split(file)[1]
		try:
			fields = {
					'file': (os.path.basename(filename), open(file, 'rb'), 'application/octet-stream')
				}
		except BaseException as e:
			print('未找到相应文件：{}'.format(file),e)
			return [-1]
		for key, value in request_data.items():
			if key != 'file':
				fields[key] = value
		multipart_encoder = MultipartEncoder(
			fields=fields,
			boundary='-----------------------------' + str(random.randint(1e28, 1e29 - 1))
		)
		headers['content-type'] = multipart_encoder.content_type
		resp = requests.post(url, data=multipart_encoder, headers=headers)
		return [resp.status_code, resp.json(), resp.elapsed.total_seconds()]