__author__ = 'root'

import os
import scrapy
import json
from pcarfinder import PcarfinderDB


db = PcarfinderDB()
os.system("scrapy crawl carmax -a searchterms_str=Porsche")
print('*****  Carmax spider was finished! *****')
print('***** Updating carmax sold status *****')
db.update_carmax_sold_status()
print('***** Finished carmax sold status *****')

os.system("scrapy crawl rennlist -a searchterms_str=Porsche")
print('*****  Rennist spider was finished! *****')

with open('shortcodes.json') as data_file1:
    state_obj = json.load(data_file1)

n_states = {}
for state in state_obj:
    n_states[state['label'].lower()] = state['value']

with open('city_state.json') as data_file:
    city_obj = json.load(data_file)

for item in city_obj:
    shortcode = item['shortcode']
    state = n_states[item['state'].lower()]
    crawl_str = 'scrapy crawl craigslist -a searchterms_str=%s -a state=%s' % (shortcode, state)
    print(crawl_str)
    os.system(crawl_str)
print('*****  Craigslist spider was finished! *****')
print('***** Updating craigslist sold status *****')
db.update_carmax_sold_status()
print('***** Finished craigslist sold status *****')