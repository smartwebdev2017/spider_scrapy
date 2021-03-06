__author__ = 'root'
import os
import scrapy
import json
from pcarfinder import PcarfinderDB
PROJECT_PATH = '/home/scott/pfinder/spider_scrapy/pfinder/'
SCRAPY_PATH='/home/scott/venv/bin/scrapy'
db = PcarfinderDB()
db.make_spider_initial_flag(1)

os.system(SCRAPY_PATH + " crawl carmax -a searchterms_str=Porsche")
print('*****  Carmax spider was finished! *****')
print('***** Updating carmax sold status *****')
db = PcarfinderDB()
db.update_carmax_sold_status()
print('***** Finished carmax sold status *****')
