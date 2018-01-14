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

import csv
import re
import datetime


class CraigslistSpider(BaseProductsSpider):
    handle_httpstatus_list = [404]
    name = "craigslist"
    allowed_domains = ['{search_term}.craigslist.org']

    agent = "iphone_ipad': 'Mozilla/5.0 (iPhone; CPU iPhone OS 7_0_6 like Mac OS X) AppleWebKit/537.51.1 (KHTML, like Gecko) Version/7.0 Mobile/11B651 Safari/9537.53",

    #HOME_URL = "https://www.carmax.com"
    current_page = 1

    SEARCH_URL = 'https://{search_term}.craigslist.org/search/cta?auto_make_model=Porsche'
    URL_STATES = {
        'https://{search_term}.craigslist.org/search/cta?auto_make_model=Porsche', 'CA'
    }
    NEXT_PAGE_URL = 'https://sfbay.craigslist.org/search/cta?s={start_index}&auto_make_model=Porsche'
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
        self.states = {}
        self.state_shortcodes = {}

        with open('city_state.json') as data_file:
            self.city_obj = json.load(data_file)

        for item in self.city_obj:
            self.state_shortcodes[item['shortcode']] = item['state']

        # with open('shortcodes.json') as data_file1:
        #     self.state_obj = json.load(data_file1)
        # self.states = self.loadStates(self.state_obj)

        self.total_matches = None

        self.state = kwargs.get('state')

        url_formatter = FormatterWithDefaults(page_num=1)
        super(CraigslistSpider, self).__init__(url_formatter=url_formatter,
                                             site_name=self.allowed_domains[0],
                                             *args,
                                             **kwargs)

        settings.overrides['DOWNLOAD_DELAY'] = 1




    def loadStates(self, states):
        n_states = {}

        for state in states:
            n_states[state['label']] = state['value']

        return n_states

    def start_requests(self):
        # with open("out_car_craigslist.csv", "a") as result:
        #     wr = csv.writer(result)
        #     wr.writerow(['VIN', 'Listing_Make', 'Listing_Model', 'Listing_Trim', 'Listing_Model_Detail', 'Listing_Year', 'Mileage', 'City', 'State', 'Listing_Date', 'Price', 'Condition', 'Seller_Type', 'VHR_Link', 'Listing_Exterior_Color', 'Listing_Interior_Color', 'Listing_Transmission', 'Listing_Transmission_Detail', 'Listing_Title', 'Listing_URL', 'Listing_Engine_Size', 'Listing_Description', 'Sold_Status', 'Sold_Date', 'Listing_Body_Type', 'Listing_Drivetrain'])

        for request in super(CraigslistSpider, self).start_requests():
            if request.meta.get('search_term'):
                yield request

    def parse_product(self, response):
        product = response.meta['product']
        props_data = response.xpath('//div[@class="mapAndAttrs"]//p[@class="attrgroup"]')
        listing_title = self._clean_text(props_data[0].xpath('//span[@id="titletextonly"]/text()')[0].extract())
        model_content = props_data[0].xpath('span/b/text()')[0].extract()
        basic_props = props_data[1].xpath('span')
        listing_model_detail = ''
        #city = self._clean_text(response.xpath('//span[@class="postingtitletext"]/small/text()')[0].extract())
        description = ''.join(response.xpath('//section[@id="postingbody"]/text()').extract())
	
        #qr_content = response.xpath('//section[@id="postingbody"]/div[@class="print-information print-qrcode-container"]')[0]
        #description = re.sub("<p class='print-qrcode-label'>(.*?)</p>", "", response.xpath('//section[@id="postingbody"]')[0].extract()).strip()
        #description = re.sub("<.*?>", "", description).strip()
        description = re.sub('<div class="print-information print-qrcode-container">(.*)</div>', '', self._clean_text(response.xpath('//section[@id="postingbody"]')[0].extract()))
        #match = re.match('(\d{4})\s{1,5}(\w+)\s{1,4}(\w+)?\s{0,4}(.*)', listing_title)
        match = re.match('(\d{0,4})\s{0,5}(\w+)\s{0,4}(\w+)?\s{0,4}(.*)', model_content)

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
                match = re.match('\d{0,4})\s{0,5}(\w+)\s{0,4}(\w+)?\s{0,4}(.*)', model_content)
                listing_year, listing_make = match.groups()
                listing_trim = ''
            else:
                listing_year, listing_make, listing_model, listing_trim = match.groups()
                if listing_model is None:
                    listing_model = ''
                #listing_trim = listing_model + ' ' + listing_trim

        except Exception as err:
            print(err)

        cur_time = datetime.datetime.now()
        cur_str = cur_time.strftime('%m-%d-%Y')
        vin_code = ''
        cond = ''
        cylinders = ''
        fuel = ''
        mileage = ''
        exterior_color = ''
        title_status = ''
        transmission = ''
        key = ''
        title_status = ''
        drive = ''
        cylinders = ''

        if response.url.find('/ctd/') > -1:
            seller_type = 'Dealership'
        elif response.url.find('/cto/') > -1:
            seller_type = 'Private Party'
        try:
            for basic_prop in basic_props:
                try:
                    key = self._clean_text(basic_prop.xpath('text()')[0].extract())
                    value = self._clean_text(basic_prop.xpath('b/text()')[0].extract())
                except Exception as err:
                    print(err)
                    continue

                if key == 'VIN:':
                    vin_code = value
                elif key =='condition:':
                    if value == 'New':
                        cond = 'New'
                    else:
                        cond = 'Used'
                elif key =='cylinders:':
                    cylinders = value
                elif key =='fuel:':
                    fuel = value
                elif key =='odometer:':
                    mileage = value
                elif key =='paint color:':
                    exterior_color = value
                elif key =='title status:':
                    title_status = value
                elif key =='transmission:':
                    if value[:4].lower() == 'auto':
                        transmission = 'Auto'
                    elif value[:4].lower() == 'manu':
                        transmission = 'Manual'
                elif key =='type:':
                    type = value
                elif key == 'drive:':
                    if value == 'fwd' or value == 'rwd':
                        drive = '2WD'
                    elif value.lower() == '4wd':
                        drive = '4WD'
        except Exception as e:
            print(e)
        if vin_code == '':
            vin = self.db.check_vin_by_url(product['url'])
        else:
            vin = self.db.check_vin_by_code(vin_code)

        site = self.db.get_site_id("craigslist")
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
                    info['model_number'] = result.get('model_number')

                    bsf_data = self.db.check_bsf(vin_code)

                    if bsf_data is None:
                        retry_result = self.db.checkRetryCar(vin_code)

                        if retry_result is None:
                            bsf_data = self.db.getBSinfo(vin_code)
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
                            self.db.insert_car(site[0], vin_code.upper(), listing_make, listing_model, listing_trim, listing_model_detail, listing_year, mileage, product['city'], product['state'], product['listing_date'], product['price'], cond, seller_type, '', exterior_color, '', transmission, '', listing_title, product.get('url'), '', description,  sold_state, cur_str, '', drive, datetime.datetime.now(), datetime.datetime.now(), bsf_id, pcf_id, active)
                    else:
                        bs_option_description = ''
                        options = self.db.get_bsf_options(bsf_data[0])
                        for option in options:
                            bs_option_description = bs_option_description + option[2] + ','

                        info['model_detail'] = bsf_data[5]
                        info['model_year'] = bsf_data[4]
                        info['bs_option_description'] = bs_option_description
                        info['gap_to_msrp'] = int(product['price'] / float(bsf_data[2]) * 100)
                        pcf_id = self.db.insert_parsing_pcf(info)
                        self.db.insert_car(site[0], vin_code.upper(), listing_make, listing_model, listing_trim, listing_model_detail, listing_year, mileage, product['city'], product['state'], product['listing_date'], product['price'], cond, seller_type, '', exterior_color, '', transmission, '', listing_title, product.get('url'), '', description,  sold_state, cur_str, '', drive, datetime.datetime.now(), datetime.datetime.now(), bsf_data[0], pcf_id, active)
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

                    pcf_id = self.db.insert_parsing_pcf(info)

                    self.db.insert_car(site[0], vin_code.upper(), listing_make, listing_model, listing_trim, listing_model_detail, listing_year, mileage, product['city'], product['state'], product['listing_date'], product['price'], cond, seller_type, '', exterior_color, '', transmission, '', listing_title, product.get('url'), '', description,  sold_state, cur_str, '', drive, datetime.datetime.now(), datetime.datetime.now(), None, pcf_id, active)
            else:
                if vin_code == '':
                    row = self.db.update_car_by_url(vin_code.upper(), listing_make, listing_model, listing_trim, listing_model_detail, listing_year, mileage, product['city'], product['state'], product['listing_date'], product['price'], cond, seller_type, '', exterior_color, '', transmission, '', listing_title, product.get('url'), '', description,  0, cur_str, '', drive, datetime.datetime.now(), 3, active)
                else:
                    row = self.db.update_car_by_id(vin_code.upper(), listing_make, listing_model, listing_trim, listing_model_detail, listing_year, mileage, product['city'], product['state'], product['listing_date'], product['price'], cond, seller_type, '', exterior_color, '', transmission, '', listing_title, product.get('url'), '', description,  0, cur_str, '', drive, datetime.datetime.now(), 3, active, vin)
                try:
                    info['pcf_id'] = row[29]
                    d1 = datetime.datetime.strptime(row[10], '%m-%d-%Y')
                    d2 = datetime.datetime.now()

                    listing_age = (d2.date() - d1.date()).days
                    info['listing_age'] = listing_age
                    self.db.update_parsing_pcf(info)
                except Exception as err:
                    pass
        # with open("out_car_craigslist.csv", "a") as result:
        #     wr = csv.writer(result)
        #     #wr.writerow(['VIN', 'Listing_Make', 'Listing_Model', 'Listing_Trim', 'Listing_Model_Detail', 'Listing_Year', 'Mileage', 'City', 'State', 'Listing_Date', 'Price', 'Condition', 'Seller_Type', 'VHR_Link', 'Listing_Color', 'Listing_Interio_Color', 'Listing_Transmission', 'Listing_Transmission_Detail', 'Listing_Title', 'Listing_URL', 'Listing_Engine_Size', 'Listing_Description', 'Sold_Status', 'Sold_Date', 'Listing_Body_Type', 'Drivetrain'])
        #     try:
        #         wr.writerow([vin_code.upper() , listing_make, listing_model, '', listing_model_detail, listing_year, mileage, product['city'], product['state'], product['listing_date'], product['price'], cond, seller_type, '', exterior_color, '', transmission, '', listing_title, response.url, '', description,  '0', '', '', drive])
        #     except Exception as err:
        #         print(err)


    def _scrape_product_links(self, response):
        products = response.xpath('//div[@id="sortable-results"]//ul/li')
        search_term = response.meta['search_term']
        product_shortcode = re.search('https://(.*)\.craigslist', response.url).group(1)
        neighborhoods = {}

        for item in self.city_obj:
            if item['state'] == self.state_shortcodes[product_shortcode]:
                if len(item['subregions']) > 0:
                    for subregion in item['subregions']:
                        if len(subregion['neighborhoods']) > 0:
                            for neighborhood in subregion['neighborhoods']:
                                neighborhoods[neighborhood['name'].lower()] = neighborhood['id']
                        else:
                            neighborhoods[subregion['name'].lower()] = subregion['shortcode']
                else:
                    neighborhoods[item['name'].lower()] = item['shortcode']

        for product in products:
            link = product.xpath('a/@href')[0].extract()

            try:
                listing_date = product.xpath('p[@class="result-info"]/time/@datetime')[0].extract()
                price = product.xpath('p[@class="result-info"]/span/span[@class="result-price"]/text()')[0].extract()
                price = re.search('\$(.*)', price).group(1)
                price = int(price)
            except Exception as err:
                print(err)
                price = 0

            try:
                city = product.xpath('p[@class="result-info"]/span/span[@class="result-hood"]/text()')[0].extract()
                city = re.search('\((.*?)\)', city).group(1)
                if  neighborhoods.get(city.lower()) == None:
                    city = ''
            except Exception as err:
                print(err)
                city = ''

            prod_item = SiteProductItem()
            if listing_date not in (None, ''):
                dt = datetime.datetime.strptime(listing_date, '%Y-%m-%d %H:%M')
                #listing_date = dt.strftime('%m-%d-%Y')

            prod_item['listing_date'] = dt
            #print(listing_date)
            prod_item['price'] = price
            prod_item['city'] = city
            prod_item['state'] = self.state

            req = Request(
                url=link,
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
        total_matches = self._clean_text(response.xpath('//span[@class="totalcount"]/text()')[0].extract())

        return int(total_matches) if total_matches else 0

    def _scrape_next_results_page_link(self, response):
        st = response.meta['search_term']
        total_matches = self._scrape_total_matches(response)

        if self.current_page * 120 > total_matches:
            return

        self.current_page += 1
        next_page_link = self.NEXT_PAGE_URL.format(search_term=st, start_index = (self.current_page - 1) * 120 + 1)

        return Request(
            url = next_page_link,
            headers=self.HEADERS,
            meta={
                'search_term': st,
                'remaining': sys.maxint,
                'state':self.state
            },
            dont_filter=True
        )

    def _clean_text(self, text):
        return re.sub("[\r\n\t]", "", text).strip()
