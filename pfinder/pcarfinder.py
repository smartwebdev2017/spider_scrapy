__author__ = 'root'
import mysql.connector
from bs4 import BeautifulSoup
import requests, random
import re
import datetime

class PcarfinderDB():
    def __init__(self):
        self.conn = mysql.connector.connect(user='root', password='root', db='test1', host='localhost', charset='utf8', use_unicode=True)
        self.cursor = self.conn.cursor(buffered=True)
    def check_vin_by_code(self, vin_code):
        sql = "select * from api_car where vin_code = '%s' "%(vin_code)
        #sql = "select * from api_car where site_id=2"
        self.cursor.execute(sql)
        vin = self.cursor.fetchall()
        return vin

    def check_vin_by_url(self, url):
        sql = "select * from api_car where listing_url = '%s' "%(url)
        self.cursor.execute(sql)
        vin = self.cursor.fetchone()
        return vin

    def get_site_id(self, name):
        sql = "select * from api_site where site_name = '%s' " %(name)
        self.cursor.execute(sql)
        site = self.cursor.fetchone()
        return site

    def update_site_status(self, site_id):
        sql = "UPDATE api_site SET updated = NOW() WHERE id = %s" % (site_id)
        self.cursor.execute(sql)
        site = self.cursor.fetchone()
        return site

    def insert_state(self, state_name):
        sql = "SELECT * FROM api_state WHERE state_name = '%s' " %(state_name)
        self.cursor.execute(sql)
        state = self.cursor.fetchone()
        if state is None:

            sql = "INSERT INTO api_state (state_name) values ('%s') " % (state_name)

            try:
                self.cursor.execute(sql)
                self.conn.commit()
                print('%s is added successfully' %(state_name))
                id = self.cursor.lastrowid
                return id
            except Exception as e:
                print(e)
                self.conn.rollback()

    def insert_city(self, city_name):
        sql = "SELECT * FROM api_city WHERE city_name = '%s' " %(city_name)
        self.cursor.execute(sql)
        city = self.cursor.fetchone()
        if city is None:

            sql = "INSERT INTO api_city (city_name) values ('%s') " % (city_name)

            try:
                self.cursor.execute(sql)
                self.conn.commit()
                print('%s is added successfully' %(city_name))
                id = self.cursor.lastrowid
                return id
            except Exception as e:
                print(e)
                self.conn.rollback()

    def insert_car(self, site, vin, listing_make, listing_model, listing_trim, listing_model_detail, listing_year, mileage, city, state, listing_date,
                   price, cond, seller_type, vhr_link, listing_exterior_color, listing_interior_color, listing_transmission, listing_transmission_detail,
                   listing_title, listing_url, listing_engine_size, listing_description, sold_state, sold_date, listing_body_type, listing_drivetrain, created, updated, bsf_id, pcf_id, active):

        sql = "INSERT INTO api_car (site_id, vin_code, listing_make, listing_model, listing_trim, listing_model_detail, listing_year, mileage, city, state, " \
                      "listing_date, price, cond, seller_type, vhr_link, listing_exterior_color, listing_interior_color, listing_transmission, listing_transmission_detail, " \
                      "listing_title, listing_url, listing_engine_size, listing_description, sold_state, sold_date, listing_body_type, listing_drivetrain, created, updated, " \
                      "pcf_id, vdf_id, vhf_id, vin_id, active )" \
                      "values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
        try:
            self.cursor.execute(sql, (site, vin, listing_make, listing_model, listing_trim, listing_model_detail, listing_year, mileage, city, state, listing_date, price, cond, seller_type, vhr_link,
                       listing_exterior_color, listing_interior_color, listing_transmission, listing_transmission_detail, listing_title, listing_url, listing_engine_size, listing_description,  sold_state,
                       sold_date, listing_body_type, listing_drivetrain, created, updated, pcf_id, None,None,bsf_id, active))
            self.conn.commit()
            print("%s is added successfully" % vin)
        except Exception as e:
            print(e)
            self.conn.rollback()

    def update_car_by_id(self, vin_code, listing_make, listing_model, listing_trim, listing_model_detail, listing_year, mileage, city, state, listing_date,
                   price, cond, seller_type, vhr_link, listing_exterior_color, listing_interior_color, listing_transmission, listing_transmission_detail,
                   listing_title, listing_url, listing_engine_size, listing_description, sold_state, sold_date, listing_body_type, listing_drivetrain, updated, site_id, active, vin_data):

        try:
            bSameListing = False
            for item in vin_data:
                if item[20] == listing_url:
                    bSameListing = True

            if ( bSameListing == False):
                sql = "INSERT INTO api_car (site_id, vin_code, listing_make, listing_model, listing_trim, listing_model_detail, listing_year, mileage, city, state, " \
                      "listing_date, price, cond, seller_type, vhr_link, listing_exterior_color, listing_interior_color, listing_transmission, listing_transmission_detail, " \
                      "listing_title, listing_url, listing_engine_size, listing_description, sold_state, sold_date, listing_body_type, listing_drivetrain, created, updated, " \
                      "pcf_id, vdf_id, vhf_id, vin_id, active )" \
                      "values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
                self.cursor.execute(sql, (site_id, vin_code, listing_make, listing_model, listing_trim, listing_model_detail, listing_year, mileage, city, state, listing_date, price, cond, seller_type, vhr_link,
                       listing_exterior_color, listing_interior_color, listing_transmission, listing_transmission_detail, listing_title, listing_url, listing_engine_size, listing_description,  sold_state,
                       sold_date, listing_body_type, listing_drivetrain, datetime.datetime.now(), updated, vin_data[0][29], None,None,vin_data[0][33], active))
                msg = "%s is added successfully" % vin_code
            else:
                sql = "UPDATE api_car SET listing_make = %s, listing_model = %s, listing_trim = %s, listing_model_detail = %s, listing_year = %s, mileage = %s, city = %s, state = %s, " \
                              "price = %s, cond = %s, seller_type = %s, vhr_link = %s, listing_exterior_color = %s, listing_interior_color = %s, listing_transmission = %s, listing_transmission_detail = %s, " \
                              "listing_title = %s, listing_engine_size = %s, listing_description = %s, sold_state = %s, sold_date = %s, listing_body_type = %s, listing_drivetrain = %s, updated = %s, active = %s " \
                              "WHERE site_id = %s and sold_state = 0 and vin_code = %s and listing_url = %s"

                self.cursor.execute(sql, (listing_make, listing_model, listing_trim, listing_model_detail, listing_year, mileage, city, state, price, cond, seller_type, vhr_link,
                                              listing_exterior_color, listing_interior_color, listing_transmission, listing_transmission_detail, listing_title, listing_engine_size,
                                              listing_description,  sold_state, sold_date, listing_body_type, listing_drivetrain, updated, active, site_id, vin_code, listing_url))
                msg = "%s is updated successfully" % vin_code
            self.conn.commit()
            print(msg)
            sql = "SELECT * FROM api_car WHERE vin_code ='%s' " % (vin_code)
            self.cursor.execute(sql)
            result = self.cursor.fetchone()
            return result
        except Exception as e:
            print(e)
            self.conn.rollback()
    def update_car_by_url(self, vin, listing_make, listing_model, listing_trim, listing_model_detail, listing_year, mileage, city, state, listing_date,
                   price, cond, seller_type, vhr_link, listing_exterior_color, listing_interior_color, listing_transmission, listing_transmission_detail,
                   listing_title, listing_url, listing_engine_size, listing_description, sold_state, sold_date, listing_body_type, listing_drivetrain, updated, site_id, active):
        sql = "UPDATE api_car SET listing_make = %s, listing_model = %s, listing_trim = %s, listing_model_detail = %s, listing_year = %s, mileage = %s, city = %s, state = %s, " \
                      "price = %s, cond = %s, seller_type = %s, vhr_link = %s, listing_exterior_color = %s, listing_interior_color = %s, listing_transmission = %s, listing_transmission_detail = %s, " \
                      "listing_title = %s, listing_engine_size = %s, listing_description = %s, sold_state = %s, sold_date = %s, listing_body_type = %s, listing_drivetrain = %s, updated = %s, active = %s " \
                      "WHERE site_id = %s and sold_state = 0 and vin_code = %s and listing_url = %s "
        try:
            self.cursor.execute(sql, (listing_make, listing_model, listing_trim, listing_model_detail, listing_year, mileage, city, state, price, cond, seller_type, vhr_link,
                                          listing_exterior_color, listing_interior_color, listing_transmission, listing_transmission_detail, listing_title, listing_engine_size,
                                          listing_description,  sold_state, sold_date, listing_body_type, listing_drivetrain, updated, active, site_id, vin, listing_url))
            self.conn.commit()
            print("%s is updated successfully" % vin)
            sql = "SELECT * FROM api_car WHERE listing_url =%s "
            self.cursor.execute(sql, (listing_url,))
            result = self.cursor.fetchone()
            return result
        except Exception as e:
            print(e)
            self.conn.rollback()

    def update_carmax_sold_status(self):
        sql = "select * from api_car  where site_id = 1 and sold_state = 0 and DATE(updated) <= (NOW() - INTERVAL 1 DAY) "
        self.cursor.execute(sql)
        results = self.cursor.fetchall()
        for result in results:
            sql = "UPDATE api_car SET active = 0, sold_state = %s, sold_date = '%s' WHERE id = %s " %(1, datetime.datetime.now(), result[0])
            try:
                self.cursor.execute(sql)
                self.conn.commit()
                print("%s is updated successfully" % result[1])
            except Exception as e:
                print(e)

    def update_craigslist_sold_status(self):
        sql = "select * from api_car  where site_id = 3 and sold_state = 0 and DATE(updated) <= (NOW() - INTERVAL 1 DAY) "
        self.cursor.execute(sql)
        results = self.cursor.fetchall()
        for result in results:
            sql = "UPDATE api_car SET active = 0, sold_state = %s, sold_date = '%s' WHERE id = %s " %(1, datetime.datetime.now(), result[0])
            try:
                self.cursor.execute(sql)
                self.conn.commit()
                print("%s is updated successfully" % result[1])
            except Exception as e:
                print(e)

    def insert_temp_data(self, vin_id, code, value):
        sql = "INSERT INTO temp (vin_id, code, value) values (%s, '%s', '%s') " % (vin_id, code, value)

        try:
            self.cursor.execute(sql)
            self.conn.commit()
            print('%s is added successfully' %(vin_id))
        except Exception as e:
            print(e)
            self.conn.rollback()
    def check_bsf(self, vin_code):
        sql = "SELECT * FROM api_bsf WHERE vin = %s"
        self.cursor.execute(sql, (vin_code,))
        vin = self.cursor.fetchone()

        return vin

    def insert_bsf(self, vin_id, msrp, warranty_start, model_year, model_detail, color, production_month, interior):
        sql = "SELECT id FROM api_bsf where vin='%s' " % (vin_id)
        self.cursor.execute(sql)
        vin = self.cursor.fetchone()
        if vin is not None:
            return vin[0]

        sql = "INSERT INTO api_bsf (vin, msrp, warranty_start, model_year, model_detail, color, production_month, interior) " \
              " values ('%s', %s, '%s', %s, '%s', '%s', '%s', '%s') " % (vin_id, msrp, warranty_start, model_year, model_detail, color, production_month, interior)

        try:
            self.cursor.execute(sql)
            self.conn.commit()
            print('%s is added successfully' %(vin_id))
            id = self.cursor.lastrowid
            return id
        except Exception as e:
            print(e)
            self.conn.rollback()

    def insert_bsf_options(self, bsf_id, code, value):
        sql = "INSERT INTO api_bsf_options (bsf_id, code, value) values (%s, '%s', '%s') " % (bsf_id, code, value)

        try:
            self.cursor.execute(sql)
            self.conn.commit()
            print('%s is added successfully' %(bsf_id))
        except Exception as e:
            print(e)
            self.conn.rollback()
    def get_bsf_options(self, bsf_id):
        sql = "SELECT * FROM api_bsf_options WHERE bsf_id = %s"
        self.cursor.execute(sql, (bsf_id,))
        options = self.cursor.fetchall()
        return options

    def updateBsfById(self, id, warranty_start, production_month, color, interior):
        sql = "UPDATE api_bsf SET warranty_start = '%s', production_month = '%s', color = '%s', interior='%s' WHERE id = %s " % (warranty_start, production_month, color, interior, id)

        try:
            self.cursor.execute(sql)
            self.conn.commit()
            print("%s is updated successfully" % id)
        except Exception as e:
            print(e)
            self.conn.rollback()

    def getOptionsByBsfId(self, bsf_id):
        sql = "SELECT * FROM temp WHERE vin_id = '%s' " % (bsf_id)
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        return result
    def insertRetryCar(self, vin):
        sql = "INSERT INTO api_retrycar (vin_code) values (%s)"
        try:
            self.cursor.execute(sql, (vin, ))
            self.conn.commit()
            print('%s is added into RetryCar successfully' % (vin))
        except Exception as e:
            print(e)
            self.conn.rollback()
    def checkRetryCar(self, vin):
        sql = "SELECT * FROM api_retrycar WHERE vin_code = '%s' " % (vin)
        self.cursor.execute(sql)
        result = self.cursor.fetchone()
        return result

    def getBSinfo(self, vin):
        data = {}
        url = 'https://admin.porschedealer.com/reports/build_sheets/print.php?vin=%s'

        res = requests.get(url % vin)

        bs = BeautifulSoup(res.content, 'html.parser')
        try:
            title = bs.find('h1').text
        except Exception as e:
            title = ''
            self.insertRetryCar(vin)
        try:
            model_year = re.search('(\d{4}\s)(.*?\s)(.*?$)', title).group(1)
            model = re.search('(\d{4}\s)(.*?\s)(.*?$)', title).group(2)
            model_detail =  model + re.search('(\d{4}\s)(.*?\s)(.*?$)', title).group(3)

            data['model_year'] = model_year
            data['model'] = model
            data['model_detail'] = model_detail
            data['vin'] = vin


        except Exception as e:
            print('Parsing Error in regular expressions')

        vehicle = bs.find('div', {'class':'vehicle'})
        vehicle_labels = vehicle.findAll('div', {'class':'label'})
        vehicle_values = vehicle.findAll('div', {'class':'value'})

        print('Vehicle')
        data['production_month'] = ''
        data['msrp'] = 0
        data['color'] = ''
        data['interior'] = ''
        data['warranty_start'] = ''

        for i in range(0, len(vehicle_labels)):
            if vehicle_labels[i].text == 'Division:':
                pass
            elif vehicle_labels[i].text == 'Commission #:':
                pass
            elif vehicle_labels[i].text == 'Prod Month:':
                data['production_month'] = vehicle_values[i].text
            elif vehicle_labels[i].text == 'Price:':
                data['msrp'] = vehicle_values[i].text.replace("$", "").replace(",","")
            elif vehicle_labels[i].text == 'Exterior:':
                data['color'] = vehicle_values[i].text
            elif vehicle_labels[i].text == 'Interior:':
                data['interior'] = vehicle_values[i].text
            elif vehicle_labels[i].text == 'Warranty Start:':
                data['warranty_start'] = vehicle_values[i].text

            print('%s, %s' %(vehicle_labels[i].text, vehicle_values[i].text))

        options = bs.find('div', {'class':'options'})
        options_labels = options.findAll('div', {'class':'label'})
        options_values = options.findAll('div', {'class':'value'})


        data['options'] = []
        for i in range(0, len(options_labels)):
            option = {}
            option['code'] = options_labels[i].text
            option['value'] = options_values[i].text
            data['options'].append(option)
            print(option)

        print(data)
        return data
    def get_modelnumber(self, listing_year, model_str):
        listing_model_detail = model_str.lower()
        model_number = ''

        try:
            year = int(listing_year)

            if year >= 1964 and year <= 1989 and listing_model_detail.find('911') > -1:
                model_number = '911'

            if year >= 1976 and year <= 1988 and listing_model_detail.find('924') > -1:
                model_number = '924'

            if year >= 1977 and year <= 1995 and listing_model_detail.find('928') > -1:
                model_number = '928'

            if year >= 1975 and year <= 1989 and (listing_model_detail.find('930') > -1 or (listing_model_detail.find('911') > -1 and listing_model_detail.find('turbo') > -1)):
                model_number = '930'

            if year >= 1979 and year <= 1983 and listing_model_detail.find('924') > -1 and listing_model_detail.find('turbo') > -1:
                model_number = '931'

            if year >= 1982 and year <= 1991 and listing_model_detail.find('944') > -1:
                model_number = '944'

            if year >= 1985 and year <= 1991 and (listing_model_detail.find('951') > -1 or (listing_model_detail.find('944') > -1 and listing_model_detail.find('turbo') > -1)):
                model_number = '951'

            if year >= 2014 and listing_model_detail.find('macan') > -1:
                model_number = '95B'

            if year >= 1989 and year <= 1994 and (listing_model_detail.find('911') > -1 or listing_model_detail.find('964') > -1):
                model_number = '964'

            if year >= 1992 and year <= 1995 and listing_model_detail.find('968') > -1:
                model_number = '968'

            if year >= 2009 and year <= 2013 and listing_model_detail.find('panamera') > -1:
                model_number = '970.1'

            if year >= 2014 and year <= 2016 and listing_model_detail.find('panamera') > -1:
                model_number = '970.2'

            if year >= 2017 and year <= 2023 and listing_model_detail.find('panamera') > -1:
                model_number = '971'

            if year >= 2003 and year <= 2007 and listing_model_detail.find('carrera gt') > -1:
                model_number = '980'

            if year >= 2013 and year <= 2016 and (listing_model_detail.find('cayman') > -1 or listing_model_detail.find('boxster') > -1):
                model_number = '981'

            if year >= 2017 and year <= 2019 and (listing_model_detail.find('cayman') > -1 or listing_model_detail.find('boxster') > -1):
                model_number = '982'

            if year >= 1997 and year <= 2004 and listing_model_detail.find('boxster') > -1:
                model_number = '986'

            if year >= 2005 and year <= 2008 and (listing_model_detail.find('cayman') > -1 or listing_model_detail.find('boxster') > -1):
                model_number = '987.1'

            if year >= 2009 and year <= 2012 and (listing_model_detail.find('cayman') > -1 or listing_model_detail.find('boxster') > -1):
                model_number = '987.2'

            if year >= 2014 and year <= 2016 and (listing_model_detail.find('911') > -1 or listing_model_detail.find('carrera') > -1):
                model_number = '991.1'

            if year >= 2017 and year <= 2018 and (listing_model_detail.find('911') > -1 or listing_model_detail.find('carrera') > -1):
                model_number = '991.2'

            if year >= 1993 and year <= 1996 and (listing_model_detail.find('911') > -1 or listing_model_detail.find('993') > -1):
                model_number = '993'

            if year >= 1998 and year <= 2003 and (listing_model_detail.find('911') > -1 or listing_model_detail.find('996') > -1):
                model_number = '996'

            if year >= 2005 and year <= 2008 and (listing_model_detail.find('911') > -1 or listing_model_detail.find('997') > -1):
                model_number = '997.1'

            if year >= 2009 and year <= 2012 and (listing_model_detail.find('911') > -1 or listing_model_detail.find('997') > -1):
                model_number = '997.2'

            if year >= 2003 and year <= 2007 and listing_model_detail.find('cayenne') > -1:
                model_number = '955'

            if year >= 2010 and year <= 2013 and listing_model_detail.find('cayenne') > -1:
                model_number = '958.1'

            if year >= 2015 and year <= 2017 and listing_model_detail.find('cayenne') > -1:
                model_number = '958.2'

        except Exception as e:
            year = 0
            model_number = ''

        return model_number

    def parsing_vin(self, vin, year, model_str):
        model_number = ''
        CONST_MODEL_NUMBERS = ['911', '924', '928', '930', '931', '944', '951', '95B', '964', '968', '970.1', '970.2', '971', '980','981', '982', '986', '987.1', '987.2', '991.1', '991.2', '993', '996', '997.1', '997.2', '955', '958.1', '958.2']

        if (len(vin) == 0):
            model_number = self.get_modelnumber(year, model_str)
        elif len(vin) < 17 and len(vin) > 0:
            return
        else:

            model_number = ''
            model_detail = ''
            year = 0

            if (vin[3] == 'Z') and (vin[4] == 'Z') and (vin[5] == 'Z') : # RoW car
                model_number = vin[6] + vin[7] + vin[11]

                if model_number == '911': model_detail = '911 G-model'
                if model_number == '924': model_detail = '924'
                if model_number == '928': model_detail = '928'
                if model_number == '930': model_detail = '930 G-model Turbo'
                if model_number == '931': model_detail = '924 Turbo'
                if model_number == '937': model_detail = '924 Carrera GT'
                if model_number == '944': model_detail = '944'
                if model_number == '951': model_detail = '944 Turbo'
                if model_number == '95B': model_detail = 'Macan'
                if model_number == '964': model_detail = '911 1989-1994'
                if model_number == '968': model_detail = '968'
                if model_number == '970':
                    if vin[9] == '9':
                        model_number = '970.1'
                        model_detail = 'Panamera 2009-2016'
                    elif vin[9] == 'A':
                        model_number = '970.1'
                        model_detail = 'Panamera 2009-2016'
                    elif vin[9] == 'B':
                        model_number = '970.1'
                        model_detail = 'Panamera 2009-2016'
                    elif vin[9] == 'C':
                        model_number = '970.1'
                        model_detail = 'Panamera 2009-2016'
                    elif vin[9] == 'D':
                        model_number = '970.1'
                        model_detail = 'Panamera 2009-2016'
                    elif vin[9] == 'E':
                        model_number = '970.2'
                        model_detail = 'Panamera 2009-2016'
                    elif vin[9] == 'F':
                        model_number = '970.2'
                        model_detail = 'Panamera 2009-2016'
                    elif vin[9] == 'G':
                        model_number = '970.2'
                        model_detail = 'Panamera 2009-2016'

                if model_number == '971': model_detail = 'Panamera 2016-2023'
                if model_number == '980': model_detail = 'Carrera GT'
                if model_number == '981': model_detail = 'Boxster/Cayman 2012-2016'
                if model_number == '982': model_detail = '718 Boxster/Cayman 2016-2019'
                if model_number == '986': model_detail = 'Boxster 1996-2004'
                if model_number == '987':
                    if vin[9] == '5':
                        model_number = '987.1'
                        model_detail = '987 (Boxster/Cayman 2005)'
                    elif vin[9] == '6':
                        model_number = '987.1'
                        model_detail = '987 (Boxster/Cayman 2006)'
                    elif vin[9] == '7':
                        model_number = '987.1'
                        model_detail = '987 (Boxster/Cayman 2007)'
                    elif vin[9] == '8':
                        model_number = '987.1'
                        model_detail = '987 (Boxster/Cayman 2008)'
                    elif vin[9] == '9':
                        model_number = '987.2'
                        model_detail = '987 (Boxster/Cayman 2009)'
                    elif vin[9] == 'A':
                        model_number = '987.2'
                        model_detail = '987 (Boxster/Cayman 2010)'
                    elif vin[9] == 'B':
                        model_number = '987.2'
                        model_detail = '987 (Boxster/Cayman 2011)'
                    elif vin[9] == 'C':
                        model_number = '987.2'
                        model_detail = '987 (Boxster/Cayman 2012)'
                if model_number == '991':
                    if vin[9] == 'C':
                        model_number = '991.1'
                        model_detail = '911 2012'
                    elif vin[9] == 'D':
                        model_number = '991.1'
                        model_detail = '911 2013'
                    elif vin[9] == 'E':
                        model_number = '991.1'
                        model_detail = '911 2014'
                    elif vin[9] == 'F':
                        model_number = '991.1'
                        model_detail = '911 2015'
                    elif vin[9] == 'G':
                        model_number = '991.1'
                        model_detail = '911 2016'
                    elif vin[9] == 'H':
                        model_number = '991.2'
                        model_detail = '911 2017'
                    elif vin[9] == 'J':
                        model_number = '991.2'
                        model_detail = '911 2018'

                if model_number == '993': model_detail = '911 1993-1997'
                if model_number == '996': model_detail = '911 1997-2004'
                if model_number == '997':
                    if vin[9] == '4':
                        model_number = '997.1'
                        model_detail = '991 2004'
                    elif vin[9] == '5':
                        model_number = '997.1'
                        model_detail = '991 2005'
                    elif vin[9] == '6':
                        model_number = '997.1'
                        model_detail = '991 2006'
                    elif vin[9] == '7':
                        model_number = '997.1'
                        model_detail = '991 2007'
                    elif vin[9] == '8':
                        model_number = '997.1'
                        model_detail = '991 2008'
                    elif vin[9] == '9':
                        model_number = '997.2'
                        model_detail = '991 2009'
                    elif vin[9] == 'A':
                        model_number = '997.2'
                        model_detail = '991 2010'
                    elif vin[9] == 'B':
                        model_number = '997.2'
                        model_detail = '991 2011'
                    elif vin[9] == 'C':
                        model_number = '997.2'
                        model_detail = '991 2012'
                    elif vin[9] == 'D':
                        model_number = '997.2'
                        model_detail = '991 2013'

                if model_number == '9PA': model_detail = 'Cayenne 955(2002-2007), 957(2007-2010)'
                if model_number == '92A':
                    model_detail = 'Cayenne 958(2010-2017)'
                    if vin[9] == 'A':
                        model_number = '958.1'
                        model_detail = '958 2010'
                    elif vin[9] == 'B':
                        model_number = '958.1'
                        model_detail = '958 2011'
                    elif vin[9] == 'C':
                        model_number = '958.1'
                        model_detail = '958 2012'
                    elif vin[9] == 'D':
                        model_number = '958.1'
                        model_detail = '958 2013'
                    elif vin[9] == 'E':
                        model_number = '958.1'
                        model_detail = '958 2014'
                    elif vin[9] == 'F':
                        model_number = '958.2'
                        model_detail = '958 2015'
                    elif vin[9] == 'G':
                        model_number = '958.2'
                        model_detail = '958 2016'
                    elif vin[9] == 'H':
                        model_number = '958.2'
                        model_detail = '958 2017'
            else: # US cars
                model_number = vin[7] + vin[11]
                if model_number == '11': model_detail = '911 (G-model)'
                if model_number == '24': model_detail = '924'
                if model_number == '28': model_detail = '928'
                if model_number == '30': model_detail = '930 (911 G-model Turbo)'
                if model_number == '31': model_detail = '924 Turbo'
                if model_number == '44': model_detail = '944'
                if model_number == '51': model_detail = '944 Turbo'
                if model_number == '5B': model_detail = '95B Macan'
                if model_number == '64': model_detail = '964(911 1989-1994)'
                if model_number == '68': model_detail = '968'
                if model_number == '70': model_detail = '970 (Panamera 2009-2016)'
                if model_number == '71': model_detail = '971 (Panamera 2016-2023)'
                if model_number == '80': model_detail = '980 (Carrera GT)'
                if model_number == '81': model_detail = '981 (Boxster/Cayman 2012-2016)'
                if model_number == '82': model_detail = '982 (718 Boxster/Cayman 2016-2019)'
                if model_number == '86': model_detail = '986 (Boxster 1996-2004)'
                if model_number == '87':
                    if vin[9] == '5':
                        model_number = '87.1'
                        model_detail = '987 (Boxster/Cayman 2005)'
                    elif vin[9] == '6':
                        model_number = '87.1'
                        model_detail = '987 (Boxster/Cayman 2006)'
                    elif vin[9] == '7':
                        model_number = '87.1'
                        model_detail = '987 (Boxster/Cayman 2007)'
                    elif vin[9] == '8':
                        model_number = '87.1'
                        model_detail = '987 (Boxster/Cayman 2008)'
                    elif vin[9] == '9':
                        model_number = '87.2'
                        model_detail = '987 (Boxster/Cayman 2009)'
                    elif vin[9] == 'A':
                        model_number = '87.2'
                        model_detail = '987 (Boxster/Cayman 2010)'
                    elif vin[9] == 'B':
                        model_number = '87.2'
                        model_detail = '987 (Boxster/Cayman 2011)'
                    elif vin[9] == 'C':
                        model_number = '87.2'
                        model_detail = '987 (Boxster/Cayman 2012)'
                if model_number == '91':
                    if vin[9] == 'C':
                        model_number = '91.1'
                        model_detail = '911 2012'
                    elif vin[9] == 'D':
                        model_number = '91.1'
                        model_detail = '911 2013'
                    elif vin[9] == 'E':
                        model_number = '91.1'
                        model_detail = '911 2014'
                    elif vin[9] == 'F':
                        model_number = '91.1'
                        model_detail = '911 2015'
                    elif vin[9] == 'G':
                        model_number = '91.1'
                        model_detail = '911 2016'
                    elif vin[9] == 'H':
                        model_number = '91.2'
                        model_detail = '911 2017'
                    elif vin[9] == 'J':
                        model_number = '91.2'
                        model_detail = '911 2018'

                if model_number == '93': model_detail = '993 (911 1993-1997)'
                if model_number == '96': model_detail = '996 (911 1997-2004)'
                if model_number == '97':
                    if vin[9] == '4':
                        model_number = '97.1'
                        model_detail = '991 2004'
                    elif vin[9] == '5':
                        model_number = '97.1'
                        model_detail = '991 2005'
                    elif vin[9] == '6':
                        model_number = '97.1'
                        model_detail = '991 2006'
                    elif vin[9] == '7':
                        model_number = '97.1'
                        model_detail = '991 2007'
                    elif vin[9] == '8':
                        model_number = '97.1'
                        model_detail = '991 2008'
                    elif vin[9] == '9':
                        model_number = '97.2'
                        model_detail = '991 2009'
                    elif vin[9] == 'A':
                        model_number = '97.2'
                        model_detail = '991 2010'
                    elif vin[9] == 'B':
                        model_number = '97.2'
                        model_detail = '991 2011'
                    elif vin[9] == 'C':
                        model_number = '97.2'
                        model_detail = '991 2012'
                    elif vin[9] == 'D':
                        model_number = '97.2'
                    elif vin[9] == 'E':
                        model_number = '97.2'
                    elif vin[9] == 'F':
                        model_number = '97.2'
                    elif vin[9] == 'G':
                        model_number = '97.2'
                if model_number == 'PA':
                    model_detail = 'Cayenne 955(2002-2007), 957(2007-2010)'
                    model_number = '55'
                if model_number == '2A':
                    model_detail = 'Cayenne 958(2010-2017)'
                    if vin[9] == 'A':
                        model_number = '58.1'
                        model_detail = '58 2010'
                    elif vin[9] == 'B':
                        model_number = '58.1'
                        model_detail = '58 2011'
                    elif vin[9] == 'C':
                        model_number = '58.1'
                        model_detail = '58 2012'
                    elif vin[9] == 'D':
                        model_number = '58.1'
                        model_detail = '58 2013'
                    elif vin[9] == 'E':
                        model_number = '58.1'
                        model_detail = '58 2014'
                    elif vin[9] == 'F':
                        model_number = '58.2'
                        model_detail = '58 2015'
                    elif vin[9] == 'G':
                        model_number = '58.2'
                        model_detail = '58 2016'
                    elif vin[9] == 'H':
                        model_number = '58.2'
                        model_detail = '58 2017'

                model_number = '9' + model_number

            year_code = vin[9] #year code

            if year_code == '1': year = 2001
            if year_code == '2': year = 2002
            if year_code == '3': year = 2003
            if year_code == '4': year = 2004
            if year_code == '5': year = 2005
            if year_code == '6': year = 2006
            if year_code == '7': year = 2007
            if year_code == '8': year = 2008
            if year_code == '9': year = 2009
            if year_code == 'A': year = 2010
            if year_code == 'B': year = 2011
            if year_code == 'C': year = 2012
            if year_code == 'D': year = 2013
            if year_code == 'E': year = 2014
            if year_code == 'F': year = 2015
            if year_code == 'G': year = 2016
            if year_code == 'H': year = 2017
            if year_code == 'J': year = 2018
            if year_code == 'K': year = 2019
            if year_code == 'L': year = 2020
            if year_code == 'M': year = 2021
            if year_code == 'N': year = 2022
            if year_code == 'P': year = 2023
            if year_code == 'R': year = 2024
            if year_code == 'S': year = 2025
            if year_code == 'T': year = 2026
            if year_code == 'V': year = 2027
            if year_code == 'W': year = 2028
            if year_code == 'X': year = 2029

            if model_number == '964' or year_code > 2017:
                year = year - 30

        result = {}

        #result['model_detail'] = model_detail
        result['model_number'] = ''
        result['year'] =  year
        for m_number in CONST_MODEL_NUMBERS:
            if model_number == m_number:
                result['model_number'] = model_number
                break

        return result
    def update_parsing_pcf(self, vin_data):
        sql = "UPDATE api_pcf SET listing_age = %s WHERE id=%s " % (vin_data['listing_age'], vin_data['pcf_id'])

        try:
            self.cursor.execute(sql)
            self.conn.commit()
            print('PCF %s is updated successfully' % vin_data['pcf_id'])
        except Exception as e:
            print(e)
            self.conn.rollback()
    def insert_parsing_pcf(self, vin_data):

        try:
            year = int(vin_data['model_year'])
        except Exception as e:
            year = 0

        vin = vin_data['Vin']
        #if len(vin) < 17:
        #    return

        try:
            listing_year=int(vin_data['Year'])
        except Exception as e:
            listing_year = 0

        listing_title = vin_data['Description'].lower()
        listing_transmission = vin_data['listing_transmission'].lower()
        model_detail = vin_data['model_detail'].lower()

        listing_model_detail = vin_data['listing_model_detail'].lower()
        listing_description = vin_data['listing_description'].lower()
        bs_option_description = vin_data['bs_option_description'].lower()
        listing_color = vin_data['listing_color'].lower()
        gap_to_msrp = vin_data['gap_to_msrp']

        auto_trans = ''
        longhood = 0
        widebody = 0
        pccb = 0
        pts = 0
        air_cooled = 0
        lwb = 0
        body_type =''

        model_number = vin_data['model_number']

        # if (vin[3] == 'Z') and (vin[4] == 'Z') and (vin[5] == 'Z') : # RoW car
        #     model_number = vin[6] + vin[7] + vin[11]
        # else:
        #     model_number = '9' + vin[7] + vin[11]

        if ((year in (1963, 1973)) or (listing_year in (1963, 1973))) and ((model_detail.find('911') > -1) or (model_detail.find('912') > -1 ) or (listing_model_detail.find('911') > -1) or (listing_model_detail.find('912') > -1 )):
            longhood = 1

        listing_model_detail = listing_model_detail.replace('porsche', '')
        model_detail = model_detail.replace('porsche', '')

        if model_number == '930':
            widebody = 1

        if  (model_number == '964') and ((model_detail.find('turbo') > -1 ) or (listing_model_detail.find('turbo') > -1)):
            widebody = 1

        if  (model_number.find('991') > -1) and ((model_detail.find('turbo') > -1 ) or (listing_model_detail.find('turbo') > -1)):
            widebody = 1

        if  (model_number == '993') and ((model_detail.find('turbo') > -1 ) or (listing_model_detail.find('turbo') > -1)):
            widebody = 1

        if  (model_number == '996') and ((model_detail.find('turbo') > -1 ) or (listing_model_detail.find('turbo') > -1)):
            widebody = 1

        if  (model_number.find('997') > -1 ) and ((model_detail.find('turbo') > -1 ) or (listing_model_detail.find('turbo') > -1)):
            widebody = 1

        if  ((listing_model_detail.find('SSE') > -1) or (model_detail.find('SSE') > -1)  or (listing_description.find('SSE') > -1) or (listing_model_detail.find('super sport equipment') > -1 )
             or (model_detail.find('super sport equipment') > -1) or (listing_description.find('super sport equipment') > -1)) and (listing_year in (1984, 1989) or year in (1984, 1989)):
            widebody = 1
        if (listing_model_detail.find('widebody') > -1 ) or (model_detail.find('widebody') > -1) or (listing_title.find('widebody') > -1) or \
            (listing_model_detail.find('wide body') > -1 ) or (model_detail.find('wide body') > -1) or (listing_title.find('wide body') > -1):
            widebody = 1

        if  (model_number == '964') and ((model_detail.find('anniversary') > -1 ) or (listing_model_detail.find('anniversary') > -1)):
            widebody = 1

        if  (model_number == '993') and ((model_detail.find('2s') > -1 ) or (listing_model_detail.find('4s') > -1)):
            widebody = 1

        if  (model_number.find('997') > -1) and ((model_detail.find(' 4s') > -1 ) or (listing_model_detail.find(' 4s') > -1) or (model_detail.find(' 4') > -1 ) or (listing_model_detail.find(' 4') > -1)):
            widebody = 1

        if  (((model_detail.find('gts') > -1 ) or (listing_model_detail.find('gts') > -1)) and \
            ((model_detail.find('911') > -1 ) or (listing_model_detail.find('911') > -1) or (model_detail.find('carrera') > -1 ) or (listing_model_detail.find('carrera') > -1))):
            widebody = 1

        if  (model_number.find('991') > -1) and ((model_detail.find(' 4') > -1 ) or (listing_model_detail.find(' 4') > -1)):
            widebody = 1

        if  (model_number.find('991') > -1 ) and ((model_detail.find('rs') > -1 ) or (listing_model_detail.find('rs') > -1)):
            widebody = 1


        if (bs_option_description.find('exterior paint to sample') > -1) or (bs_option_description.find('exterior color to sample') > -1) or \
           (listing_title.find(' pts') > -1) or (listing_title.find('paint to sample') > -1) or (listing_title.find('color to sample') > -1) or \
           (listing_description.find(' pts') > -1) or (listing_description.find('paint to sample') > -1) or (listing_description.find('color to sample') > -1):
            pts = 1

        if (bs_option_description.find('ceramic') > -1) or (bs_option_description.find('pccb') > -1) or \
           (listing_title.find('pccb') > -1) or (listing_title.find('ceramic') > -1) or \
           (listing_description.find('pccb') > -1) or (listing_description.find('ceramic') > -1):
            pccb = 1
        if vin not in ('', None):
            if (year in (1948, 1997)) or (listing_year in (1948, 1997)) or (( (year == 1998)or (listing_year == 1998)) and (vin[11] == '3')):
                air_cooled = 1

        if bs_option_description.find('bucket') > -1:
            lwb = 1


        if (listing_transmission == 'auto') and ((listing_year in (1967, 1981)) or (year in (1967, 1981))):
            auto_trans = 'Sportomatic'
        if ((listing_transmission == 'auto'  ) or (bs_option_description.find('tiptronic') > -1)) and ((listing_year in (1989, 2008)) or (year in (1989, 2008))):
            auto_trans = 'Tiptronic'
        if ((listing_transmission == 'auto') or (bs_option_description.find('doppelkupplung') > -1)) and ((listing_year >= 2009) or ( year >= 2009)):
            auto_trans = 'PDK'

        if (listing_model_detail.find('cayenne')>-1) or (model_detail.find('cayenne')>-1):  body_type = 'SUV'
        if (listing_model_detail.find('boxster')>-1) or (model_detail.find('boxster')>-1): body_type = 'Convertible'
        if (listing_model_detail.find('cayman')>-1) or (model_detail.find('cayman')>-1): body_type = 'Coupe'
        if (listing_model_detail.find('panamera')>-1) or (model_detail.find('panamera')>-1): body_type = 'Sedan'
        if (listing_model_detail.find('macan')>-1) or (model_detail.find('macan')>-1): body_type = 'Crossover'
        if (listing_model_detail.find('cabrio')>-1) or (model_detail.find('cabrio')>-1): body_type = 'Convertible'
        if (listing_model_detail.find('cabriolet')>-1) or (model_detail.find('cabriolet')>-1): body_type = 'Convertible'
        if (listing_model_detail.find('coupe')>-1) or (model_detail.find('coupe')>-1): body_type = 'Copue'
        #if (listing_model_detail.find(u'coup', )>-1) or (model_detail.find(u'coup')>-1): body_type = 'Copue'
        if (listing_model_detail.find('roadster')>-1) or (model_detail.find('roadster')>-1): body_type = 'Roadster'
        if (listing_model_detail.find('spyder')>-1) or (model_detail.find('spyder')>-1): body_type = 'Spyder'
        if (listing_model_detail.find('speedster')>-1) or (model_detail.find('speedster')>-1): body_type = 'Convertible'
        if (listing_model_detail.find('targa')>-1) or (model_detail.find('targa')>-1): body_type = 'Targa'
        if (listing_model_detail.find('gt1')>-1) or (model_detail.find('gt1')>-1): body_type = 'Coupe'
        if (listing_model_detail.find('gt2')>-1) or (model_detail.find('gt2')>-1): body_type = 'Coupe'
        if (listing_model_detail.find('gt3')>-1) or (model_detail.find('gt3')>-1): body_type = 'Coupe'
        if (listing_model_detail.find('gt4')>-1) or (model_detail.find('gt4')>-1): body_type = 'Coupe'

        if (listing_model_detail.find(' gt ')>-1) or (model_detail.find(' gt ')>-1): body_type = 'Coupe'

        if (listing_model_detail.find('america')>-1) or (model_detail.find('america')>-1): body_type = 'Coupe'
        if (listing_model_detail.find('cup')>-1) or (model_detail.find('cup')>-1): body_type = 'Coupe'
        if (listing_model_detail.find('914')>-1) or (model_detail.find('914')>-1): body_type = 'Targa'
        if (listing_model_detail.find('924')>-1) or (model_detail.find('924')>-1): body_type = 'Coupe'
        if (listing_model_detail.find('928')>-1) or (model_detail.find('928')>-1): body_type = 'Coupe'
        if (listing_model_detail.find('942')>-1) or (model_detail.find('942')>-1): body_type = 'Coupe'
        if (listing_model_detail.find('gtr')>-1) or (model_detail.find('gtr')>-1): body_type = 'Coupe'

        if (listing_model_detail.find('944')>-1) or (model_detail.find('944')>-1): body_type = 'Coupe'
        if (listing_model_detail.find('911')>-1) or (model_detail.find('911')>-1): body_type = 'Coupe'

        if (listing_model_detail.find('959')>-1) or (model_detail.find('959')>-1): body_type = 'Coupe'

        if (listing_model_detail.find('968')>-1) or (model_detail.find('968')>-1): body_type = 'Coupe'
        if (listing_model_detail.find('912')>-1) or (model_detail.find('912')>-1): body_type = 'Coupe'
        if (listing_model_detail.find('356')>-1) or (model_detail.find('356')>-1): body_type = 'Coupe'

        if (listing_model_detail.find('718')>-1) or (model_detail.find('718')>-1): body_type = 'Coupe'

        color = listing_color


        option_code = ''
        option_description = ''
        placeholder = 0
        producted_usa = 0
        producted_globally = 0
        same_counts = 0
        listing_age = 0

        bGen = False
        while bGen == False:
            newKey = ''.join(random.choice('01234567890ABCDEF') for i in range(6))
            sql = "SELECT * FROM api_pcf WHERE vid ='%s'" % (newKey)
            self.cursor.execute(sql)
            result = self.cursor.fetchone()
            if result is None:
                bGen = True
                sql = "insert into api_pcf (longhood, widebody, pts, pccb, color, body_type, air_cooled, gap_to_msrp, listing_age, lwb_seats, auto_trans" \
                      ", option_code, option_description, placeholder, produced_usa, produced_globally, same_counts, vid, model_number) values (" \
                      "%s, %s, %s, %s, '%s', '%s', %s, %s, %s, %s, '%s', '%s', '%s', %s, %s, %s, %s, '%s', '%s') " % (longhood, widebody, pts, pccb, color, body_type, air_cooled,
                                                                                                          gap_to_msrp, listing_age, lwb, auto_trans, option_code,
                                                                                                          option_description, placeholder, producted_usa, producted_globally, same_counts, newKey, model_number)

                try:
                    self.cursor.execute(sql)
                    self.conn.commit()
                    print("'%s' is added to pcf successfully" %(newKey))
                    id = self.cursor.lastrowid
                    return id
                except Exception as e:
                    print(e)
                    self.conn.rollback()
                    return None

    def update_rennlist_cond(self):
        sql = "SELECT * FROM api_car WHERE site_id = '%s' " %(2)
        self.cursor.execute(sql)
        results = self.cursor.fetchall()
        for item in results:
            mileage = item[7]
            seller_type = item[13]
            cond = item[12]

            if seller_type == 'Dealership' and int(mileage) < 100 and cond == 'Used' and int(mileage) > 0:

                sql = "UPDATE api_car SET  cond = 'New' WHERE id=%s" % (item[0])

                try:
                    self.cursor.execute(sql)
                    self.conn.commit()
                    print('%s is updated successfully' %(item[0]))
                except Exception as e:
                    print(e)
                    self.conn.rollback()

    def remove_scam(self):
        sql = "SELECT * FROM api_car"
        self.cursor.execute(sql)
        results = self.cursor.fetchall()
        for item in results:
            listing_title = item[19].lower()

            if listing_title.find('scam') > -1:

                sql = "DELETE FROM api_car WHERE id=%s" % (item[0])

                try:
                    self.cursor.execute(sql)
                    self.conn.commit()
                    print('%s is removed successfully from scam' %(item[0]))
                except Exception as e:
                    print(e)
                    self.conn.rollback()

    def update_model_number(self):
        sql = "SELECT * FROM api_car"
        self.cursor.execute(sql)
        results = self.cursor.fetchall()

        for item in results:
            listing_title = item[19].lower()
            listing_year = item[6]
            model_detail = item[5]
            site_id = item[30]
            vin_code = item[1]

            if vin_code == '':
                if site_id == 3:
                    model_detail = item[3]
                data = self.parsing_vin(vin_code, listing_year, model_detail)
                pcf_id = item[29]

                if data['model_number'] == '':
                    continue

                sql = "UPDATE api_pcf SET  model_number = '%s' WHERE id=%s" % (data['model_number'], pcf_id)
                try:
                    self.cursor.execute(sql)
                    self.conn.commit()
                    print('%s is updated for model number' %(pcf_id))
                except Exception as e:
                    print(e)
                    self.conn.rollback()
    def remove_listings(self, model_number):
        sql = "SELECT * FROM api_pcf WHERE model_number = '%s'" % (model_number)
        self.cursor.execute(sql)
        results = self.cursor.fetchall()

        for item in results:
            sql = "DELETE FROM api_car WHERE pcf_id=%s" % (item[0])

            try:
                self.cursor.execute(sql)
                self.conn.commit()
                print('%s is removed successfully from api_car' %(item[0]))
            except Exception as e:
                print(e)
                self.conn.rollback()

            sql = "DELETE FROM api_pcf WHERE id=%s" % (item[0])

            try:
                self.cursor.execute(sql)
                self.conn.commit()
                print('%s is removed successfully from api_pcf' %(item[0]))
            except Exception as e:
                print(e)
                self.conn.rollback()
