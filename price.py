import sys
import math
from dataclasses import dataclass

increase = 5  # in %
base_price = 49
min_price = 47
max_price = 69
n_rooms = 26
n_room_min_price = 3
n_room_increase = 4

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


def calcul_price(total_avail: int, date: str=None, rate: Rate=None, add_percent: float=0):
    rate = rate or low_season  # if not rate

    if rate.max_price:
        n_rate = rate.n_rooms // rate.n_room_increase
        if rate.n_rooms % rate.n_room_increase == 0:  # évite les cas où le nombre de chambre peut être divisé par le nombre de chambre à augmenter ce qui faussent les résultats
           n_rate -= 1
        rate.increase = (math.pow(rate.max_price/rate.min_price, 1 / n_rate) - 1) * 100
    
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
        if rate.n_rooms % rate.n_room_increase == 0:  # évite les cas où le nombre de chambre peut être divisé par le nombre de chambre à augmenter ce qui faussent les résultats
           n_rate -= 1
        rate.increase = (math.pow(rate.max_price/rate.min_price, 1 / n_rate) - 1) * 100
    
    if rate.increase:
            prices = [rate.min_price]
            for i in range(rate.n_rooms // rate.n_room_increase):
                prices.append(prices[-1] * (1 + rate.increase/100))
    print(prices)

def price_for_double_eco(total_avail, date=None):
    """ Return the suggest price for a double eco according to total_avail 
    can be also according to <date>: dd/mm/yyyy"""
    return calcul_price(total_avail=total_avail, date=date, rate=low_season)


def test_calcul_price_increase_set():
    rate1 = Rate(n_rooms=11, n_room_increase=3, min_price=40, increase=5, max_price=None)
    rate2 = Rate(n_rooms=12, n_room_increase=4, min_price=40, increase=5, max_price=None)

    assert calcul_price(11, None, rate1, 0) == 40
    assert calcul_price(10, None, rate1, 3) == 41
    assert calcul_price(9, None, rate1, 0) == 40
    assert calcul_price(8, None, rate1, 0) == 42
    assert calcul_price(6, None, rate1, 0) == 42
    assert calcul_price(2, None, rate1, 0) == 46
    assert calcul_price(1, None, rate1, 0) == 46


    assert calcul_price(12, None, rate2, 0) == 40
    assert calcul_price(10, None, rate2, 0) == 40
    assert calcul_price(9, None, rate2, 0) == 40
    assert calcul_price(8, None, rate2, 0) == 42
    assert calcul_price(5, None, rate2, 0) == 42
    assert calcul_price(4, None, rate2, 0) == 44
    assert calcul_price(1, None, rate2, 0) == 44


def test_calcul_price_max_price_set():
    rate1 = Rate(n_rooms=11, n_room_increase=3, min_price=40, increase=None, max_price=69)  # ~19,93%
    rate2 = Rate(n_rooms=12, n_room_increase=4, min_price=40, increase=None, max_price=69)  # ~31.33%
    # rate.increase = math.pow(rate.max_price/rate.min_price, 1 / (rate.n_rooms // rate.n_room_increase)) - 1

    assert calcul_price(11, None, rate1, 0) == 40
    assert calcul_price(10, None, rate1, 0) == 40
    assert calcul_price(9, None, rate1, 0) == 40
    assert calcul_price(8, None, rate1, 0) == 47
    assert calcul_price(6, None, rate1, 0) == 47
    assert calcul_price(5, None, rate1, 0) == 57
    assert calcul_price(3, None, rate1, 0) == 57
    assert calcul_price(2, None, rate1, 0) == 69
    assert calcul_price(1, None, rate1, 0) == 69

    assert calcul_price(12, None, rate2, 0) == 40
    assert calcul_price(11, None, rate2, 0) == 40
    assert calcul_price(9, None, rate2, 0) == 40

    assert calcul_price(8, None, rate2, 0) == 52
    assert calcul_price(5, None, rate2, 0) == 52

    assert calcul_price(4, None, rate2, 0) == 69
    assert calcul_price(1, None, rate2, 0) == 69

if __name__ == "__main__":
    pass