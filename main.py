import pickle
import time
from pprint import pprint
from datetime import datetime, timedelta
import xmlrpc.client
import logging

from price import price_for_double_eco

url = "https://wired.wubook.net/xrws/"
server = xmlrpc.client.ServerProxy(url, verbose=False)

# TODO: faire attention au fichier de logs
logging.basicConfig(filename="main.log", level=logging.DEBUG, format="%(asctime)s -- %(name)s -- %(levelname)s -- %(message)s")

# LOAD ID
# File where identification is:
with open("../id_pywubook.pkl", "rb") as f_in:
    info = pickle.load(f_in)
user = info["user"]
password = info["password"]
pkey = info["pkey"]
lcode = info["lcode"]

res, token = server.acquire_token(user, password, pkey)
logging.info("Server connected")

type_room = {"329039": "double economic",
             "329667": "double balcony",
             "329670": "triple economic",
             "405126": "single balcony",
             "405127": "single economic",
             "407751": "triple balcony"
            }

def get_avail(dfrom, dto):
    """Get avail from dfrom to dto in the wubook server
    RETURN {<date>: {
                     <code_chambre>:<disponibilité>, ...}
            ...}"""
    
    return_code, avail = server.fetch_rooms_values(token, lcode, dfrom, dto)
    if return_code != 0:
        raise ConnectionError(avail)

    dfrom_time = datetime.strptime(dfrom, "%d/%m/%Y")
    dto_time = datetime.strptime(dto, "%d/%m/%Y")
    days_diff = (dto_time - dfrom_time).days

    result = dict()
    for i in range(days_diff):
        temp_dict = dict()
        for room in type_room:
            temp_dict[room] = avail[room][i].get("avail", 0)
        result[(dfrom_time + timedelta(days=i)).strftime("%d/%m/%Y")] = temp_dict
    return result


def sum_avail(avail, list_code=("329039", "329667", "329670")):
    """Total des disponibilités par jour des chambres dans list_code.
    INPUT: {<date>: {<code_chambre>: <disponibilité, ...},
            ... }
        voir fonction get_avail(dfrom, dto)
    RETURN {<date>: <total_disponibilité>, ...}"""
    result = dict()
    for date, avail_day in avail.items():
        total_avail_day = 0
        for room, avail in avail_day.items():
            if room in list_code:
                total_avail_day += avail
        result[date] = total_avail_day
    return result


def update_price(room_code, date_price):
    """Update new price in the wubook server
    If existing price in wubook "triple eco" ends with .99, then doesn’t modify price.
    INPUT date_price: {<date>: <price>, ..}
    To update, we need to call:
        update_plan_prices(token, lcode, pid, dfrom, prices)
        where prices = { <room_code> : [price1, price2, ...], ...}
    In this function, prices = [price1, price2, ...]
    
    RETURN dates and prices that was not changed {<date>: <price>, ..} or None """

    date_price_tuple = list(sorted(date_price.items(), key=lambda dico: datetime.strptime(dico[0], "%d/%m/%Y")))
    days = len(date_price_tuple) - 1  # On exclu le dernier jour.
    dfrom = date_price_tuple[0][0]
    dto = (datetime.strptime(dfrom, "%d/%m/%Y") + timedelta(days=days)).strftime("%d/%m/%Y")
    prices = [price for _, price in date_price_tuple]

    if date_price_tuple[-1][0] != dto:
        raise Exception("Les dates ne sont pas continues pour mettre à jour les prix. Il doit manquer des dates: " + str(date_price_tuple))

    # Prevent price modification if triple eco endswith .99
    _, plan_prices = server.fetch_plan_prices(token, lcode, 0, dfrom, dto)
    triple_eco_prices = plan_prices["329670"]
    ignore = dict()  # to be return
    for i in range(len(triple_eco_prices)):
        if str(triple_eco_prices[i]).endswith(".99"):
            prices[i] = plan_prices[room_code][i]
            date_tmp = (dfrom.strptime("%d/%m/%Y") + timedelta(days=i)).strftime("%d/%m/%Y")
            ignore[date_tmp] = prices[i]
    
    # Call wubook function for update
    server.update_plan_prices(token, lcode, 0, dfrom, {room_code: prices})
    
    return ignore


def update_price_automatic(period=60):
    """update price in the next period (in days)
    and print ignore dates"""
    dfrom_time = datetime.today()
    dfrom = dfrom_time.strftime("%d/%m/%Y")
    dto_time = dfrom_time + timedelta(days=period)
    dto = dto_time.strftime("%d/%m/%Y")

    logging.info(f"Mise à jour en cours: (start: {dfrom}, end: {dto})")

    avail = get_avail(dfrom, dto)
    total_avail = sum_avail(avail)

    price_double_eco = dict()
    price_double_balcon = dict()
    for date, avail in total_avail.items():
        price_double_eco[date] = round(price_for_double_eco(avail), 2)  # Détermine les nouvelles valeurs
        price_double_balcon[date] = round(price_double_eco[date] * 1.1, 2)  # Balcon à 10% plus élevé.
    ignore = dict()
    ignore["double_eco"] = update_price("329039", price_double_eco)  # deco
    ignore["double_balcon"] = update_price("329667", price_double_balcon)  # dblc
    ignore["triple"] = update_price("329670", price_double_eco)  # prix triple fixée sur deco

    pprint(ignore)
    logging.info(f"Dates ignorées: {ignore}")
    

def main():
    update_price_automatic()


if __name__ == "__main__":
    try:
        main()
    finally:
        server.release_token(token)