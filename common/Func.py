#!/usr/bin/env python
#coding=utf-8

import json
import hashlib
from Common import *
import TestData
from TestRequest import *

def gen_md5(password):
	'''
	:param password: 密码
	:return: md5加密
	'''
	return hashlib.md5(password.encode('utf-8')).hexdigest()

def deleteDataSetByName(token, datasetname):
	if datasetname ==  'not_defined':
		return [True,'datasetname未定义']
	Data = TestData.GetData()
	host = Data.get_config_data('Host', 'cm_host')
	getDataSetList_api = '/api/DataSet/Folder/getDataSetList'
	url = host + getDataSetList_api
	request_data = json.dumps(Data.get_yml_data(Data.change_api_name(getDataSetList_api))['json'])
	headers = {'token': token}
	resp = TestRequest.test_request(url=url, method='post', headers=headers, data=request_data)
	if resp[0] != 200:return [False,'status code不为200']
	data_list = resp[1]['data']['list']
	data_id = ''
	for data in data_list:
		if data['name'] == datasetname:
			data_id = data['id']
			type = data['type']
	if data_id == '':
		return [True,'没有此name对应的id']
	delete_api = '/api/DataSet/Manage/delete'
	url = host + delete_api
	request_data = Data.get_yml_data(Data.change_api_name(delete_api))['json']
	request_data['table_id'] = int(data_id)
	request_data['table_type'] = int(type)
	request_data = json.dumps(request_data)
	headers = {'token': token}
	resp = TestRequest.test_request(url=url, method='post', headers=headers, data=request_data)
	return [False,'code不为0'] if resp[1]['code'] != 0 else [True,'成功删除']

def deleteCampaignByName(token, campaignname):
	if campaignname ==  'not_defined':
		return [True,'campaignname未定义']
	Data = TestData.GetData()
	host = Data.get_config_data('Host', 'cm_host')
	api = '/apicm/Page/Campaign/Campaign/getRmosList'
	url = host + api
	request_data = json.dumps(Data.get_yml_data(Data.change_api_name(api))['json'])
	headers = {'token': token}
	resp = TestRequest.test_request(url=url, method='post', headers=headers, data=request_data)
	if resp[0] != 200:return [False,'status code不为200']
	data_list = resp[1]['data']['list']
	data_id = ''
	for data in data_list:
		if data['name'] == campaignname:
			data_id = data['id']
	if data_id == '':
		return [True,'没有此name对应的id']
	delete_api = '/apicm/Page/Campaign/Campaign/deleteRmosCampaign'
	url = host + delete_api
	request_data = Data.get_yml_data(Data.change_api_name(delete_api))['json']
	request_data['rmos_campaign_id'] = int(data_id)
	request_data = json.dumps(request_data)
	headers = {'token': token}
	resp = TestRequest.test_request(url=url, method='post', headers=headers, data=request_data)
	return [False, 'code不为0'] if resp[1]['code'] != 0 else [True, resp[1]]

# if __name__ == '__main__':
# 	deleteCampaignByName('77ce39ab2ca123899e1a831e1d1a9f01bd83fe44','aa')