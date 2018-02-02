__author__ = 'root'
import os
import scrapy
import json
from pcarfinder import PcarfinderDB
PROJECT_PATH = '/home/smartwebdev2017/pfinder/spider_scrapy/pfinder/'
SCRAPY_PATH='/home/smartwebdev2017/pfinder/venv/bin/scrapy'
db = PcarfinderDB()
os.system(SCRAPY_PATH + " crawl carmax -a searchterms_str=Porsche")
print('*****  Carmax spider was finished! *****')
print('***** Updating carmax sold status *****')
db.update_carmax_sold_status()
print('***** Finished carmax sold status *****')
#exit()
os.system(SCRAPY_PATH+" crawl rennlist -a searchterms_str=Porsche")
print('*****  Rennist spider was finished! *****')
with open(PROJECT_PATH+'shortcodes.json') as data_file1:
    state_obj = json.load(data_file1)
n_states = {}
for state in state_obj:
    n_states[state['label'].lower()] = state['value']
with open(PROJECT_PATH+'city_state.json') as data_file:
    city_obj = json.load(data_file)
for item in city_obj:
    shortcode = item['shortcode']
    state = n_states[item['state'].lower()]
    crawl_str = SCRAPY_PATH + ' crawl craigslist -a searchterms_str=%s -a state=%s' % (shortcode, state)
    print(crawl_str)
    os.system(crawl_str)
print('*****  Craigslist spider was finished! *****')
print('***** Updating craigslist sold status *****')
db.update_craigslist_sold_status()
print('***** Finished craigslist sold status *****')
db.update_rennlist_older()
with open('porschedealer.json') as porsche_file:
    domains = json.load(porsche_file)
for domain in domains:
    crawl_str = SCRAPY_PATH + ' crawl porsche -a searchterms_str=%s' % (domain['name'])
    os.system(crawl_str)
print('***** Updating porsche sold status *****')
db.update_porsche_sold_status()
print('***** Finished porsche sold status *****')