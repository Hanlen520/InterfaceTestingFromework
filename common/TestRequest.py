#!/usr/bin/env python
#coding=utf-8

import requests
import random
from TestLogger import *
from requests_toolbelt.multipart.encoder import MultipartEncoder

file_path = os.path.abspath('..') + '\\file'

class TestRequest:
	
	def test_request(self, url, method, headers=None, data=None):
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
			return
		return [resp.status_code, resp.json(), resp.elapsed.total_seconds()]
	
	def multipart_form_data(self, url, headers, request_data):
		if not 'file' in request_data.keys():
			return [-1]
		file = file_path + '\\' + request_data['file']
		filename = os.path.split(file)[1]
		fields = {
				'file': (os.path.basename(filename), open(file, 'rb'), 'application/octet-stream')
			}
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