import sys, os

C = os.path.abspath(os.path.dirname(__file__))

from selectorlib import Extractor
import requests 
from time import sleep
import csv
from datetime import datetime, timedelta
from pprint import pprint

# Create an Extractor by reading from the YAML file
e = Extractor.from_yaml_file(os.path.join(C, 'booking.yml'))

def scrape(url):    
    headers = {
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
        'DNT': '1',
        'Upgrade-Insecure-Requests': '1',
        # You may want to change the user agent if you get blocked
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.113 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',

        'Referer': 'https://www.booking.com/index.en-gb.html',
        'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
    }

    # Download the page using requests
    print("Downloading %s"%url)
    r = requests.get(url, headers=headers)
    # Pass the HTML of the page and create 
    return e.extract(r.text,base_url=url)




URL_TEMPLATE = "https://www.booking.com/searchresults.en-gb.html?label=gen173nr-1DCAEoggI46AdIM1gEaKQCiAEBmAEJuAEHyAEM2AED6AEBiAIBqAIDuALCxJ31BcACAQ&lang=en-gb&sid=4c66111699f2737e59fa9bb34705aef5&sb=1&sb_lp=1&src=index&src_elem=sb&error_url=https%3A%2F%2Fwww.booking.com%2Findex.en-gb.html%3Flabel%3Dgen173nr-1DCAEoggI46AdIM1gEaKQCiAEBmAEJuAEHyAEM2AED6AEBiAIBqAIDuALCxJ31BcACAQ%3Bsid%3D4c66111699f2737e59fa9bb34705aef5%3Bsb_price_type%3Dtotal%26%3B&ss=Grasse%2C+Provence-Alpes-C%C3%B4te+d%27Azur%2C+France&is_ski_area=&ssne=Cannes&ssne_untouched=Cannes&group_adults=2&group_children=0&no_rooms=1&b_h4u_keep_filters=&from_sf=1&ss_raw=grasse&ac_position=0&ac_langcode=en&ac_click_type=b&dest_id=-1430518&dest_type=city&place_id_lat=43.659992&place_id_lon=6.92362&search_pageview_id=5f0d92c3aeac038d&search_selected=true&search_pageview_id=5f0d92c3aeac038d&ac_suggestion_list_length=5&ac_suggestion_theme_list_length=0"
URL_TEMPLATE2 = "https://www.booking.com/searchresults.fr.html?aid=318615&label=French_France-FR-FR-116605733887-4eIPfuV0xgYOMDFPkQsxiAS479723944020%3Apl%3Ata%3Ap1%3Ap2%3Aac%3Aap%3Aneg%3Afi146292847245%3Atiaud-297601666955%3Adsa-1073823970767%3Alp9054940%3Ali%3Adec%3Adm&sid=4c66111699f2737e59fa9bb34705aef5&sb=1&sb_lp=1&src=index&src_elem=sb&error_url=https%3A%2F%2Fwww.booking.com%2Findex.fr.html%3Faid%3D318615%3Blabel%3DFrench_France-FR-FR-116605733887-4eIPfuV0xgYOMDFPkQsxiAS479723944020%253Apl%253Ata%253Ap1%253Ap2%253Aac%253Aap%253Aneg%253Afi146292847245%253Atiaud-297601666955%253Adsa-1073823970767%253Alp9054940%253Ali%253Adec%253Adm%3Bsid%3D4c66111699f2737e59fa9bb34705aef5%3Bsb_price_type%3Dtotal%3Bsrpvid%3D3346a73e0b0000d6%26%3B&ss=Mouans-Sartoux&is_ski_area=0&ssne=Mouans-Sartoux&ssne_untouched=Mouans-Sartoux&dest_id=-1453848&dest_type=city&group_adults=2&group_children=0&no_rooms=1&b_h4u_keep_filters=&from_sf=1"
def buildUrlBooking(datefrom, dateto=None, ibis=False):
    """Build a url booking of list of hotel near Provence Alpes Cotes d’Azur.
    datefrom and dateto: dd/mm/aaaa
    """
    dayfrom, monthfrom, yearfrom = datefrom.split("/")
    if not dateto:
        dateto = (datetime.strptime(datefrom, "%d/%m/%Y") + timedelta(days=1)).strftime("%d/%m/%Y")
    dayto, monthto, yearto = dateto.split("/")
    if not ibis:
        return URL_TEMPLATE + f"&checkin_year={yearfrom}&checkin_month={monthfrom}&checkin_monthday={dayfrom}&checkout_year={yearto}&checkout_month={monthto}&checkout_monthday={dayto}"
    else:
        return URL_TEMPLATE2 + f"&checkin_year={yearfrom}&checkin_month={monthfrom}&checkin_monthday={dayfrom}&checkout_year={yearto}&checkout_month={monthto}&checkout_monthday={dayto}"


import csv

def main(days=6*30):
    with open(os.path.join(C, "data.csv"), mode="w", newline="") as price_file:
        fieldnames = ["date", "poste", "ibis", "campanile", "casabella"]
        writer = csv.DictWriter(price_file,  fieldnames=fieldnames)
        writer.writeheader()

    def writeInFile(datas):
        """
        datas:
        [ {date: ..., poste: ..., ibis: ..., campanile: ..., casabella: ...},
        {...},
        ...
        ]
        """
        with open(os.path.join(C, "data.csv"), mode="a", newline="") as price_file:
            fieldnames = ["date", "poste", "ibis", "campanile", "casabella"]
            writer = csv.DictWriter(price_file,  fieldnames=fieldnames)
            for day in datas:
                writer.writerow(day)

    result_temp = []
    for day in range(0, days):
        date = (datetime.today() + timedelta(days=day)).strftime("%d/%m/%Y")
        res2 = {"date": date}
        data = scrape(buildUrlBooking(date))
        data2 = scrape(buildUrlBooking(date, ibis=True))
        for data in data["hotels"] + data2["hotels"]:
            if "Poste" in data["name"]:
                res2["poste"] = int(data['price'].lstrip("€\xa0"))
            elif "Ibis Budget Cannes Mouans Sartoux" in data["name"]:
                res2["ibis"] = int(data['price'].lstrip("€\xa0"))
            elif "Campanile" in data["name"]:
                res2["campanile"] = int(data['price'].lstrip("€\xa0"))
            elif "CasaBella" in data["name"]:
                res2["casabella"] = int(data['price'].lstrip("€\xa0"))
        result_temp.append(res2)
        if day % 5 == 0:
            writeInFile(result_temp)
            result_temp = []
    else:
        writeInFile(result_temp)

if __name__ == "__main__":
    main(30*3)