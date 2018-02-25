__author__ = 'root'
import os
import scrapy
import json
from pcarfinder import PcarfinderDB
PROJECT_PATH = '/home/me/Workspace/spider_scrapy/pfinder/'
SCRAPY_PATH='/home/me/Workspace/venv/bin/scrapy'
db = PcarfinderDB()
db.make_spider_initial_flag(4)

with open(PROJECT_PATH+'porschedealer.json') as porsche_file:
    domains = json.load(porsche_file)
for domain in domains:
    crawl_str = SCRAPY_PATH + ' crawl porsche -a searchterms_str=%s' % (domain['name'])
    os.system(crawl_str)
print('***** Updating porsche sold status *****')
db.update_porsche_sold_status()
print('***** Finished porsche sold status *****')
