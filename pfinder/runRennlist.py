__author__ = 'root'
import os
import scrapy
import json
from pcarfinder import PcarfinderDB
PROJECT_PATH = '/home/scott/pfinder/spider_scrapy/pfinder/'
SCRAPY_PATH='/home/scott/venv/bin/scrapy'
db = PcarfinderDB()
#db.make_spider_initial_flag(2)

os.system(SCRAPY_PATH+" crawl rennlist -a searchterms_str=Porsche")
db.update_rennlist_older()
print('*****  Rennist spider was finished! *****')
