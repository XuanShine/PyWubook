import sys

increase = 5  # in %
base_price = 49
min_price = 46
max_price = 69
n_rooms = 26
n_room_min_price = 3
n_room_increase = 4

def graph_price():
    """Show a list of evolution of price"""
    prices = [base_price]
    for _ in range(n_rooms // n_room_increase + 1):
        prices.append(round(prices[-1] * (1+increase*0.01)))
    print(prices)

def price_for_double_eco(total_avail):
    """ Return the suggest price for a double eco according to total_avail """
    if total_avail > n_rooms - n_room_min_price:
        return min_price
    elif total_avail <= 0:
        return max_price

    prices = [base_price]
    for i in range(n_rooms // n_room_increase + 1):
        prices.append(prices[-1] * (1 + increase/100))
    
    i = (n_rooms - n_room_min_price - total_avail) // n_room_increase  # indice de l’augmentation

    return prices[i]

def test_price_for_double_eco():
    """For
        increase = 8  # in %
        base_price = 44
        min_price = 39
        max_price = 100
        n_rooms = 30
        n_room_min_price = 2
    """

    assert price_for_double_eco(30) == 39
    assert price_for_double_eco(31) == 39
    assert price_for_double_eco(29) == 39

    assert price_for_double_eco(28) == 44
    assert price_for_double_eco(26) == 44

    assert price_for_double_eco(25) == 47.52
    assert price_for_double_eco(23) == 47.52

    assert price_for_double_eco(22) - 51.31 <= 0.1
    assert price_for_double_eco(20) - 51.31 <= 0.1

    assert price_for_double_eco(3) - 81.43 <= 0.1
    assert price_for_double_eco(2) - 81.43 <= 0.1

    assert price_for_double_eco(1) - 87.95 <= 0.1

    assert price_for_double_eco(0) == 100
    assert price_for_double_eco(-1) == 100

    
if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "graph":
            graph_price()
        else:
            print(price_for_double_eco(int(sys.argv[1])))