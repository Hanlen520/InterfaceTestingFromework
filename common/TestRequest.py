#!/usr/bin/env python
#coding=utf-8

import requests
from TestLogger import *

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
