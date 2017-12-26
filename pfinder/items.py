# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.item import Item, Field

class PcarfinderItem(scrapy.Item):
    # define the fields for your item here like:
    name = scrapy.Field()

class SiteProductItem(Item):
    #Search metadata.
    site = Field()
    search_term = Field()
    ranking = scrapy.Field()
    total_matches = scrapy.Field()
    results_per_page = scrapy.Field()
    scraped_results_per_page = scrapy.Field()

    #Indicates whether this Item comes from scraping single product url
    is_single_result = scrapy.Field()

    #Product data
    id = Field()
    url = Field()
    listing_date = Field()
    seller_type = Field()
    sold_status = Field()
    sold_date = Field()
    listing_year = Field()
    listing_make = Field()
    listing_model = Field()
    mileage = Field()
    condition = Field()
    price = Field()
    listing_color = Field()
    vin = Field()
    city = Field()
    state = Field()
    listing_body_type = Field()
    listing_transmission = Field()
    listing_transmission_detail = Field()
    drive_train = Field()
    listing_model_detail = Field()
    listing_url = Field()
    listing_title = Field()
    listing_description = Field()
    vhr_link = Field()
    dealer_ship = Field()

