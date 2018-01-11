__author__ = 'root'

import os
import scrapy
import json
from pcarfinder import PcarfinderDB


db = PcarfinderDB()
db.update_rennlist_cond()
db.remove_scam()
db.update_model_number()