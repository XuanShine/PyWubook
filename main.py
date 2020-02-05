"""Mettre à jour automatiquement les prix WuBook.

Usage:
    main.py [<days>]

Options:
    -h --help
    --version
"""
import os
import pickle
import time
from dataclasses import dataclass
from pprint import pprint
from datetime import datetime, timedelta
import xmlrpc.client
import logging


from price import price_for_double_eco

url = "https://wired.wubook.net/xrws/"


# TODO: faire attention au fichier de logs
logging.basicConfig(filename="main.log", level=logging.DEBUG, format="%(asctime)s -- %(name)s -- %(levelname)s -- %(message)s")

# LOAD ID
# File where identification is:
logins_path = os.path.join(os.path.dirname(__file__), '..', "id_pywubook.pkl")
with open(logins_path, "rb") as f_in:
    info = pickle.load(f_in)
user = info["user"]
pkey = info["pkey"]
lcode = info["lcode"]
del info


type_room = {"329039": "double economic",
             "329667": "double balcony",
             "329670": "triple economic",
             "405126": "single balcony",
             "405127": "single economic",
             "407751": "triple balcony"
            }

def get_avail(dfrom, dto, connection):
    """Get avail from dfrom to dto in the wubook server
    RETURN {<date>: {
                     <code_chambre>:<disponibilité>, ...}
            ...}"""
    
    return_code, avail = connection.server.fetch_rooms_values(connection.token, lcode, dfrom, dto)
    if return_code != 0:
        raise ConnectionError(f"in get_avail({dfrom}, {dto}, connection) error: {avail}")

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
    # TODO function can be test
    result = dict()
    for date, avail_day in avail.items():
        total_avail_day = 0
        for room, avail in avail_day.items():
            if room in list_code:
                total_avail_day += avail
        result[date] = total_avail_day
    return result


def update_price(room_code, date_price, connection):
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
    prices = [price for _, price in date_price_tuple]  # prices = [price1, price2, ...]

    if date_price_tuple[-1][0] != dto:
        raise Exception("Les dates ne sont pas continues pour mettre à jour les prix. Il doit manquer des dates: " + str(date_price_tuple))

    # Prevent price modification if triple eco endswith .99
    # On récupère les prix sur wubook
    return_code, plan_prices = connection.server.fetch_plan_prices(connection.token, lcode, 0, dfrom, dto)
    if return_code != 0:
        raise ConnectionError(f"in update_price({room_code}, {date_price}, connection), error: {avail}")

    # On détermine les prix qui vont être modifiés
    actual_room_prices = plan_prices[room_code]
    modifs = dict()  # ne sert qu’à informer de ce qui a été modifié
    for i in range(len(actual_room_prices)):
        if prices[i] != actual_room_prices[i]:
            date_tmp = (datetime.strptime(dfrom, "%d/%m/%Y") + timedelta(days=i)).strftime("%d/%m/%Y")
            modifs[date_tmp] = prices[i]

    # On évite de modifier les prix dont la triple éco fini par .99
    triple_eco_prices = plan_prices["329670"]  # : [price1, price2, ...]
    ignore = dict()  # ne sert qu’à informer de ce qui a été ignoré
    for i in range(len(triple_eco_prices)):
        if str(triple_eco_prices[i]).endswith(".99"):
            prices[i] = plan_prices[room_code][i]
            date_tmp = (datetime.strptime(dfrom, "%d/%m/%Y") + timedelta(days=i)).strftime("%d/%m/%Y")
            ignore[date_tmp] = prices[i]
            # on supprime ce qui a été modifié dans modifs
            modifs.pop(date_tmp, None)
    
    # Call wubook function for update
    connection.server.update_plan_prices(connection.token, lcode, 0, dfrom, {room_code: prices})
    
    return ignore, modifs


def update_price_automatic(connection, period=60):
    """update price in the next period (in days)
    and print ignore dates"""
    dfrom_time = datetime.today()
    dfrom = dfrom_time.strftime("%d/%m/%Y")
    dto_time = dfrom_time + timedelta(days=period)
    dto = dto_time.strftime("%d/%m/%Y")

    logging.info(f"Mise à jour en cours: (start: {dfrom}, end: {dto})")

    avail = get_avail(dfrom, dto, connection)
    total_avail = sum_avail(avail)

    price_double_eco = dict()
    price_double_balcon = dict()
    price_triple_eco = dict()
    for date, avail in total_avail.items():
        price_double_eco[date] = round(price_for_double_eco(avail), 2)  # Détermine les nouvelles valeurs
        price_double_balcon[date] = round(price_double_eco[date] * 1.1, 2)  # Balcon à 10% plus élevé.
        price_triple = round(price_double_eco[date] * 1.15, 2)  # Triple à 15% plus élevé que les doubles éco. Min: 54€
        if price_triple < 54:
            price_triple = 54
        price_triple_eco[date] = price_triple
    ignore = dict()
    modifs = dict()
    ignore["double_eco"], modifs["double_eco"] = update_price("329039", price_double_eco, connection)  # deco
    ignore["double_balcon"], modifs["double_balcon"] = update_price("329667", price_double_balcon, connection)  # dblc
    ignore["triple"], modifs["triple"] = update_price("329670", price_triple_eco, connection)  # triple

    pprint(f"Dates ignorées: {ignore}")
    pprint(f"Dates modifiées: {modifs}")
    logging.info(f"Dates ignorées: {ignore}")
    logging.info(f"Dates modifiées: {modifs}")
    

@dataclass
class Connection:
    server : None
    token : str


def main(days):
    with xmlrpc.client.ServerProxy(url, verbose=False) as server:
        try:
            with open(logins_path, "rb") as f_in:
                info = pickle.load(f_in)
            password = info["password"]
            returnCode, token = server.acquire_token(user, password, pkey)
            del password
            if returnCode != 0:
                logging.warning("Can’t connect to server")
            else:
                logging.info("Server connected")
            
                update_price_automatic(period=days, connection=Connection(server, token))
        except Exception:
            import traceback
            logging.error(f"Exception dans la main fonction de PyWubook: {traceback.format_exc()}")
        finally:
            if returnCode != 0:  # N’a pas pu se connecter au serveur
                pass
            else:
                try:
                    server.release_token(token)
                except xmlrpc.client.ProtocolError as e:
                    logging.warning("ProtocolError while realeasing token from wubook server: \n{e}")
                finally
                    logging.info("Server disconnected")


if __name__ == "__main__":
    from docopt import docopt

    arguments = docopt(__doc__, version="1.0")
    days = int(arguments.get("[<days>]", 60))
    main(days)