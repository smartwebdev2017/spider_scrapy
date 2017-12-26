__author__ = 'root'

import csv
import re
from pcarfinder import PcarfinderDB

db = PcarfinderDB()
index = 0

with open('Options.csv') as csvfile:
    readCSV = csv.reader(csvfile, delimiter=',')

    for row in readCSV:
        if index > 0:
            vin_id = row[1]
            code = row[2]
            try:

                value = row[3] + ',' + row[4]
            except Exception as e:
                value = row[3]

            db.insert_temp_data(vin_id, code, value)

        index = index + 1

index = 0
with open('VINs.csv') as seedcsvfile:
    readSeedCSV = csv.reader(seedcsvfile, delimiter=',')

    for row in readSeedCSV:
        if index > 0:
            old_id = row[0]
            vin = row[1]
            title = row[2]
            msrp = row[3]
            try:
                model_year = re.search('(\d{4}\s)(.*?\s)(.*?$)', title).group(1)
            except Exception as e:
                print(e)
                model_year = 0000

            try:
                model = re.search('(\d{4}\s)(.*?\s)(.*?$)', title).group(2)
            except Exception as e:
                print(e)
                model = ''

            try:
                model_detail =  model + re.search('(\d{4}\s)(.*?\s)(.*?$)', title).group(3)
            except Exception as e:
                model_detail = ''

            new_id = db.insert_bsf(vin, msrp, '', model_year, model_detail, '', '', '')

            options = db.getOptionsByBsfId(old_id)
            for option in options:
                if option[2] == 'Prod Month:':
                    production_month = option[3]
                elif option[2] == 'Warranty Start:':
                    warranty_start = option[3]
                elif option[2] == 'Exterior:':
                    color = option[3]
                elif option[2] == 'Interior:':
                    interior = option[3]
                elif option[2] == 'Division:':
                    pass
                elif option[2] == 'Commission #:':
                    pass
                elif option[2] == '&nbsp;':
                    pass
                elif option[2] == 'VIN:':
                    pass
                elif option[2] == 'Price:':
                    pass
                elif option[2] == 'Commission #:':
                    pass
                else:
                    db.insert_bsf_options(new_id, option[2], option[3])
            #new_id = db.insert_bsf(vin, msrp, warranty_start, model_year, model_detail, color, production_month, interior)
            db.updateBsfById(new_id, warranty_start, production_month, color, interior)


        index = index + 1