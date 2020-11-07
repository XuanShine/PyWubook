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


from price import priceDoubleStd, priceTripleStd, matchPrice10Low

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

# différencier chambres "réelles" et chambres "virtuelles"
REAL_ROOMS = {"329039", "329667", "329670", "407751", "469743", "469744"}

type_room = {"329039": "double economic",
             "329667": "double balcony",
             "329670": "triple economic",
             "405126": "single balcony",
             "405127": "single economic",
             "407751": "triple balcony",
             "469743": "familiale",
             "469744": "kichenette"
            }

room_to_code = {"sstd": "405127",
                "sblc": "405126",
                "dstd": "329039",
                "dblc": "329667",
                "tstd": "329670",
                "tblc": "407751",
                "fblc": "469743",
                "ktch": "469744"
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


def sum_avail(avail, list_code=REAL_ROOMS):
    """Total des disponibilités par jour des chambres dans list_code.
    INPUT: {<date>: {<code_chambre>: <disponibilité, ...},
            ... }
        voir fonction get_avail(dfrom, dto)
    RETURN {<date>: <total_disponibilité>, ...} <date>: dd/mm/yyyy"""
    # TODO function can be test
    result = dict()
    for date, avail_day in avail.items():
        total_avail_day = 0
        for room, avail in avail_day.items():
            if room in list_code:
                total_avail_day += avail
        result[date] = total_avail_day
    return result


@dataclass
class Connection:
    server : None
    token : str


def main(days, simulation=False):
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
                update_price_automatic(period=days, connection=Connection(server, token), simulation=simulation)
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
                else:
                    logging.info("Server disconnected")


def update_price_automatic(connection, period=60, dstart=None, simulation=False):
    """update price in the next period (in days)
    and print ignore dates
    
    Il faut calculer sstd, sstdOTA, dstd, dstdOTA, tstd, tstdOTA. Les balcons sont de-facto a 15% plus cher. La kichenette est fixé au prix du dblc et la familiale est déjà fixé.
    Comme il faut concurrencer les autres hôtels, il faut donc que le dstdOTA soit calculé en 1er.
    En ayant le dstdOTA, on peut utiliser les fonctions (dans price.py): matchPrice10Low pour calculer dstd.
    En re-appliquant matchPrice10Low sur dstd, on trouve le sstd. Et le dstd est lui-même le sstdOTA
    Pour le triple, il faut de la même manière concurrencer en calculant d’abord le tstdOTA, puis appliquer matchPrice10Low pour trouver le tstd.
    """
    if dstart:
        dfrom_time = datetime.strptime(dstart, "%d/%m/%Y")
    else:
        dfrom_time = datetime.today()
    dfrom = dfrom_time.strftime("%d/%m/%Y")
    dto_time = dfrom_time + timedelta(days=period)
    dto = dto_time.strftime("%d/%m/%Y")

    logging.info(f"Mise à jour en cours: (start: {dfrom}, end: {dto})")

    avail = get_avail(dfrom, dto, connection)
    total_avail = sum_avail(avail)

    prices_dstdOTA = dict()  # {<date>: price, ...}
    prices_tstdOTA = dict()
    for date, avail in total_avail.items():
        prices_dstdOTA[date] = round(priceDoubleStd(avail, date), 2)
        prices_tstdOTA[date] = round(priceTripleStd(avail, date), 2)

    update_price(room_to_code["dstd"], prices_dstdOTA, connection, simulation=simulation, OTA=True)
    update_price(room_to_code["dstd"], {date: matchPrice10Low(prices_dstdOTA[date]) for date in prices_dstdOTA}, connection, simulation=simulation, OTA=False)
    update_price(room_to_code["sstd"], {date: matchPrice10Low(prices_dstdOTA[date]) for date in prices_dstdOTA}, connection, simulation=simulation, OTA=True)
    update_price(room_to_code["sstd"], {date: matchPrice10Low(matchPrice10Low(prices_dstdOTA[date])) for date in prices_dstdOTA}, connection, simulation=simulation, OTA=False)
    update_price(room_to_code["tstd"], prices_tstdOTA, connection, simulation=simulation, OTA=True)
    update_price(room_to_code["tstd"], {date: matchPrice10Low(prices_tstdOTA[date], base=60) for date in prices_dstdOTA}, connection, simulation=simulation, OTA=False)


def update_price(room_code, date_price, connection, simulation=False, OTA=True):
    """Update new price in the wubook server
    INPUT date_price: {<date>: <price>, ..}
    To update, we need to call:
        update_plan_prices(token, lcode, pid, dfrom, prices)
        where prices = { <room_code> : [price1, price2, ...], ...}
    In this function, prices = [price1, price2, ...]
    
    RETURN """

    # Change de {<date>: <price>, ...} à {<date>: [<price1>, <price2>, ...], ...}
    date_price_tuple = list(sorted(date_price.items(), key=lambda dico: datetime.strptime(dico[0], "%d/%m/%Y")))
    days = len(date_price_tuple) - 1  # On exclu le dernier jour.
    dfrom = date_price_tuple[0][0]
    dto = (datetime.strptime(dfrom, "%d/%m/%Y") + timedelta(days=days)).strftime("%d/%m/%Y")
    prices = [price for _, price in date_price_tuple]  # prices = [price1, price2, ...]

    if date_price_tuple[-1][0] != dto:
        raise Exception("Les dates ne sont pas continues pour mettre à jour les prix. Il doit manquer des dates: " + str(date_price_tuple))

    # Call wubook function for update
    if not simulation:
        if OTA:
            connection.server.update_plan_prices(connection.token, lcode, 174018, dfrom, {room_code: prices})
        else: 
            connection.server.update_plan_prices(connection.token, lcode, 0, dfrom, {room_code: prices})
    
    is_ota = "OTA" if OTA else ""
    logging.info(f"{type_room[room_code]}{is_ota}: {date_price}")


def get_prices_avail_today():
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

                dfrom = dto = datetime.now().strftime("%d/%m/%Y")
                return_code, plan_prices = server.fetch_plan_prices(token, lcode, 0, dfrom, dto)
                return_code2, avails = server.fetch_rooms_values(token, lcode, dfrom, dto)
                if return_code != 0:
                    raise ConnectionError(f"in get_prices_today(), error: {plan_prices}")
                if return_code2 != 0:
                    raise ConnectionError(f"in get_prices_today(), error: {avails}")
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
                else:
                    logging.info("Server disconnected")
            return plan_prices, avails

if __name__ == "__main__":
    # from docopt import docopt

    # arguments = docopt(__doc__, version="1.0")
    # days = int(arguments.get("[<days>]", 60))
    main(1, simulation=False)

def test_sum_avail():
    # TODO
    pass