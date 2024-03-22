from Oanda import Oanda

oanda = Oanda(practice=True)

def test_buy_order():
    response = oanda.long_asset("JP225_USD", 1)
    print(response)

def test_sell_order():
    response = oanda.short_asset("EUR_USD", 1)
    print(response)

def test_close_trade():
    response = oanda.close_trade_fully("1109")
    print(response)

#test_sell_order()
test_buy_order()
#test_close_trade()