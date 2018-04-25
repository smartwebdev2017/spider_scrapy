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
from pfinder.pcarfinder import PcarfinderDB
import json
import urllib2
import Cookie
import os
import csv
import re
import datetime
from selenium import webdriver

class HemmingsSpider(BaseProductsSpider):
    #crawlera_enabled = True
    #crawlera_apikey = '6c7e115ad3a848d980baac441aa927cc'
    driverpath = '/home/me/Workspace/spider_scrapy/pfinder'
    driver = webdriver.PhantomJS(executable_path=driverpath + '/phantomjs')
    tries = 0
    cookies_dict = {}

    handle_httpstatus_list = [503, 407]
    name = "hemmings"
    allowed_domains = ['www.hemmings.com']

    agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36",

    HOME_URL = "https://www.hemmings.com"
    current_page = 1
    extract_pattern = ['Sunroof', 'Coupe', 'Manual', 'Convertible', 'converti','Conver',  'Sedan', 'Classic Car', 'True', 'Barn','Find!', '5 Speed Manual Transmission', 'Sport Utility Vehicle 4 Door',
                       'SUV 4 Door', '2dr Car', '2 door', '4 speed', 'autmotic', 'manual transmission', '6 speed', 'not specified', 'Sport Utility Vehicl', '2-dr',
                       'Hatchback', 'Conv', '6-S', '2DR Turbo']

    SEARCH_URL = 'https://www.hemmings.com/classifieds/?0=0&adtypeFacet=Vehicles%20for%20Sale&makeFacet=Porsche&country[]=US&sort=sort_time_desc&page_size=60&start={start_index}'
    # URL_STATES = {
    #     'https://{search_term}.craigslist.org/search/cta?auto_make_model=Porsche', 'CA'
    # }
    NEXT_PAGE_URL = 'https://www.hemmings.com/classifieds/?0=0&adtypeFacet=Vehicles%20for%20Sale&makeFacet=Porsche&country[]=US&sort=sort_time_desc&page_size=60&start={start_index}'
    HEADERS={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, sdch, br",
            "Accept-Language": "en-US,en;q=0.8",
            "method": "get",
            "Cache-Control": "max-age=0",
            #"Connection": "keep-alive",
            #"DNT":"1",
            #"Upgrade-Insecure-Requests": "1",
            #"cookie": "visid_incap_984766=L4pKYVELTiGpHf1vVyxGjeO22VoAAAAAQUIPAAAAAACUsigLnrSl9O2J5W/jUJ9q; __utmz=114059806.1524215273.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); __gads=ID=d3dc5ca0d446d107:T=1524217574:S=ALNI_MbpZii_me-AyJXoThp97Vg5eJpHIw; AMCV_653F60B351E568560A490D4D%40AdobeOrg=1766948455%7CMCMID%7C64157379492117918583861199695401241584%7CMCAID%7CNONE%7CMCAAMLH-1524621134%7C6%7CMCAAMB-1524621134%7Cj8Odv6LonN4r3an7LhD3WZrU1bUpAkFkkiY1ncBR96t2PTI; fitracking_12=no; __qca=P0-88327587-1524016340616; s_fid=78FC1AD688A7D176-2A5AF404FA2C8C06; c_code_2016=DE; U=35824841115ad6a4d867f7f7a4cee3; nlbi_984766=TfMKZQ3te3He+uwEqlAkVQAAAADFe45X8+obTbeWAkWEkh/h; s_cc=true; __utmc=114059806; incap_ses_534_984766=fO/HIsYqpzQiUknOpCZpB+O22VoAAAAAhBmD4UmEt9Xi1ChVtpXXKg==; __utma=114059806.204852835.1524215273.1524215273.1524215273.1; __utmt=1; fiutm=direct|direct||||; __utmb=114059806.1.10.1524215273",
            "User-Agent": agent
    }

    def __init__(self, *args, **kwargs):

        self.driver.get(self.HOME_URL)
        if self.tries == 0:
            self.driver.maximize_window()
        self.driver.implicitly_wait(2)
        self.driver.get_screenshot_as_file(self.driverpath + 'screenshot.png')
        self.cookies = self.driver.get_cookies()


        for cookie in self.cookies:
            self.cookies_dict[cookie['name']] = cookie['value']

        self.db = PcarfinderDB()

        self.total_matches = None

        self.state = kwargs.get('state')

        url_formatter = FormatterWithDefaults(page_num=1)
        super(HemmingsSpider, self).__init__(url_formatter=url_formatter,
                                             site_name=self.allowed_domains[0],
                                             *args,
                                             **kwargs)

        #settings.overrides['DOWNLOAD_DELAY'] = 1




    # def loadStates(self, states):
    #     n_states = {}
    #
    #     for state in states:
    #         n_states[state['label']] = state['value']
    #
    #     return n_states

    def start_requests(self):
        with open("out_car_hemmings.csv", "a") as result:
            wr = csv.writer(result)
            wr.writerow(['VIN', 'Listing_Make', 'Listing_Model', 'Listing_Trim', 'Listing_Model_Detail', 'Listing_Year', 'Mileage', 'City', 'State', 'Listing_Date', 'Price', 'Condition', 'Seller_Type', 'VHR_Link', 'Listing_Exterior_Color', 'Listing_Interior_Color', 'Listing_Transmission', 'Listing_Transmission_Detail', 'Listing_Title', 'Listing_URL', 'Listing_Engine_Size', 'Listing_Description', 'Sold_Status', 'Sold_Date', 'Listing_Body_Type', 'Listing_Drivetrain'])

        yield Request(
            self.HOME_URL,
            #cookies={
                     #"visid_incap_984766":"L4pKYVELTiGpHf1vVyxGjeO22VoAAAAAQkIPAAAAAACArqGDAdWIXo83eSJ2rHCkeVxVa362DIvv",
                     #"__utmz":"114059806.1524215273.1.1.",
                     #"utmcsr":"(direct)|utmccn=(direct)|utmcmd=(none)",
                     #"__gads":"=ID=d3dc5ca0d446d107:T=1524217574:S=ALNI_MbpZii_me-AyJXoThp97Vg5eJpHIw; AMCV_653F60B351E568560A490D4D%40AdobeOrg=1766948455%7CMCMID%7C64157379492117918583861199695401241584%7CMCAID%7CNONE%7CMCAAMLH-1524621134%7C6%7CMCAAMB-1524621134%7Cj8Odv6LonN4r3an7LhD3WZrU1bUpAkFkkiY1ncBR96t2PTI",
                     #"fitracking_12":"no",
                     # "__qca":"P0-88327587-1524016340616; s_fid=78FC1AD688A7D176-2A5AF404FA2C8C06; c_code_2016=DE; U=35824841115ad6a4d867f7f7a4cee3; nlbi_984766=TfMKZQ3te3He+uwEqlAkVQAAAADFe45X8+obTbeWAkWEkh/h; s_cc=true",
                     #"__utmc":"114059806",
                     #"incap_ses_534_984766":"bmtRCM3Yiww6dXnOpCZpB/L32VoAAAAAAYZXHhqBSdMG3YPs0Zu38Q==",
                     #"__utma":"114059806.204852835.1524215273.1524215273.1524215273.1",
                     #"__utmt":"1",
                     #"fiutm":"direct|direct||||",
                     #"__utmb":"114059806.1.10.1524215273",
            #},
            headers=self.HEADERS,
            callback=self._start_requests
        )

    def _start_requests(self, response):
        #cookies = []
        #cookies = response.headers['Set-Cookie']
        #c = Cookie.SimpleCookie(cookies)
        #self.cookie = c['incap_ses_534_984766'].value
        if not self.product_url:
            for st in self.searchterms:
                yield Request(
                    url=self.SEARCH_URL.format(search_term=st, start_index = (self.current_page - 1) * 20, page_num=self.current_page),
                    meta={
                        'search_term': st,
                        'remaining': sys.maxint
                    },
                    cookies={
                             #"visid_incap_984766":"L4pKYVELTiGpHf1vVyxGjeO22VoAAAAAQkIPAAAAAACArqGDAdWIXo83eSJ2rHCkeVxVa362DIvv",
                             #"__utmz":"114059806.1524215273.1.1.",
                             #"utmcsr":"(direct)|utmccn=(direct)|utmcmd=(none)",
                             #"__gads":"=ID=d3dc5ca0d446d107:T=1524217574:S=ALNI_MbpZii_me-AyJXoThp97Vg5eJpHIw; AMCV_653F60B351E568560A490D4D%40AdobeOrg=1766948455%7CMCMID%7C64157379492117918583861199695401241584%7CMCAID%7CNONE%7CMCAAMLH-1524621134%7C6%7CMCAAMB-1524621134%7Cj8Odv6LonN4r3an7LhD3WZrU1bUpAkFkkiY1ncBR96t2PTI",
                             #"fitracking_12":"no",
                             # "__qca":"P0-88327587-1524016340616; s_fid=78FC1AD688A7D176-2A5AF404FA2C8C06; c_code_2016=DE; U=35824841115ad6a4d867f7f7a4cee3; nlbi_984766=TfMKZQ3te3He+uwEqlAkVQAAAADFe45X8+obTbeWAkWEkh/h; s_cc=true",
                             #"__utmc":"114059806",
                             "incap_ses_534_984766":self.cookies_dict.get('incap_ses_534_984766') ,
                             #"__utma":"114059806.204852835.1524215273.1524215273.1524215273.1",
                             #"__utmt":"1",
                             #"fiutm":"direct|direct||||",
                             #"__utmb":"114059806.1.10.1524215273",
                    },
                    dont_filter=True,
                    headers=self.HEADERS,
                )
        elif self.product_url:
            prod = SiteProductItem()
            prod['url'] = self.product_url
            prod['search_term'] = ''

            yield Request(
                self.product_url,
                meta={
                    'product': prod,
                },
                callback=self._parse_single_product,
                headers={"User-Agent": self.agent},
            )

    def parse_product(self, response):
        product = response.meta['product']
        try:
            props_data = response.xpath('//div[@id="listing-description-details"]')[0].extract()
        except Exception as err:
            props_data = None
        listing_title = product['listing_title']

        try:
            mileage = re.search('<label>\sMileage:</label>\s(.*)<br>', props_data).group(1)
            mileage = re.sub(r'[^\d.]', '', mileage)
        except Exception as err:
            print(err)
            mileage = '0'

        try:
            transmission = re.search('<label>Transmission:</label>\s(.*)<br>', props_data).group(1)
        except Exception as err:
            print(err)
            transmission = ''

        try:
            exterior_color = re.search('<label>Exterior:</label>\s(.*)<br>', props_data).group(1)
        except Exception as err:
            print(err)
            exterior_color = ''

        try:
            interior_color = re.search('<label>Interior:</label>\s(.*)<br>', props_data).group(1)
            if interior_color.lower().find('not specified') > -1:
                interior_color = ''
        except Exception as err:
            print(err)
            interior_color = ''

        try:
            vin_code = re.search('<label>VIN\s#:</label>\s(.*)<br>', props_data).group(1)
        except Exception as err:
            print(err)
            vin_code = ''

        try:
            description = self._clean_text(re.search('Description:\s</b>(.*)</div>', props_data,re.DOTALL).group(1))
        except Exception as err:
            description = ''
        description = description.encode("utf-8")
        seller_type= product['seller_type']
        listing_model_detail = ''
        match = re.match('(\d{0,4})\s{0,5}(\w+)\s{0,4}(\w+)?\s{0,4}(.*)', listing_title)
        listing_date = datetime.datetime.now().date()

        if listing_title.lower().find('scam') > -1 or listing_title.lower().find('wtb') > -1 or listing_title.lower().find('looking') > -1 or \
                        listing_title.lower().find('want to buy') > -1 or listing_title.lower().find('searching') > -1 or listing_title.lower().find('wanted') > -1:
            return

        if (listing_title.lower().find('sold') > -1):
            active = 0
            sold_state = 1
        else:
            active = 1
            sold_state = 0
        try:
            if match is None:
                match = re.match('\d{0,4})\s{0,5}(\w+)\s{0,4}(\w+)?\s{0,4}(.*)', listing_title)
                listing_year, listing_make = match.groups()
                listing_trim = ''
            else:
                listing_year, listing_make, listing_model, listing_trim = match.groups()
                if listing_model is None:
                    listing_model = ''
                listing_model_detail = listing_model + ' ' + listing_trim

        except Exception as err:
            print(err)

        for str in self.extract_pattern:
            #listing_model_detail = self._clean_text(listing_model_detail.lower().replace(str.lower(), ''))
            pattern = re.compile(str + '?(\s|$)', re.IGNORECASE)
            listing_model_detail = self._clean_text(pattern.sub("", listing_model_detail))

        cond = 'Used'
        listing_trim = ''
        cur_time = datetime.datetime.now()
        cur_str = cur_time.strftime('%m-%d-%Y')
        drive = ''

        if vin_code == '':
            vin = self.db.check_vin_by_url(product['url'])
        else:
            vin = self.db.check_vin_by_code(vin_code)

        site = self.db.get_site_id("hemmings")
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
                                self.db.insert_car(site[0], vin_code.upper(), listing_make, listing_model, listing_trim, listing_model_detail, listing_year, mileage, product['city'], product['state'], listing_date, product['price'], cond, seller_type, '', exterior_color, interior_color, transmission, '', listing_title, product.get('url'), '', description,  sold_state, cur_str, '', drive, datetime.datetime.now(), 1, bsf_id, pcf_id, active)
                                with open("out_car_hemmings.csv", "a") as result:
                                    wr = csv.writer(result)
                                    wr.writerow([vin_code.upper(), listing_make, listing_model, listing_trim, listing_model_detail, listing_year, mileage, product['city'], product['state'], listing_date, product['price'], cond, seller_type, '', exterior_color, interior_color, transmission, '', listing_title, product.get('url'), '', description, sold_state, cur_str, '', drive])

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
                        self.db.insert_car(site[0], vin_code.upper(), listing_make, listing_model, listing_trim, listing_model_detail, listing_year, mileage, product['city'], product['state'], listing_date, product['price'], cond, seller_type, '', exterior_color, interior_color, transmission, '', listing_title, product.get('url'), '', description,  sold_state, cur_str, '', drive, datetime.datetime.now(), 1, bsf_data[0], pcf_id, active)
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
                    self.db.insert_car(site[0], vin_code.upper(), listing_make, listing_model, listing_trim, listing_model_detail, listing_year, mileage, product['city'], product['state'], listing_date, product['price'], cond, seller_type, '', exterior_color, interior_color, transmission, '', listing_title, product.get('url'), '', description,  sold_state, cur_str, '', drive, datetime.datetime.now(), 1, None, pcf_id, active)
                    with open("out_car_hemmings.csv", "a") as result:
                        wr = csv.writer(result)
                        wr.writerow([vin_code.upper(), listing_make, listing_model, listing_trim, listing_model_detail, listing_year, mileage, product['city'], product['state'], listing_date, product['price'], cond, seller_type, '', exterior_color, interior_color, transmission, '', listing_title, product.get('url'), '', description, sold_state, cur_str, '', drive])

            else:
                if vin_code == '':
                    row = self.db.update_car_by_url(vin_code.upper(), listing_make, listing_model, listing_trim, listing_model_detail, listing_year, mileage, product['city'], product['state'], listing_date, product['price'], cond, seller_type, '', exterior_color, interior_color, transmission, '', listing_title, product.get('url'), '', description,  0, cur_str, '', drive, 1, site[0], active)
                else:
                    row = self.db.update_car_by_id(vin_code.upper(), listing_make, listing_model, listing_trim, listing_model_detail, listing_year, mileage, product['city'], product['state'], listing_date, product['price'], cond, seller_type, '', exterior_color, interior_color, transmission, '', listing_title, product.get('url'), '', description,  0, cur_str, '', drive, 1, site[0], active, vin)
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

    def _scrape_product_links(self, response):
        products = response.xpath('//div[@id="resultdata"]//div[@class="rs-inner col-md-12 web-result"]')

        search_term = response.meta['search_term']

        for product in products:
            link = product.xpath('a/@href')[0].extract()

            try:
                city_state = product.xpath('div[@class="col-xs-7 col-md-9 result-text"]/h4/text()')[0].extract()
                city_state_match = re.match('(.*),\s(.*)', city_state)
                city, state = city_state_match.groups()

                title = product.xpath('a/h3[@class="rs-headline"]/text()')[0].extract()
                price_str = product.xpath('div/h3[@class="rs-headline class_price"]/text()')[0].extract()
                price = re.sub(r'[^\d.]', '', price_str)

                if price == '':
                    price = 0
                else:
                    price = int(price)

            except Exception as err:
                print(err)
                price = 0

            seller_type_str = self._clean_text(''.join(product.xpath('div[@class="col-xs-7 col-md-9 result-text"]//div[@style="padding-top:5px;"]/text()').extract()))

            if seller_type_str == '':
                if price_str == "Auction":
                    seller_type = 'Auction'
                else:
                    seller_type = 'Dealership'
            else:
                if seller_type_str == 'Private Seller':
                    seller_type = 'Private Party'
                else:
                    seller_type = 'Dealership'
            prod_item = SiteProductItem()

            #print(listing_date)
            prod_item['listing_title'] = title
            prod_item['price'] = price
            prod_item['city'] = city
            prod_item['state'] = state
            prod_item['seller_type'] = seller_type
            prod_item['url'] = self.HOME_URL + link
            req = Request(
                url=self.HOME_URL + link,
                callback=self.parse_product,
                meta={
                    'product': prod_item,
                    'search_term': search_term,
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
        total_matches = self._clean_text(response.xpath('//div[@class="results-count"]/text()')[0].extract())
        total_matches = re.match('(.*)of\s(.*)', total_matches)
        counts, total = total_matches.groups()

        return int(total) if total else 0

    def _scrape_next_results_page_link(self, response):
        st = response.meta['search_term']
        total_matches = self._scrape_total_matches(response)

        if self.current_page * 60 > total_matches:
            return

        self.current_page += 1
        next_page_link = self.NEXT_PAGE_URL.format(search_term=st, start_index = (self.current_page - 1) * 60 + 1)

        return Request(
            url = next_page_link,
            headers=self.HEADERS,
            cookies={
                             #"visid_incap_984766":"L4pKYVELTiGpHf1vVyxGjeO22VoAAAAAQkIPAAAAAACArqGDAdWIXo83eSJ2rHCkeVxVa362DIvv",
                             #"__utmz":"114059806.1524215273.1.1.",
                             #"utmcsr":"(direct)|utmccn=(direct)|utmcmd=(none)",
                             #"__gads":"=ID=d3dc5ca0d446d107:T=1524217574:S=ALNI_MbpZii_me-AyJXoThp97Vg5eJpHIw; AMCV_653F60B351E568560A490D4D%40AdobeOrg=1766948455%7CMCMID%7C64157379492117918583861199695401241584%7CMCAID%7CNONE%7CMCAAMLH-1524621134%7C6%7CMCAAMB-1524621134%7Cj8Odv6LonN4r3an7LhD3WZrU1bUpAkFkkiY1ncBR96t2PTI",
                             #"fitracking_12":"no",
                             # "__qca":"P0-88327587-1524016340616; s_fid=78FC1AD688A7D176-2A5AF404FA2C8C06; c_code_2016=DE; U=35824841115ad6a4d867f7f7a4cee3; nlbi_984766=TfMKZQ3te3He+uwEqlAkVQAAAADFe45X8+obTbeWAkWEkh/h; s_cc=true",
                             #"__utmc":"114059806",
                             "incap_ses_534_984766":self.cookies_dict.get('incap_ses_534_984766') ,
                             #"__utma":"114059806.204852835.1524215273.1524215273.1524215273.1",
                             #"__utmt":"1",
                             #"fiutm":"direct|direct||||",
                             #"__utmb":"114059806.1.10.1524215273",
            },
            meta={
                'search_term': st,
                'remaining': sys.maxint
            },
            dont_filter=True,
        )

    def _clean_text(self, text):
        return re.sub("[\r\n\t]", "", text).strip()
