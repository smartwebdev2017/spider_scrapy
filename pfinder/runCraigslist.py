__author__ = 'root'
import os
import scrapy
import json
from pcarfinder import PcarfinderDB
PROJECT_PATH = '/home/scott/pfinder/spider_scrapy/pfinder/'
SCRAPY_PATH='/home/scott/venv/bin/scrapy'
db = PcarfinderDB()
db.make_spider_initial_flag(3)

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
db = PcarfinderDB()
db.update_craigslist_sold_status()
print('***** Finished craigslist sold status *****')
