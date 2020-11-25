import requests
from datetime import datetime, timedelta
import httpx
from requests.api import post
from json.decoder import JSONDecodeError
# import pandas as pd
import logging


def cost(hotel_key, date):
    """date: datetime"""
    url = "https://data.xotelo.com/api/rates?hotel_key=" + hotel_key + "&chk_in=" + date.strftime("%Y-%m-%d") + "&chk_out=" + ((date + timedelta(days=1)).strftime("%Y-%m-%d"))
    res = requests.get(url)

    try:
        data = res.json()['result']['rates']
    except TypeError as e:
        logging.error(e + f"\nIn xotelo.py file function cost({hotel_key}, {date})")
        return 0
    except JSONDecodeError as e:
        logging.error(e + f"\nIn xotelo.py file function cost({hotel_key}, {date})")
        return 0
    minCost  = min(data, key=(lambda site: site['rate']))
    minCost = (minCost['rate'] + minCost['tax']) * 0.8585  # conversion en euro
    return int(minCost)

    #!use res for testing as res.json
    # with open('Hotel Pricing/res.json') as f:
    #     data = json.load(f)['result']['rates']

def get_price(hotel_key, start, end):
    """start: datetime
    end: datetime"""
    assert start < end
    result = []
    while start < end:
        result.append(cost(hotel_key, start))
        start += timedelta(days=1)
        print((end - start).days)
    return result


# date = (datetime.today())
# df = pd.read_csv('Hotel Pricing/prices.csv',delimiter=',')
# dateString = date.strftime("%Y-%m-%d")
# df[dateString]=" "

# for index, row in df.iterrows():
#     df.loc[index,dateString] = cost(row['hotel code'])
#     print(row['Hotel'], row['hotel code'])

# print(df)
# df.to_csv("Hotel Pricing/prices.csv", index=False)

poste_key = "g1380878-d2184159"
ibis_budget_mouans = "g666506-d1071475"

if __name__ == "__main__":
    print(get_price(ibis_budget_mouans, datetime(2021, 1, 1, 12, 34, 34, 34), datetime(2021, 1, 1, 12, 34, 34, 34) + timedelta(days=1)))