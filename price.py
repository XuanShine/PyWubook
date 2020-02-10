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
    switch_rate = {
        1: Rate(n_rooms=25, n_room_increase=2, min_price=44, increase=None, max_price=74),  # 44 48 53 58 64 70 77 85 94 103 114 125 138
        2: Rate(n_rooms=25, n_room_increase=2, min_price=47, increase=None, max_price=74),  # 47 48 50 52 54 56 58 61 63 66 68 71 74
        3: Rate(n_rooms=25, n_room_increase=2, min_price=44, increase=5, max_price=None),   # 44 46 48 50 53 56 58 61 65 68 71 75 79
        4: Rate(n_rooms=25, n_room_increase=4, min_price=53, increase=6, max_price=None),   # 53 56 59 63 66 70 75
        5: Rate(n_rooms=25, n_room_increase=4, min_price=54, increase=None, max_price=74),  # 54 56 59 63 66 70 74
        6: Rate(n_rooms=25, n_room_increase=4, min_price=54, increase=None, max_price=84),  # 54 58 62 67 72 78 84
        7: Rate(n_rooms=25, n_room_increase=4, min_price=59, increase=None, max_price=99),  # 59 64 70 76 83 90 98
        8: Rate(n_rooms=25, n_room_increase=4, min_price=74, increase=None, max_price=114), # 74 79 85 91 98 106 114
        9: Rate(n_rooms=25, n_room_increase=4, min_price=54, increase=None, max_price=84),  # 54 58 62 67 72 78 84
        10: Rate(n_rooms=25, n_room_increase=4, min_price=44, increase=None, max_price=64), # 44 46 49 53 56 60 63
        11: Rate(n_rooms=25, n_room_increase=4, min_price=44, increase=None, max_price=64), # 44 46 49 53 56 60 63
        12: Rate(n_rooms=25, n_room_increase=3, min_price=44, increase=None, max_price=64), # 44 46 48 50 53 55 58 61 63
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