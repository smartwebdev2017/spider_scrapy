__author__ = 'root'
import os
import scrapy
import json
from pcarfinder import PcarfinderDB
PROJECT_PATH = '/home/me/Workspace/spider_scrapy/pfinder/'
SCRAPY_PATH='/home/me/Workspace/venv/bin/scrapy'
db = PcarfinderDB()
db.make_spider_initial_flag(5)

with open(PROJECT_PATH+'zipcodes.json') as data_file:
    zipcodes = json.load(data_file)
for item in zipcodes:
    for code in range(int(item['from']), int(item['to'])):
        crawl_str = SCRAPY_PATH + ' crawl autotrader -a searchterms_str=porsche -a zipcode=%s' % (code)
        print(crawl_str)
        os.system(crawl_str)
print('*****  Autotrader spider was finished! *****')
print('***** Updating autotrader sold status *****')
db.update_autotrader_sold_status()
