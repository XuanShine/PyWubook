import sys, os

C = os.path.abspath(os.path.dirname(__file__))

from os import access
import sys, os
import math
import statistics
from dataclasses import dataclass
from datetime import datetime, date
from HotelRates.xotelo import ibis_budget_mouans, cost
from statistics import mean
import logging
import csv

TOTAL_ROOMS = 22
# TODO: server can change the availlability of TOTAL_ROOMS

special_dates = {  # augmentation en % : 50% => 50
    "21/02/2020" : 5,
    "22/02/2020" : 00,  # Rallye 2 CV
    "23/02/2020" : 5,

    "03/03/2020" : 0,  # Événement inconnu

    "07/03/2020" : 10,  # duathlon Grasse
    # Fête du jasmin
    "06/05/2020": 10,
    "07/05/2020": 10,
    "08/05/2020": 10,
    "09/05/2020": 10, # Fête de la rose
    # Concours de danse
    "22/10/2020" : 10,
    "23/10/2020" : 10,
    "24/10/2020" : 10,
    "25/10/2020" : 5,
    # Mariage
    "10/10/2020" : 10,
    # Marathon ?
    "07/11/2020": 15,
    # Mariage 15/13/2020
    "15/12/2020": 15,
    # VTT dans Grasse
    # ASA GRASSE 2021
    "03/04/2021": 50,
    # ASA GRASSE 2022
    "02/04/2021": 50,

}

@dataclass
class Rate:
    n_rooms: int
    n_room_increase: int  # Augmente au bout de <n_room_increase> chambres réservées
    min_price: float
    # Les deux variables suivants sont dépendants l’un de l’autre.
    increase: int  # (in %)
    max_price: float


low_season = Rate(
    n_rooms=25,
    n_room_increase=4,
    min_price=49,
    increase=None,
    max_price=69
)
# mid_season = Rate()
# full_season = Rate()
# july = Rate()
# congres = Rate()
# saturday = Rate()  # mariage
# christmas_new_year = Rate()

switch_rate = {
    1: Rate(n_rooms=25, n_room_increase=2, min_price=47, increase=None, max_price=84),  # 44 48 53 58 64 70 77 85 94 103 114 125 138
    2: Rate(n_rooms=25, n_room_increase=2, min_price=47, increase=None, max_price=84),  # 47 48 50 52 54 56 58 61 63 66 68 71 74
    3: Rate(n_rooms=25, n_room_increase=2, min_price=47, increase=None, max_price=89),   # 44 46 48 50 53 56 58 61 65 68 71 75 79
    4: Rate(n_rooms=25, n_room_increase=4, min_price=53, increase=6, max_price=None),   # 53 56 59 63 66 70 75
    5: Rate(n_rooms=25, n_room_increase=4, min_price=54, increase=None, max_price=74),  # 54 56 59 63 66 70 74
    6: Rate(n_rooms=25, n_room_increase=4, min_price=54, increase=None, max_price=84),  # 54 58 62 67 72 78 84
    7: Rate(n_rooms=25, n_room_increase=4, min_price=59, increase=None, max_price=99),  # 59 64 70 76 83 90 98
    8: Rate(n_rooms=25, n_room_increase=4, min_price=74, increase=None, max_price=120), # 74 79 85 91 98 106 114
    9: Rate(n_rooms=25, n_room_increase=4, min_price=54, increase=None, max_price=110),  # 54 58 62 67 72 78 84
    10: Rate(n_rooms=25, n_room_increase=4, min_price=44, increase=None, max_price=90), # 44 46 49 53 56 60 63
    11: Rate(n_rooms=25, n_room_increase=4, min_price=44, increase=None, max_price=90), # 44 46 49 53 56 60 63
    12: Rate(n_rooms=25, n_room_increase=3, min_price=44, increase=None, max_price=90), # 44 46 48 50 53 55 58 61 63
}

