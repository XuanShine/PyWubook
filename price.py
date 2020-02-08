import sys
import math
from dataclasses import dataclass
from datetime import datetime

special_dates = {  # augmentation en % : 50% => 50
    "21/02/2020" : 5,
    "22/02/2020" : 10,  # Rallye 2 CV
    "23/02/2020" : 5,

    "03/03/2020" : 10,  # Événement inconnu

    "07/03/2020" : 10,  # duathlon Grasse
    # Fête du jasmin
    # Fête de la rose
    # Concours de danse
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


def calcul_price(total_avail: int, rate: Rate=None, add_percent: float=0):
    rate = rate or low_season  # if not rate

    if rate.max_price:
        n_rate = rate.n_rooms // rate.n_room_increase
        if rate.n_rooms % rate.n_room_increase == 0:  # évite les cas où le nombre de chambre peut être divisé par le nombre de chambre à augmenter ce qui faussent les résultats
           n_rate -= 1
        rate.increase = (math.pow(rate.max_price/rate.min_price, 1 / (n_rate - 1)) - 1) * 100
    
    if rate.increase:
            prices = [rate.min_price]
            for i in range(rate.n_rooms // rate.n_room_increase):
                prices.append(prices[-1] * (1 + rate.increase/100))
            
            i = (rate.n_rooms - total_avail) // rate.n_room_increase  # indice de l’augmentation

    res = prices[i] * (1 + add_percent/100)
    assert res >= 40
    return math.floor(res)


def graph_price(rate):
    """Show a list of evolution of price"""
    if rate.max_price:
        n_rate = rate.n_rooms // rate.n_room_increase
        if rate.n_rooms % rate.n_room_increase == 0:
           n_rate -= 1
        rate.increase = (math.pow(rate.max_price/rate.min_price, 1 / n_rate) - 1) * 100
    
    if rate.increase:
            prices = [rate.min_price]
            for i in range(rate.n_rooms // rate.n_room_increase):
                prices.append(math.floor(prices[-1] * (1 + rate.increase/100)))
    print(prices)

def price_for_double_eco(total_avail, date:str=None):
    """ Return the suggest price for a double eco according to total_avail 
    can be also according to <date>: dd/mm/yyyy"""
    dt_date = datetime.strptime(date, "%d/%m/%Y")
    switch_rate = {
        1: Rate(n_rooms=25, n_room_increase=2, min_price=44, increase=10, max_price=None),  # [44, 48, 52, 57, 62, 68, 74, 81, 89]
        2: Rate(n_rooms=25, n_room_increase=2, min_price=47, increase=5, max_price=None),  # [47, 49, 51, 53, 55, 57, 59, 61, 64, 67, 70, 73, 76]
        3: Rate(n_rooms=25, n_room_increase=2, min_price=44, increase=5, max_price=None),  # [44, 46, 48, 50, 52, 54, 56, 58, 60, 63, 66, 69, 72]
        4: Rate(n_rooms=25, n_room_increase=4, min_price=53, increase=6, max_price=None),  # [53, 56, 59, 62, 65, 68, 72, 76, 80]
        5: Rate(n_rooms=25, n_room_increase=4, min_price=54, increase=None, max_price=74),  # [54, 56, 58, 60, 62, 64, 66, 68, 70]
        6: Rate(n_rooms=25, n_room_increase=4, min_price=54, increase=None, max_price=84),  # [54, 57, 60, 63, 66, 69, 72, 76, 80]
        7: Rate(n_rooms=25, n_room_increase=4, min_price=59, increase=None, max_price=99),
        8: Rate(n_rooms=25, n_room_increase=4, min_price=74, increase=None, max_price=114),
        9: Rate(n_rooms=25, n_room_increase=4, min_price=54, increase=None, max_price=84),
        10: Rate(n_rooms=25, n_room_increase=4, min_price=44, increase=None, max_price=64),
        11: Rate(n_rooms=25, n_room_increase=4, min_price=44, increase=None, max_price=64),
        12: Rate(n_rooms=25, n_room_increase=3, min_price=44, increase=None, max_price=64),
        # rate.increase = (math.pow(rate.max_price/rate.min_price, 1 / n_rate) - 1) * 100
    }
    rate = switch_rate.get(dt_date.month, low_season)
    # TODO: gestion des dates spéciaux
    return calcul_price(total_avail=total_avail, rate=rate)


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