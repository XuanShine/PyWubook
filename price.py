import sys
import math
from dataclasses import dataclass
from datetime import datetime, date
from HotelRates.xotelo import get_price, ibis_budget_mouans, cost
from statistics import mean
import logging

TOTAL_ROOMS = 27
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
    # ASA GRASSE
    # VTT dans Grasse

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
def min_price_month(month):
    today = datetime.today()
    year = today.year if month >= today.month else today.year + 1
    price = get_price(ibis_budget_mouans, datetime(year, month, 25, 0, 0, 0), datetime(year, month, 26, 0, 0, 0))
    print(f"price({month}/{year}) = {price}")
    return 0.95 * mean(list( 
            filter(lambda x: x >= 50,
                   price)) + [55])


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

def price_for_double_eco(total_avail, date:str=None):
    """ Return the suggest price for a double eco according to total_avail 
    can be also according to <date>: dd/mm/yyyy"""
    dt_date = datetime.strptime(date, "%d/%m/%Y")

    if date in special_dates:
        ### Le prix selon les dates spéciaux.
        rate = special_dates[date]
        if isinstance(rate, Rate):
            result_rate = calcul_price(total_avail=total_avail, rate=rate)
        else:
            rate = switch_rate.get(dt_date.month, low_season)
            add_percent = special_dates[date]
            result_rate = calcul_price(total_avail=total_avail, rate=rate, add_percent=add_percent)
    else:
        ### Déterminer le prix selon les TARIFS saisonniers
        rate = switch_rate.get(dt_date.month, low_season)
        result_rate = calcul_price(total_avail=total_avail, rate=rate)

    ### Déterminer le prix selon les autres hôtels ###
    date_ = datetime.strptime(date, "%d/%m/%Y")
    prices_low = (cost("g1380878-d2184159", date_), cost(ibis_budget_mouans, date_), cost("g662774-d488551", date_))  # poste, ibis, campanile
    price_best_western = cost("g187224-d248537", date_)
    logging.info(f"{date}: {prices_low} (poste, ibis, campanile)")
    price = max(min(price for price in prices_low if price != 0), 50)
    taux_occupation = 1 - total_avail/TOTAL_ROOMS
    if taux_occupation < 0.3:  # < 10%
        result = price - 2
    elif taux_occupation < 0.6:  
        result = price
    elif taux_occupation < 1:
        result = max(price_best_western, 90) * 0.85
    else:
        result = max(price_best_western, 90)
    
    logging.info(f"prix rate, prix autres hotels: {result_rate} / {result}")
    if date in special_dates:
        res = max(result, result_rate)
        assert res >= 40
        return res
    else:
        if result == 0:
            assert result_rate >= 40
            return result_rate
        else:
            assert result >= 40
            return result

def price_for_triple_eco(total_avail, date:str=None):
    """ Return the suggest price for a triple eco according to total_avail 
    can be also according to <date>: dd/mm/yyyy"""
    date_ = datetime.strptime(date, "%d/%m/%Y")
    price = cost("g666506-d1071475", date_)  # ibis
    logging.debug(f"{date_} : {price}")
    if price == 0:
        result = price_for_double_eco(total_avail, date) * 1.15
    else:
        result = price
    assert result >= 40
    if date in special_dates:
        return result * 1.15

    return result


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