def explicit_rate(rate: Rate):
    if rate.max_price:
        n_rate = rate.n_rooms // rate.n_room_increase
        if rate.n_rooms % rate.n_room_increase == 0:  # évite les cas où le nombre de chambre peut être divisé par le nombre de chambre à augmenter ce qui faussent les résultats
           n_rate -= 1
        rate.increase = (math.pow(rate.max_price/rate.min_price, 1 / n_rate) - 1) * 100
    
    if rate.increase:
        prices = [rate.min_price]
        for i in range(rate.n_rooms // rate.n_room_increase):
            prices.append(prices[-1] * (1 + rate.increase/100))
    return prices


def calcul_price(total_avail: int, rate: Rate=None, add_percent: float=0):
    """add_percent : 50 -> 50%, ect.."""
    rate = rate or low_season  # if not rate
    prices = explicit_rate(rate)
    i = (rate.n_rooms - total_avail) // rate.n_room_increase  # indice de l’augmentation
    if i < 0:  # if rate.n_rooms < total_avail
        i = 0
    res = prices[i] * (1 + add_percent/100)
    assert res >= 40
    return math.floor(res)


def graph_price(rate):
    """Show a list of evolution of price"""
    prices = explicit_rate(rate)
    print(*map(math.floor, prices))

def priceDoubleStd(total_avail, date:str=None):
    """ Return the suggest price for a double eco according to total_avail
    can be also according to <date>: dd/mm/yyyy"""
    dt_date = datetime.strptime(date, "%d/%m/%Y")

    # Nouvelle façon: 
    # < 5 chambres: on prend le moins cher - 1€
    # 5 < ... < 10: on prend la moyenne entre ibis et campanile
    # 10 < ... < 20: on prend casabella
    # 20 < .. : on prend casabella + 20%
    # Et on ajoute le % des dates spéciales
    with open(os.path.join(C, "HotelRates", "data.csv"), mode="r") as price_file:
        csv_reader = csv.DictReader(price_file)
        for row in csv_reader:
            if row["date"] == date:
                ibis = row["ibis"]
                campanile = row["campanile"]
                casabella = row["casabella"]
                break
        else:
            raise(Exception(f"Dans price.py fonction priceDoubleStd, pas de date {date} dans le fichier data.csv"))
    # int les trois pour virer ce qui sert à rien:
    valid_value = []
    maxi = 70
    try:
        ibis = int(ibis)
        valid_value.append(ibis)
        maxi = max(maxi, ibis)
    except ValueError:
        pass
    try:
        campanile = int(campanile)
        valid_value.append(campanile)
        maxi = max(maxi, campanile)
    except ValueError:
        pass
    try:
        casabella = int(casabella)
        maxi = max(maxi, casabella)
    except ValueError:
        pass
    if not valid_value:
        valid_value = [55]

    taux_occupation = 1 - total_avail/TOTAL_ROOMS
    if taux_occupation < 0.15:
        res = min(valid_value) - 1
    elif taux_occupation < 0.3:  
        res = statistics.mean(valid_value)
    elif taux_occupation < 0.6:  
        res = maxi
    elif taux_occupation < 1:
        res = maxi * 1.20
    else:
        res = max(maxi, 90)
    return res * (1 + special_dates.get(date, 0) / 100)
    #  
    # if date in special_dates:
    #     ### Le prix selon les dates spéciaux.
    #     rate = special_dates[date]
    #     if isinstance(rate, Rate):
    #         result_rate = calcul_price(total_avail=total_avail, rate=rate)
    #     else:
    #         rate = switch_rate.get(dt_date.month, low_season)
    #         add_percent = special_dates[date]
    #         result_rate = calcul_price(total_avail=total_avail, rate=rate, add_percent=add_percent)
    # else:
    #     ### Déterminer le prix selon les TARIFS saisonniers
    #     rate = switch_rate.get(dt_date.month, low_season)
    #     result_rate = calcul_price(total_avail=total_avail, rate=rate)

    # def calculPriceWithXotelo():
    #     ### Déterminer le prix selon les autres hôtels avec xotelo ###
    #     date_ = datetime.strptime(date, "%d/%m/%Y")
    #     prices_low = (cost("g1380878-d2184159", date_), cost(ibis_budget_mouans, date_), cost("g662774-d488551", date_))  # poste, ibis, campanile
    #     price_best_western = cost("g187224-d248537", date_)
    #     logging.info(f"{date}: {prices_low} (poste, ibis, campanile)")
    #     price = max(min(price for price in prices_low if price != 0), 50)
    #     taux_occupation = 1 - total_avail/TOTAL_ROOMS
    #     if taux_occupation < 0.3:  # < 10%
    #         return price - 2
    #     elif taux_occupation < 0.6:  
    #         return price
    #     elif taux_occupation < 1:
    #         return max(price_best_western, 90) * 0.85
    #     else:
    #         return max(price_best_western, 90)
    
    # result = calculPriceWithXotelo()

    # logging.info(f"prix rate, prix autres hotels: {result_rate} / {result}")
    # if date in special_dates:
    #     res = max(result, result_rate)
    #     assert res >= 40
    #     return res
    # else:
    #     if result == 0:
    #         assert result_rate >= 40
    #         return result_rate
    #     else:
    #         assert result >= 40
    #         return result

def priceTripleStd(total_avail, date:str=None):
    """ Return the suggest price for a triple eco according to total_avail 
    can be also according to <date>: dd/mm/yyyy"""
    # date_ = datetime.strptime(date, "%d/%m/%Y")
    # price = cost("g666506-d1071475", date_)  # ibis
    # price_double_eco = priceDoubleStd(total_avail, date)
    # logging.debug(f"{date_} : {price}")
    # if price == 0:
    #     result = price_double_eco * 1.15
    # else:
    #     result = max(price_double_eco, price)
    # assert result >= 40
    # if date in special_dates:
    #     return result * 1.15

    return priceDoubleStd(total_avail, date) * 1.1


def matchPrice10Low(price: float, base=50):
    """Decrease the price of 10% except if it’s between 50 and 60. (base and base+10)
    Then apply a (price - 50) / 2 + 50
    Utilisé surtout pour calculer le prix de la chambre single lorsque le prix est inférieur à 60
    Utilisé pour calculer le prix d’une chambre en direct à partir de son prix OTA si inférieur au prix de base + 10
    """
    # TODO: to be test
    if price <= base:
        return round(price)
    elif price < base + 10:
        return round((price - base) / 2 + base)
    else:
        return round(price / 1.1)


def test_calcul_price_increase_set():
    rate1 = Rate(n_rooms=11, n_room_increase=3, min_price=40, increase=5, max_price=None)
    rate2 = Rate(n_rooms=12, n_room_increase=4, min_price=40, increase=5, max_price=None)

    assert calcul_price(11, rate1, 0) == 40
    assert calcul_price(10, rate1, 3) == 41
    assert calcul_price(9, rate1, 0) == 40
    assert calcul_price(8, rate1, 0) == 42
    assert calcul_price(6, rate1, 0) == 42
    assert calcul_price(2, rate1, 0) == 46
    assert calcul_price(1, rate1, 0) == 46


    assert calcul_price(12, rate2, 0) == 40
    assert calcul_price(10, rate2, 0) == 40
    assert calcul_price(9, rate2, 0) == 40
    assert calcul_price(8, rate2, 0) == 42
    assert calcul_price(5, rate2, 0) == 42
    assert calcul_price(4, rate2, 0) == 44
    assert calcul_price(1, rate2, 0) == 44


def test_calcul_price_max_price_set():
    rate1 = Rate(n_rooms=11, n_room_increase=3, min_price=40, increase=None, max_price=69)  # ~19,93%
    rate2 = Rate(n_rooms=12, n_room_increase=4, min_price=40, increase=None, max_price=69)  # ~31.33%

    assert calcul_price(11, rate1, 0) == 40
    assert calcul_price(10, rate1, 0) == 40
    assert calcul_price(9, rate1, 0) == 40

    assert calcul_price(8, rate1, 0) == 47
    assert calcul_price(6, rate1, 0) == 47

    assert calcul_price(5, rate1, 0) == 57
    assert calcul_price(3, rate1, 0) == 57
    
    assert calcul_price(2, rate1, 0) == 69
    assert calcul_price(1, rate1, 0) == 69

    assert calcul_price(12, rate2, 0) == 40
    assert calcul_price(11, rate2, 0) == 40
    assert calcul_price(9, rate2, 0) == 40

    assert calcul_price(8, rate2, 0) == 52
    assert calcul_price(5, rate2, 0) == 52

    assert calcul_price(4, rate2, 0) == 69
    assert calcul_price(1, rate2, 0) == 69

if __name__ == "__main__":
    pass