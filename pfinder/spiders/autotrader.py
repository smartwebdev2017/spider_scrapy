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


class AutotraderSpider(BaseProductsSpider):
    crawlera_enabled = True
    crawlera_apikey = '6c7e115ad3a848d980baac441aa927cc'
    handle_httpstatus_list = [404]
    name = "autotrader"
    allowed_domains = ['autotrader.com']

    agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:35.0) '\
            'Gecko/20100101 Firefox/35.0",

    current_page = 0
    HOME_URL = 'https://www.autotrader.com'
    SEARCH_URL = 'https://www.autotrader.com/rest/searchresults/sunset/base?zip={zipcode}&startYear=1981&numRecords=25&sortBy=derivedpriceDESC&firstRecord=0&endYear=2019&makeCodeList=POR&searchRadius=25'
    NEXT_PAGE_URL = 'https://www.autotrader.com/rest/searchresults/sunset/base?zip={zipcode}&startYear=1981&numRecords=25&sortBy=derivedpriceDESC&firstRecord={start_index}&endYear=2019&makeCodeList=POR&searchRadius=25'
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
        self.zipcode = kwargs.get('zipcode')
        self.SEARCH_URL = self.SEARCH_URL.format(zipcode=self.zipcode)

        url_formatter = FormatterWithDefaults(page_num=1)
        super(AutotraderSpider, self).__init__(url_formatter=url_formatter,
                                             site_name=self.allowed_domains[0],
                                             *args,
                                             **kwargs)

    def start_requests(self):
        # with open("auto.csv", "a") as result:
        #     wr = csv.writer(result)
        #
        #     wr.writerow(['VIN', 'Listing_Make', 'Listing_Model', 'Listing_Trim', 'Listing_Model_Detail', 'Listing_Year', 'Mileage', 'City', 'State', 'Listing_Date', 'Price', 'Condition', 'Seller_Type', 'VHR_Link', 'Listing_Exterior_Color', 'Listing_Interior_Color', 'Listing_Transmission', 'Listing_Transmission_Detail', 'Listing_Title', 'Listing_URL', 'Listing_Engine_Size', 'Listing_Description', 'Sold_Status', 'Sold_Date', 'Listing_Body_Type', 'Listing_Drivetrain'])

        for request in super(AutotraderSpider, self).start_requests():
            if request.meta.get('search_term'):
                yield request

    def parse_product(self, response):
        product = response.meta['product']
        data = response.xpath('//div[@data-birf-role="dataisland"]/@data-birf-extra')[0].extract()
        try:
            data = json.loads(data)
        except Exception as e:
            data = None

        product['listing_year'] = data['page']['vehicle']['car_year']
        try:
            mileage = data['page']['vehicle']['odometer']
            mileage = mileage.replace(' mi', '').replace(',', '')
        except Exception as e:
            mileage = 0

        try:
            listing_trim = response.xpath('//span[@data-qaid="cntnr-vehicle-trim"]/text()')[0].extract()
        except Exception as e:
            listing_trim = ''

        try:
            drive = response.xpath('//td[@data-qaid="tbl-value-Drive Type"]/text()')[0].extract()
            if drive.lower().find('2') > -1 or drive.lower().find('front') > -1 or drive.lower().find('rear') > -1:
                drive = '2WD'
            elif drive.lower().find('4') > -1:
                drive = '4WD'
            elif drive.lower().find('all') > -1:
                drive = '4WD'
        except Exception as e:
            drive = ''

        try:
            engine = response.xpath('//td[@data-qaid="tbl-value-Engine"]/text()')[0].extract()
        except Exception as e:
            engine = ''

        try:
            transmission = response.xpath('//td[@data-qaid="tbl-value-Transmission"]/text()')[0].extract()
            if transmission.lower().find('tiptronic') > -1 or transmission.lower().find('pdk') > -1 or transmission.lower().find('auto') > -1:
                transmission = 'Auto'
            else:
                transmission = 'Manual'

        except Exception as e:
            transmission = ''

        try:
            vhr = response.xpath('//a[@data-birf-par="ec_pa1"]/@href')[0].extract()
            if vhr.find("http://") == -1:
                vhr = self.HOME_URL + vhr
        except Exception as e:
            vhr = ""

        try:
            listing_interior = response.xpath('//div[@data-qaid="cntnr-interiorColor"]/strong/text()')[0].extract()
            if listing_interior.lower().find('unavailable') > -1:
                listing_interior = ''
        except Exception as e:
            listing_interior = ''

        try:
            if data['page']['owner']['seller_type'] == 'p':
                seller_type = 'Private Party'
            else:
                seller_type = 'Dealership'
        except Exception as e:
            seller_type = 'Dealership'

        try:
            city = response.xpath('//span[@itemprop="addressLocality"]/text()')[1].extract()
            state = response.xpath('//span[@itemprop="addressRegion"]/text()')[1].extract()
        except Exception as e:
            city = response.xpath('//div[@data-qaid="no_map_address"]//text()')[5].extract()
            state = response.xpath('//div[@data-qaid="no_map_address"]//text()')[7].extract()
        product['city'] = city
        product['state'] = state

        vin_code = product.get('vin')
        if vin_code is None:
            vin_code = ''

        listing_year = product.get('listing_year')
        listing_make = 'Porsche'
        listing_model = product.get('listing_model')
        try:
            description = response.xpath('//p[@data-qaid="cntnr-listingDescription"]//text()').extract()
            description = "\n".join(description)
        except Exception as e:
            description = ''
        listing_model_detail = product.get('listing_model_detail')

        exterior_color = ''
        if product.get('listing_color') is not None:
            exterior_color = product.get('listing_color')

        listing_title = product.get('listing_title')
        cond = product.get('condition')

        if cond.lower().find('new') == -1:
            cond = 'Used'

        sold_state = 0
        active = 1
        cur_time = datetime.datetime.now()
        cur_str = cur_time.date()
        listing_date = datetime.datetime.now().date()

        if vin_code == '':
            vin = self.db.check_vin_by_url(product['url'])
        else:
            vin = self.db.check_vin_by_code(vin_code)

        site = self.db.get_site_id("autotrader")
        info = {}

        if site is not None:
            if not vin:
                if vin_code != '' and int(listing_year) >= 2001:

                    info['Vin'] = vin_code
                    info['Year'] = listing_year
                    info['Make'] = listing_make
                    info['Model'] = listing_model
                    info['Mileage'] = mileage
                    info['Price'] = product['price']
                    info['Transmission'] = transmission
                    info['DriveTrain'] = drive
                    info['Description'] = description
                    info['listing_trim'] = listing_trim
                    info['listing_model_detail'] = listing_model_detail
                    info['listing_transmission'] = transmission
                    info['listing_color'] = exterior_color
                    info['listing_description'] = description
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
                                info['gap_to_msrp'] = int(product['price'] / float(bsf_data['msrp']) * 100)
                                pcf_id = self.db.insert_parsing_pcf(info)
                                self.db.insert_car(site[0], vin_code.upper(), listing_make, listing_model, listing_trim, listing_model_detail, listing_year, mileage, product['city'], product['state'], listing_date, product['price'], cond, seller_type, vhr, exterior_color, listing_interior, transmission, '', listing_title, product.get('url'), '', description,  sold_state, cur_str, '', drive, datetime.datetime.now(), datetime.datetime.now(), bsf_id, pcf_id, active)
                    else:
                        bs_option_description = ''
                        options = self.db.get_bsf_options(bsf_data[0])
                        for option in options:
                            bs_option_description = bs_option_description + option[2] + ','

                        info['model_detail'] = bsf_data[5]
                        info['model_year'] = bsf_data[4]
                        info['bs_option_description'] = bs_option_description
                        info['gap_to_msrp'] = int(product['price'] / float(bsf_data[2]) * 100)
                        info['pcf_id'] = None
                        pcf_id = self.db.insert_parsing_pcf(info)
                        self.db.insert_car(site[0], vin_code.upper(), listing_make, listing_model, listing_trim, listing_model_detail, listing_year, mileage, product['city'], product['state'], listing_date, product['price'], cond, seller_type, vhr, exterior_color, listing_interior, transmission, '', listing_title, product.get('url'), '', description,  sold_state, cur_str, '', drive, datetime.datetime.now(), datetime.datetime.now(), bsf_data[0], pcf_id, active)
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
                    info['Price'] = product['price']
                    info['Transmission'] = transmission
                    info['DriveTrain'] = drive
                    info['Description'] = description

                    info['model_detail'] = ''
                    try:
                        info['model_number'] = result['model_number']
                    except Exception as e:
                        info['model_number'] = ''
                    info['model_year'] = ''
                    info['listing_trim'] = listing_trim
                    info['listing_model_detail'] = listing_model_detail
                    info['listing_transmission'] = transmission
                    info['bs_option_description'] = ''
                    info['listing_color'] = exterior_color
                    info['listing_description'] = description
                    info['gap_to_msrp'] = 0

                    pcf_id = self.db.get_same_description_pcf(listing_title, description)
                    if pcf_id is None:
                        pcf_id = self.db.insert_parsing_pcf(info)
                    else:
                        print('same %s pcf_id is exist!' % (pcf_id))
                    self.db.insert_car(site[0], vin_code.upper(), listing_make, listing_model, listing_trim, listing_model_detail, listing_year, mileage, product['city'], product['state'], listing_date, product['price'], cond, seller_type, vhr, exterior_color, listing_interior, transmission, '', listing_title, product.get('url'), '', description,  sold_state, cur_str, '', drive, datetime.datetime.now(), datetime.datetime.now(), None, pcf_id, active)
            else:
                if vin_code == '':
                    row = self.db.update_car_by_url(vin_code.upper(), listing_make, listing_model, listing_trim, listing_model_detail, listing_year, mileage, product['city'], product['state'], listing_date, product['price'], cond, seller_type, vhr, exterior_color, listing_interior, transmission, '', listing_title, product.get('url'), '', description,  0, cur_str, '', drive, datetime.datetime.now(), site[0], active)
                else:
                    row = self.db.update_car_by_id(vin_code.upper(), listing_make, listing_model, listing_trim, listing_model_detail, listing_year, mileage, product['city'], product['state'], listing_date, product['price'], cond, seller_type, vhr, exterior_color, listing_interior, transmission, '', listing_title, product.get('url'), '', description,  0, cur_str, '', drive, datetime.datetime.now(), site[0], active, vin)
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
                    info['Price'] = product['price']
                    info['Transmission'] = transmission
                    info['DriveTrain'] = drive
                    info['Description'] = description

                    try:
                        info['model_number'] = result['model_number']
                    except Exception as e:
                        info['model_number'] = ''
                    info['listing_trim'] = listing_trim
                    info['listing_model_detail'] = listing_model_detail
                    info['listing_transmission'] = transmission
                    info['listing_color'] = exterior_color
                    info['listing_description'] = description

                    bs_option_description = ''
                    if bsf_data is not None:
                        options = self.db.get_bsf_options(bsf_data[0])
                        for option in options:
                            bs_option_description = bs_option_description + option[2] + ','

                        info['model_detail'] = bsf_data[5]
                        info['model_year'] = bsf_data[4]
                        info['bs_option_description'] = bs_option_description
                        info['gap_to_msrp'] = int(product['price'] / float(bsf_data[2]) * 100)
                    else:
                        info['model_detail'] = ''
                        info['model_year'] = ''
                        info['bs_option_description'] = ''
                        info['gap_to_msrp'] = 0

                    self.db.insert_parsing_pcf(info)
                except Exception as err:
                    print(err)

            # with open("auto.csv", "a") as result:
            #     wr = csv.writer(result)
            #     #wr.writerow(['VIN', 'Listing_Make', 'Listing_Model', 'Listing_Trim', 'Listing_Model_Detail', 'Listing_Year', 'Mileage', 'City', 'State', 'Listing_Date', 'Price', 'Condition', 'Seller_Type', 'VHR_Link', 'Listing_Color', 'Listing_Interio_Color', 'Listing_Transmission', 'Listing_Transmission_Detail', 'Listing_Title', 'Listing_URL', 'Listing_Engine_Size', 'Listing_Description', 'Sold_Status', 'Sold_Date', 'Listing_Body_Type', 'Drivetrain'])
            #     try:
            #         wr.writerow([vin_code.upper(), listing_make, listing_model, listing_trim, listing_model_detail, listing_year, mileage, product['city'], product['state'], listing_date, product['price'], cond, seller_type, vhr, exterior_color, listing_interior, transmission, '', listing_title, product.get('url'), '', description,  sold_state, cur_str, '', drive])
            #     except Exception as err:
            #         print(err)

    def _scrape_product_links(self, response):
        data = json.loads(response.body)
        products = data['listings']

        for product in products:
            title = product.get('title')
            vin = product.get('vin')
            try:
                price = product.get('derivedPrice').replace("$", "").replace(",", "")
            except Exception as e:
                price = 0

            cond = product.get('listingType')

            if cond.lower().find('new') > -1:
                continue

            msrp = product.get('msrp')
            try:
                trim = product['trim']
            except Exception as e:
                trim = ''

            modelCode = product.get('modelCode')
            description = product.get('description')
            exterior_color = product.get('colorExteriorSimple')
            try:
                model_detail = (modelCode + ' ' + trim).strip()
            except Exception as e:
                model_detail = ''
            st = response.meta['search_term']
            link_zip = product.get('vdpSeoUrl')
            try:
                link = re.search('(.*)&zip',link_zip).group(1)
            except Exception as e:
                link = link_zip
            prod_item = SiteProductItem()
            #
            prod_item['listing_title'] = title
            prod_item['vin'] = vin
            prod_item['price'] = int(price)
            prod_item['condition'] = cond
            prod_item['listing_model'] = modelCode
            prod_item['listing_description'] = description
            prod_item['listing_color'] = exterior_color
            prod_item['listing_model'] = modelCode
            prod_item['listing_model_detail'] = model_detail
            prod_item['url'] = self.HOME_URL + link

            req = Request(
                url=self.HOME_URL + link,
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
        pass

    def _scrape_next_results_page_link(self, response):
        st = response.meta['search_term']
        data = json.loads(response.body)

        total_pages = data['pagination']['totalPages']
        total_matches = data['matchListingCount']

        if self.current_page * 25 > int(total_matches.replace(",", "")):
            return

        self.current_page += 1
        next_page_link = self.NEXT_PAGE_URL.format(zipcode = self.zipcode, start_index = (self.current_page - 1) * 25)

        return Request(
            url = next_page_link,
            #headers=self.HEADERS,
            meta={
                'search_term': st,
                'remaining': sys.maxint
            },
            dont_filter=True
        )

    def _clean_text(self, text):
        return re.sub("[\r\n\t]", "", text).strip()
