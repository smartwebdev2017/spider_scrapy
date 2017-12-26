__author__ = 'root'
from bs4 import BeautifulSoup
import requests
import re

vin = 'WP1AD2A27DLA70957'

def getBSinfo(vin):
    url = 'https://admin.porschedealer.com/reports/build_sheets/print.php?vin=%s'

    res = requests.get(url % vin)

    bs = BeautifulSoup(res.content, 'html.parser')
    title = bs.find('h1').text
    try:
        model_year = re.search('(\d{4}\s)(.*?\s)(.*?$)', title).group(1)
        model = re.search('(\d{4}\s)(.*?\s)(.*?$)', title).group(2)
        model_detail =  model + re.search('(\d{4}\s)(.*?\s)(.*?$)', title).group(3)


    except Exception as e:
        print('Parsing Error in regular expressions')

    vehicle = bs.find('div', {'class':'vehicle'})
    vehicle_labels = vehicle.findAll('div', {'class':'label'})
    vehicle_values = vehicle.findAll('div', {'class':'value'})

    print('Vehicle')
    for i in range(0, len(vehicle_labels)):
        print('%s, %s' %(vehicle_labels[i].text, vehicle_values[i].text))

    options = bs.find('div', {'class':'options'})
    options_labels = options.findAll('div', {'class':'label'})
    options_values = options.findAll('div', {'class':'value'})

    print('Options')
    for i in range(0, len(options_labels)):
        print('%s, %s' %(options_labels[i].text, options_values[i].text))

    print(bs)


getBSinfo(vin)