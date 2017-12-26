__author__ = 'root'

import scrapy
from pfinder.spiders import BaseProductsSpider
from pfinder.spiders import FormatterWithDefaults, cond_set_value
from pfinder.items import SiteProductItem
from pfinder.US_States import STATES
from scrapy.http import Request
from pfinder.pcarfinder import PcarfinderDB
import csv
import re
import datetime

class RennlistSpider(BaseProductsSpider):
    handle_httpstatus_list = [524]

    name = "rennlist"
    allowed_domains = ['rennlist.com']

    SEARCH_URL = 'https://rennlist.com/forums/marketplace/cars/search/f4-{search_term}/f7-min-max/f6-min-max/f10-1/page-{page_num}/'

    def __init__(self, *args, **kwargs):
        self.db = PcarfinderDB()

        self.total_matches = None

        url_formatter = FormatterWithDefaults(page_num=1)
        super(RennlistSpider, self).__init__(url_formatter=url_formatter,
                                             site_name=self.allowed_domains[0],
                                             *args,
                                             **kwargs)
    def start_requests(self):
        # with open("out.csv", "a") as result:
        #     wr = csv.writer(result)
        #     wr.writerow(['Listing_Date', 'Seller_Type', 'Sold_Status', 'Sold_Date', 'Listing_Year', 'Listing_Make', 'Listing_Model', 'Mileage', 'Condition', 'Price', 'Listing_Exterior_Color', 'VIN', 'City', 'State', 'Listing_Body_Type', 'Listing_Transmission', 'Listing_Transmission_Detail', 'Listing_Drivetrain', 'Listing_Model_Detail', 'Listing_URL', 'Listing_Title', 'Listing_Description' ])

        for request in super(RennlistSpider, self).start_requests():
            if request.meta.get('search_term'):
                yield request

    def after_start(self, response):
        pass
    def __parse_sing_product(self, response):
        return self.parse_product(response)
    def parse_product(self, response):
        content = response.xpath('//div[@id="posts"]//div[contains(@id, "post_message")]//p')[0].extract()
        product = response.meta['product']
        product['url'] = response.url
        active = 1
        info = {}
        try:
            year_str = re.search('<strong>Year:</strong>(.*?)<br>', content).group(1)

        except:
            return None

        try:
            make_str = re.search('<strong>Make:</strong>\s(.+?)<br>', content).group(1)
        except:
            return None

        try:
            model_str = re.search('<strong>Model:</strong>\s(.+?)<br>', content).group(1)
            if model_str == '0':
                model_str = ''
        except:
            model_str = ''

        try:
            price_str = re.search('<strong>Price.*?</strong>(.*?)<br>', content).group(1)
            price_str = int(price_str.replace('$', ''))
        except:
            price_str = 0

        try:
            color_str = re.search('<strong>Color:</strong>(.*?)<br>', content).group(1)
        except:
            color_str = ''

        try:
            vin_str = re.search('<strong>VIN:</strong>.*?>(.*?)</a><br>', content).group(1)
        except:
            vin_str = ''

        try:
            location_str = re.search('<strong>Location.*?</strong>(.*?)<br>', content).group(1)
        except:
            location_str = ''

        try:
            style_str = re.search('<strong>Body Style.*?</strong>(.*?)<br>', content).group(1)
        except:
            style_str = ''

        try:
            transmission_detail_str = re.search('<strong>Transmission.*?</strong>(.*?)<br>', content).group(1)
            if transmission_detail_str.strip() == 'Tiptronic' or transmission_detail_str.strip() == 'PDK':
                transmission_str = 'Auto'
            else:
                transmission_str = 'Manual'
        except:
            transmission_detail_str = ''
            transmission_str = ''

        try:
            wheel_str = re.search('<strong>2 or 4.*?</strong>(.*?)<br>', content).group(1)
            if wheel_str.strip() == '2 Wheel Drive':
                wheel_str = '2WD'
            elif wheel_str.strip() == '4 Wheel Drive':
                wheel_str = '4WD'
        except:
            wheel_str = ''

        try:
            engine_str = re.search('<strong>Engine Type.*?</strong>(.*?)<br>', content).group(1)
        except:
            engine_str = ''

        try:
            stereo_str = re.search('<strong>Stereo System.*?</strong>(.*?)<br>', content).group(1)
        except:
            stereo_str = ''

        try:
            cont_str = re.search('<strong>Cont.*?</strong>(.*?)<br>', content).group(1)
        except:
            cont_str = ''
        try:
            options_str = re.search('<strong>Options.*?</strong>(.*?)<br>', content).group(1)
        except:
            options_str = ''

        product = response.meta['product']

        try:
            dealer_ship = re.search('<b>(.*?)</b>', product.get('dealer_ship')).group(1)
            if dealer_ship == 'Dealer Inventory':
                dealer_ship = 'Dealership'
        except:
            dealer_ship = 'Private Party'

        try:
            mileage_str = re.search('<strong>Mileage\s(.+?)</strong>\s(\d+)<br>', content).group(2)
        except:
            mileage_str = ''

        try:
            sold_status = re.search('<strong>(.*?)</strong>', product.get('sold_status')).group(1)
            sold_status = 1
            cur_time = datetime.datetime.now()
            cur_str = ("%s-%s-%s" % (cur_time.month, cur_time.day, cur_time.year))
            active = 0
        except:
            sold_status = 0
            cur_time = datetime.datetime.now()
            cur_str = ("%s-%s-%s" % (cur_time.month, cur_time.day, cur_time.year))

        if int(year_str)  == cur_time.year - 1 or int(year_str)  == cur_time.year:
            condition = 'New'
        else:
            condition = 'Used'

        city_content = response.xpath('//div[@id="posts"]//div[contains(@id, "post")]//div[@class="tcell alt2"]')[0].extract()

        try:
            location = re.search('<div>Location:\s(.*?)</div>', city_content).group(1)

            try:
                city = location.split(',')[0].strip()
            except:
                city = ''

            try:
                state = location.split(',')[1].strip()
            except:
                state = ''

            if len(city) == 2:
                state = city
                city = ''
            state = ''.join([i for i in state if not i.isdigit()])
            if STATES.get(state.lower()) is not None:
                state = STATES[state.lower()]
        except:
            city = ''
            state = ''

        try:
             description = response.xpath('//div[@id="posts"]//div[contains(@id, "post_message")]')[0].extract()
             description = re.search('</p>(.*?)</div>', description, re.DOTALL).group(1)
             description = re.sub('<.*?>', '', description)
             description = description.replace("'", "\'")
        except:
            description = ''
        try:
            date_content = response.xpath('//div[@id="posts"]//div[contains(@id, "post")]//div[@class="trow thead smallfont"]/div[@class="tcell"]')[0].extract()
            posted_date = re.search('</a>\r\n\t\t(.*)\r\n\t\t', date_content).group(1)
            date = posted_date.split(',')
            posted_date = date[0]

            if date[0] == 'Today':
                today = datetime.datetime.now()
                date[0] = today.strftime('%m-%d-%Y')
                posted_date = date[0]
            elif date[0] == 'Yesterday':
                yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
                date[0] = yesterday.strftime('%m-%d-%Y')
                posted_date = date[0]
        except:
            posted_date = ''
        try:
            title = response.xpath('//div[@class="row sticky-container"]//h1')[0].extract()
            title = re.search('>\s(.*?)</h1>', title).group(1)

            lw_title = title.lower()
            if (lw_title.find('wtb') > -1) or (lw_title.find('want to buy') > -1) or (lw_title.find('looking') > -1) or (lw_title.find('searching') > -1) or (lw_title.find('wanted') > -1) or (lw_title.find('sold') > -1):
                return
        except:
            title = ''

        if vin_str == '':
            vin = self.db.check_vin_by_url(product['url'])
        else:
            vin = self.db.check_vin_by_code(vin_str)

        site = self.db.get_site_id("rennlist")

        info = {}
        if site is not None:
            if  not vin:
                if vin_str != '' and int(year_str) >= 2001:

                    info['Vin'] = vin_str
                    info['Year'] = year_str
                    info['Make'] = make_str
                    info['Model'] = model_str
                    info['Mileage'] = mileage_str
                    info['Price'] = price_str
                    info['Transmission'] = transmission_str
                    info['DriveTrain'] = wheel_str
                    info['Description'] = description
                    info['listing_model_detail'] = model_str
                    info['listing_transmission'] = transmission_str
                    info['listing_color'] = color_str
                    info['listing_description'] = description
                    result = self.db.parsing_vin(vin_str.upper())
                    info['model_number'] = result['model_number']

                    bsf_data = self.db.check_bsf(vin_str)

                    if bsf_data is None:
                        retry_result = self.db.checkRetryCar(vin_str)

                        if retry_result is None:
                            bsf_data = self.db.getBSinfo(vin_str)
                            bsf_id = self.db.insert_bsf(vin_str, bsf_data['msrp'], bsf_data['warranty_start'], bsf_data['model_year'], bsf_data['model_detail'], bsf_data['color'], datetime.datetime.strptime(bsf_data['production_month'], '%m/%Y'), bsf_data['interior'])
                            bs_option_description = ''

                            for option in bsf_data['options']:
                                self.db.insert_bsf_options(bsf_id, option['code'], option['value'])
                                bs_option_description = bs_option_description + option['value'] + ','

                            info['model_detail'] = bsf_data['model_detail']
                            info['model_year'] = bsf_data['model_year']
                            info['bs_option_description'] = bs_option_description
                            info['gap_to_msrp'] = int(price_str / float(bsf_data['msrp']) * 100)
                            pcf_id = self.db.insert_parsing_pcf(info)
                            self.db.insert_car(site[0], vin_str.upper(), make_str, model_str, '', cont_str, year_str, mileage_str, city, state, posted_date, price_str, condition, dealer_ship, '', color_str, '', transmission_str, '', title, product.get('url'), '', description,  sold_status, cur_time, '', wheel_str, datetime.datetime.now(), datetime.datetime.now(), bsf_id, pcf_id, active)
                    else:
                        bs_option_description = ''
                        options = self.db.get_bsf_options(bsf_data[0])
                        for option in options:
                            bs_option_description = bs_option_description + option[2] + ','

                        info['model_detail'] = bsf_data[5]
                        info['model_year'] = bsf_data[4]
                        info['bs_option_description'] = bs_option_description
                        info['gap_to_msrp'] = int(price_str / float(bsf_data[2]) * 100)
                        pcf_id = self.db.insert_parsing_pcf(info)
                        self.db.insert_car(site[0], vin_str.upper(), make_str, model_str, '', cont_str, year_str, mileage_str, city, state, posted_date, price_str, condition, dealer_ship, '', color_str, '', transmission_str, '', title, product.get('url'), '', description,  sold_status, cur_time, '', wheel_str, datetime.datetime.now(), datetime.datetime.now(), bsf_data[0], pcf_id, active)
                else:
                    result = self.db.parsing_vin(vin_str.upper())

                    info['Vin'] = vin_str
                    info['Year'] = year_str
                    info['Make'] = make_str
                    info['Model'] = model_str
                    info['Mileage'] = mileage_str
                    info['Price'] = price_str
                    info['Transmission'] = transmission_str
                    info['DriveTrain'] = wheel_str
                    info['Description'] = description

                    info['model_detail'] = ''
                    try:
                        info['model_number'] = result['model_number']
                    except Exception as e:
                        info['model_number'] = ''
                    info['model_year'] = ''
                    info['listing_model_detail'] = model_str
                    info['listing_transmission'] = transmission_str
                    info['bs_option_description'] = ''
                    info['listing_color'] = color_str
                    info['listing_description'] = description
                    info['gap_to_msrp'] = 0

                    pcf_id = self.db.insert_parsing_pcf(info)

                    self.db.insert_car(site[0], vin_str.upper(), make_str, model_str, '', cont_str, year_str, mileage_str, city, state, posted_date, price_str, condition, dealer_ship, '', color_str, '', transmission_str, '', title, product.get('url'), '', description,  sold_status, cur_time, '', wheel_str, datetime.datetime.now(), datetime.datetime.now(), None, pcf_id, active)
            else:
            #if vin[30] == 2:
                    if vin_str == '':
                        row = self.db.update_car_by_url(vin_str.upper(), make_str, model_str, '', '', year_str, mileage_str, city, state, posted_date, price_str, condition, dealer_ship, '', color_str, '', transmission_str, '', title, product.get('url'), '', description,  sold_status, cur_time, '', wheel_str, datetime.datetime.now(), 2, active)
                    else:
                        row = self.db.update_car_by_id(vin_str.upper(), make_str, model_str, '', '', year_str, mileage_str, city, state, posted_date, price_str, condition, dealer_ship, '', color_str, '', transmission_str, '', title, product.get('url'), '', description,  sold_status, cur_time, '', wheel_str, datetime.datetime.now(), 2, active, vin)
                    if row is not None:
                        info['pcf_id'] = row[29]
                        d1 = datetime.datetime.strptime(row[10], '%m-%d-%Y')
                        d2 = datetime.datetime.now()

                        listing_age = (d2.date() - d1.date()).days
                        info['listing_age'] = listing_age
                        self.db.update_parsing_pcf(info)
            #else:
            #    self.db.insert_car(site[0], vin_str.upper(), make_str, model_str, '', cont_str, year_str, mileage_str, city, state, posted_date, price_str, condition, dealer_ship, '', color_str, '', transmission_str, '', title, product.get('url'), '', description,  sold_status, cur_time, '', wheel_str, datetime.datetime.now(), datetime.datetime.now(), vin[33], vin[29], active)

        #with open("out.csv", "a") as result:
            #wr = csv.writer(result)
            #wr.writerow(['Year', 'Make', 'Model', 'Mileage', 'Price', 'Color', 'VIN', 'Location' 'Style', 'Transmission', 'Wheel', 'Engine', 'Stereo', 'Cont', 'Option'])
            #wr.writerow([posted_date, dealer_ship, sold_status, cur_str, year_str, make_str, model_str, mileage_str, condition, price_str, color_str, vin_str.upper(), city, state, style_str, transmission_str, transmission_detail_str, wheel_str, cont_str, product.get('url'), title, description])
        return product

    def _scrape_product_links(self, response):
        products_container = response.xpath('//div[@id="threadslist"]//div[@class="trow text-center"]//div[@class="tcell alt1 text-left"]')
        products_link = response.xpath('//div[@id="threadslist"]//div[@class="trow text-center"]//div[@class="tcell alt1 text-left"]//a[contains(@id, "title")]/@href').extract()
        for product in products_container:
            dealer_ship = product.xpath('.//span[@style="color:blue"]/b').extract()
            link = product.xpath('.//a[contains(@id, "title")]/@href').extract()
            sold_status = product.xpath('.//  span[@class="highlight alert"]/strong').extract()
            product_item = SiteProductItem()

            cond_set_value(product_item, 'url', 'https://rennlist.com/forums/' + link[0])

            try:
                cond_set_value(product_item, 'dealer_ship', dealer_ship[0])
            except:
                cond_set_value(product_item, 'dealer_ship', '')

            try:
                cond_set_value(product_item, 'sold_status', sold_status[0])
            except:
                cond_set_value(product_item, 'sold_status', '')
            yield 'https://rennlist.com/forums/' + link[0], product_item

    def _scrape_total_matches(self, response):
        return None

    def _scrape_results_per_page(self, response):
        products_link = response.xpath('//div[@id="threadslist"]//div[@class="trow text-center"]//div[@class="tcell alt1 text-break text-left"]//a[contains(@id, "title")]/@href').extract()
        return products_link

    def _scrape_next_results_page_link(self, response):
        meta = response.meta
        current_page = meta.get('current_page')
        try:
            max_pages = re.search('<div class="tcell vbmenu_control">Page\s(.*?)\sof\s(.*?)</div>', response.body).group(2)
            max_pages = int(max_pages)
        except:
            max_pages = 0
        if not current_page:
            current_page = 1
        if current_page > max_pages:
            return
        current_page += 1
        st = meta.get('search_term')
        meta['current_page'] = current_page
        next_url = self.SEARCH_URL.format(search_term=st, page_num=current_page)
        return Request(url=next_url, meta = meta)