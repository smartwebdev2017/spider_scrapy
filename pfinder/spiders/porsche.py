__author__ = 'root'

import scrapy
import sys
import urlparse
from pfinder.spiders import BaseProductsSpider
from pfinder.spiders import FormatterWithDefaults, cond_set_value
from pfinder.items import SiteProductItem
from scrapy.conf import settings
from pfinder.US_States import STATES
from scrapy.http import Request
from twisted.internet._sslverify import ClientTLSOptions
from twisted.internet.ssl import ClientContextFactory
from scrapy.core.downloader.contextfactory import ScrapyClientContextFactory
from OpenSSL import SSL
from decimal import Decimal
from pfinder.pcarfinder import PcarfinderDB
import json
import urllib2

import csv
import re
import datetime


class PorscheSpider(BaseProductsSpider):
    crawlera_enabled = True
    crawlera_apikey = '6c7e115ad3a848d980baac441aa927cc'
    handle_httpstatus_list = [404]
    name = "porsche"
    allowed_domains = ['{search_term}']

    agent = "iphone_ipad': 'Mozilla/5.0 (iPhone; CPU iPhone OS 7_0_6 like Mac OS X) AppleWebKit/537.51.1 (KHTML, like Gecko) Version/7.0 Mobile/11B651 Safari/9537.53",

    current_page = 1
    HOME_URL = 'https://{search_term}'
    SEARCH_URL = 'https://{search_term}/inventory?condition=all&make=Porsche&limit=10'

    NEXT_PAGE_URL = 'https://{search_term}/inventory?condition=all&make=Porsche&limit=10&page={start_index}'
    HEADERS={
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate, sdch, br",
            "Accept-Language": "en-US,en;q=0.8",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "DNT":"1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": agent
    }

    def __init__(self, *args, **kwargs):

        self.db = PcarfinderDB()

        self.total_matches = None

        url_formatter = FormatterWithDefaults(page_num=1)
        super(PorscheSpider, self).__init__(url_formatter=url_formatter,
                                             site_name=self.allowed_domains[0],
                                             *args,
                                             **kwargs)

    def start_requests(self):
        for request in super(PorscheSpider, self).start_requests():
            if request.meta.get('search_term'):
                yield request

    def parse_product(self, response):
        cond_year = response.xpath('//div[@id="headline"]/h1/span/text()')[0].extract()
        cond_year_match = re.match('(\D+)\s(\d+)', cond_year)
        inventory_id = response.xpath('//input[@id="inventory_id"]/@value')[0].extract()
        try:
            cond, listing_year = cond_year_match.groups()
        except Exception as e:
            pass
        listing_make = 'Porsche'
        listing_model = response.xpath('//span[@itemprop="model"]/text()')[0].extract()
        listing_model_detail = listing_model
        city_state = response.xpath('//div[@id="headline"]/h1/small/text()')[0].extract()
        city_state_match = re.match('Located\sin\s(.*),\s(.*)', city_state)
        city, state = city_state_match.groups()
        state = STATES[state.lower()]
        listing_title = '{} {} {}'.format(cond_year, listing_make, listing_model)
        listing_date = datetime.datetime.now().date()
        listing_url = response.url

        keys_obj = response.xpath('//div[@class="panel-body"]/dl/dt')
        values  = response.xpath('//div[@class="panel-body"]/dl/dd')

        vin_code = ''
        listing_trim = ''
        listing_price = 0
        cond = ''
        mileage = 0
        listing_exterior_color = ''
        listing_interior_color = ''
        listing_transmission = ''
        listing_transmission_detail = ''
        listing_engine = ''
        listing_drivetrain = ''
        listing_description = ''

        index = 0

        try:
            vhr = response.xpath('//a[@class="us-experian-link-destkop"]/@href')[0].extract()
            pass
        except Exception as e:
            vhr = ''

        for key_obj in keys_obj:
            key = key_obj.xpath('text()')[0].extract()
            try:
                value = values[index].xpath('text()')[0].extract()
            except Exception as e:
                value = None
                print(e)
            if key == 'Price:':
                try:
                    listing_price_str = values[index].xpath('strong[@id="vehicle-detail-price"]/text()')[0].extract()
                    listing_price = float(re.sub(r'[^\d.]', '', listing_price_str))
                except Exception as e:
                    index+= 1
                    listing_price_str = values[index].xpath('strong[@id="vehicle-detail-price"]/text()')[0].extract()
                    listing_price = float(re.sub(r'[^\d.]', '', listing_price_str))
            elif key == "Condition:":
                cond = value
                if cond.lower().find('new') == -1:
                    cond = 'Used'
            elif key == "Mileage:":
                mileage = value.replace(' mi', '').replace(',', '')
            elif key == "Exterior Color:":
                listing_exterior_color = value
            elif key == "Interior Color:":
                listing_interior_color = value
            elif key == "Transmission:":
                listing_transmission_detail = value

                if listing_transmission_detail.lower().find('tiptronic') > -1 or listing_transmission_detail.lower().find('pdk') > -1 or listing_transmission_detail.lower().find('auto') > -1:
                    listing_transmission = 'Auto'
                else:
                    listing_transmission = 'Manual'
            elif key == "Engine:":
                listing_engine = value
                listing_engine = re.search('(\w.\w+)\s', listing_engine).group(1)
            elif key == "Drivetrain:":
                listing_drivetrain = value
                if listing_drivetrain.lower().find('all') > -1 or listing_drivetrain.lower().find('4wd') > -1:
                    listing_drivetrain = '4WD'
                else:
                    listing_drivetrain = '2WD'
            elif key == "VIN (Vehicle Identification Number):":
                vin_code = value
            elif key == "Stock #:":
                listing_description = "Stock #: " + value

            index += 1

        listing_url = self.HOME_URL.format(search_term=response.meta['search_term']) + "/inventory/" + cond.lower() + "/" + inventory_id

        if vin_code == '':
            vin = self.db.check_vin_by_url(listing_url)
        else:
            vin = self.db.check_vin_by_code(vin_code)

        site = self.db.get_site_id("porsche")
        info = {}
        active = 1
        sold_state = 0
        seller_type = 'Dealership'
        cur_time = datetime.datetime.now()
        cur_str = cur_time.date()

        if site is not None:
            if not vin:
                if vin_code != '' and int(listing_year) >= 2001:
                    info['Vin'] = vin_code
                    info['Year'] = listing_year
                    info['Make'] = listing_make
                    info['Model'] = listing_model
                    info['Mileage'] = mileage
                    info['Price'] = listing_price
                    info['Transmission'] = listing_transmission
                    info['DriveTrain'] = listing_drivetrain
                    info['Description'] = listing_description
                    info['listing_trim'] = listing_trim
                    info['listing_model_detail'] = listing_model_detail
                    info['listing_transmission'] = listing_transmission
                    info['listing_color'] = listing_exterior_color
                    info['listing_description'] = listing_description
                    result = self.db.parsing_vin(vin_code.upper(), listing_year, listing_model)

                    try:
                        info['model_number'] = result.get('model_number')
                    except Exception as e:
                        info['model_number'] = ''

                    bsf_data = self.db.check_bsf(vin_code)

                    if bsf_data is None:
                        retry_result = self.db.checkRetryCar(vin_code)

                        if retry_result is None:
                            bsf_data = self.db.getBSinfo(vin_code)

                            if bsf_data is not None:
                                bsf_id = self.db.insert_bsf(vin_code, bsf_data['msrp'], bsf_data['warranty_start'], bsf_data['model_year'], bsf_data['model_detail'], bsf_data['color'], datetime.datetime.strptime(bsf_data['production_month'], '%m/%Y'), bsf_data['interior'])
                                bs_option_description = ''

                                for option in bsf_data['options']:
                                    self.db.insert_bsf_options(bsf_id, option['code'], option['value'])
                                    bs_option_description = bs_option_description + option['value'] + ','

                                info['model_detail'] = bsf_data['model_detail']
                                info['model_year'] = bsf_data['model_year']
                                info['bs_option_description'] = bs_option_description
                                info['gap_to_msrp'] = int(listing_price / float(bsf_data['msrp']) * 100)
                                pcf_id = self.db.insert_parsing_pcf(info)
                                self.db.insert_car(site[0], vin_code.upper(), listing_make, listing_model, listing_trim, listing_model_detail, listing_year, mileage, city, state, listing_date, listing_price, cond, seller_type, vhr, listing_exterior_color, '', listing_transmission, listing_transmission_detail, listing_title, listing_url, '', listing_description,  sold_state, None, '', listing_drivetrain, datetime.datetime.now(), 1, bsf_id, pcf_id, active)
                    else:
                        bs_option_description = ''
                        options = self.db.get_bsf_options(bsf_data[0])
                        for option in options:
                            bs_option_description = bs_option_description + option[2] + ','

                        info['model_detail'] = bsf_data[5]
                        info['model_year'] = bsf_data[4]
                        info['bs_option_description'] = bs_option_description
                        info['gap_to_msrp'] = int(listing_price / float(bsf_data[2]) * 100)
                        info['pcf_id'] = None
                        pcf_id = self.db.insert_parsing_pcf(info)
                        self.db.insert_car(site[0], vin_code.upper(), listing_make, listing_model, listing_trim, listing_model_detail, listing_year, mileage, city, state, listing_date, listing_price, cond, seller_type, vhr, listing_exterior_color, '', listing_transmission, listing_transmission_detail, listing_title, listing_url, '', listing_description,  sold_state, None, '', listing_drivetrain, datetime.datetime.now(), 1, bsf_data[0], pcf_id, active)
                else:
                    result = self.db.parsing_vin(vin_code.upper(), listing_year, listing_model)

                    info['Vin'] = vin_code
                    try:
                        info['Year'] = listing_year
                    except Exception as err:
                        print(err)
                        listing_year = 0
                    info['Make'] = listing_make
                    info['Model'] = listing_model
                    info['Mileage'] = mileage
                    info['Price'] = listing_price
                    info['Transmission'] = listing_transmission
                    info['DriveTrain'] = listing_drivetrain
                    info['Description'] = listing_description

                    info['model_detail'] = ''
                    try:
                        info['model_number'] = result['model_number']
                    except Exception as e:
                        info['model_number'] = ''
                    info['model_year'] = ''
                    info['listing_trim'] = listing_trim
                    info['listing_model_detail'] = listing_model_detail
                    info['listing_transmission'] = listing_transmission
                    info['bs_option_description'] = ''
                    info['listing_color'] = listing_exterior_color
                    info['listing_description'] = listing_description
                    info['gap_to_msrp'] = 0

                    pcf_id = self.db.get_same_description_pcf(listing_title, listing_description)
                    if pcf_id is None:
                        pcf_id = self.db.insert_parsing_pcf(info)
                    else:
                        print('same %s pcf_id is exist!' % (pcf_id))
                    self.db.insert_car(site[0], vin_code.upper(), listing_make, listing_model, listing_trim, listing_model_detail, listing_year, mileage, city, state, listing_date, listing_price, cond, seller_type, vhr, listing_exterior_color, '', listing_transmission, listing_transmission_detail, listing_title, listing_url, '', listing_description,  sold_state, None, '', listing_drivetrain, datetime.datetime.now(), 1, None, pcf_id, active)
            else:
                if vin_code == '':
                    row = self.db.update_car_by_url(vin_code.upper(), listing_make, listing_model, listing_trim, listing_model_detail, listing_year, mileage, city, state, listing_date, listing_price, cond, seller_type, vhr, listing_exterior_color, '', listing_transmission, listing_transmission_detail, listing_title, listing_url, '', listing_description,  0, cur_str, '', listing_drivetrain, 1, site[0], active)
                else:
                    row = self.db.update_car_by_id(vin_code.upper(), listing_make, listing_model, listing_trim, listing_model_detail, listing_year, mileage, city, state, listing_date, listing_price, cond, seller_type, vhr, listing_exterior_color, '', listing_transmission, listing_transmission_detail, listing_title, listing_url, '', listing_description,  0, cur_str, '', listing_drivetrain, 1, site[0], active, vin)
                try:
                    info['pcf_id'] = row[29]
                    d1 = row[10]
                    d2 = datetime.datetime.now()

                    listing_age = (d2.date() - d1).days
                    info['listing_age'] = listing_age
                    result = self.db.parsing_vin(vin_code.upper(), listing_year, listing_model)
                    bsf_data = self.db.check_bsf(vin_code)

                    info['Vin'] = vin_code
                    try:
                        info['Year'] = listing_year
                    except Exception as err:
                        print(err)
                        listing_year = 0
                    info['Make'] = listing_make
                    info['Model'] = listing_model
                    info['Mileage'] = mileage
                    info['Price'] = listing_price
                    info['Transmission'] = listing_transmission
                    info['DriveTrain'] = listing_drivetrain
                    info['Description'] = listing_description

                    try:
                        info['model_number'] = result['model_number']
                    except Exception as e:
                        info['model_number'] = ''
                    info['listing_trim'] = listing_trim
                    info['listing_model_detail'] = listing_model_detail
                    info['listing_transmission'] = listing_transmission
                    info['listing_color'] = listing_exterior_color
                    info['listing_description'] = listing_description

                    bs_option_description = ''
                    if bsf_data is not None:
                        options = self.db.get_bsf_options(bsf_data[0])
                        for option in options:
                            bs_option_description = bs_option_description + option[2] + ','

                        info['model_detail'] = bsf_data[5]
                        info['model_year'] = bsf_data[4]
                        info['bs_option_description'] = bs_option_description
                        info['gap_to_msrp'] = int(listing_price / float(bsf_data[2]) * 100)
                    else:
                        info['model_detail'] = ''
                        info['model_year'] = ''
                        info['bs_option_description'] = ''
                        info['gap_to_msrp'] = 0

                    self.db.insert_parsing_pcf(info)
                except Exception as err:
                    print(err)


    def _scrape_product_links(self, response):
        products = response.xpath('//div[@id="inventory-list-container"]//div[@class="vehicle-listing-ymm"]/a/@href')

        for product in products:
            st = response.meta['search_term']
            link = product.extract()
            prod_item = SiteProductItem()

            req = Request(
                url=self.HOME_URL.format(search_term=st) + link,
                callback=self.parse_product,
                meta={
                    'product': prod_item,
                    'search_term': st,
                    'remaining': sys.maxint,
                },
                dont_filter=True,
                headers={"User-Agent": self.agent}
            )
            yield req, prod_item


    def after_start(self, response):
        pass
    def __parse_sing_product(self, response):
        return self.parse_product(response)

    def _scrape_total_matches(self, response):
        total_matches = self._clean_text(response.xpath('//div[@id="inventory-pager-result-counter"]/text()')[0].extract())
        try:
            match = re.match('(\d+)\sto\s(\d+)\sof\s(\d+)', total_matches)
            start, end, total = match.groups()
        except Exception as e:
            total = 0

        return int(total) if total else 0

    def _scrape_next_results_page_link(self, response):
        st = response.meta['search_term']
        total_matches = self._scrape_total_matches(response)

        if self.current_page * 10 > total_matches:
            return

        self.current_page += 1
        next_page_link = self.NEXT_PAGE_URL.format(search_term=st, start_index = self.current_page)

        return Request(
            url = next_page_link,
            headers=self.HEADERS,
            meta={
                'search_term': st,
                'remaining': sys.maxint
            },
            dont_filter=True
        )

    def _clean_text(self, text):
        return re.sub("[\r\n\t]", "", text).strip()
