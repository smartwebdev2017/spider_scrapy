__author__ = 'root'

import os
import scrapy
import json
from pcarfinder import PcarfinderDB


db = PcarfinderDB()
#db.update_rennlist_cond()
#db.remove_scam()
#db.get_modelnumber('1973', '911')
#db.update_model_number()
#db.remove_listings('958')
#db.update_cond();
db.move_listing_date()