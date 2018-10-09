#!/usr/bin/env python3
# -*- coding: utf-8 -*-

' 执行器  '

__author__ = "liuxiaolei"

from TestData import *
import pytest
import requests
import json
import logging

# print(test_data['case_name'])

       
class TestRunner(object):
    
    @pytest.fixture(scope="module", params=test_data)
    def before_module(self,request):
        self.param = request.param
        print("000000-setup")
        yield self.param
        print("000000-teardown")
        
#   执行前置条件和后置条件
    @pytest.fixture(scope="class", params=test_data[0][0])
    def before_class(self,request):
        param = request.param
        print("测试用例名称为：%s" % param['case_name'])
        print("host为：%s" % param['case_name'])
        if param.has_key('beforeClass'):
            print("前置条件数据为：%s" % param['before'])
        
        
        yield before_class
        
        if param.has_key('after_class'):
            print("后置条件数据为：%s" % param['after'])
        print("111111-teardown")
        
    @pytest.fixture(params=test_data[0][0]['testcase'])
    def case(self,request,):
        print("22222222-setup")
        yield request.param
        print("22222222-teardown")
    
    def test_main(self,case,before_class,before_module):
        url = case['url']
        logging.info("url= %s" %url)
        assert case['No'] == 2,"msg %s" %case['No']
        assert 0
    
    
if  __name__ == "__main__":
    pytest.main()
    
    


