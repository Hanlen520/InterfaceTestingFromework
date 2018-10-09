# encoding: utf-8

import os
import logging

if os.path.exists(os.path.abspath('..') + '\Log\log.txt'):
    os.remove(os.path.abspath('..') + '\Log\log.txt')
logger = logging.getLogger(u'接口测试日志')
logger.setLevel(level = logging.INFO)
handler = logging.FileHandler(os.path.abspath('..') + '\Log\log.txt')
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(formatter)

logger.addHandler(handler)
logger.addHandler(console)




