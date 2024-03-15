class Trade:
    def __init__(self, trade_id, trade_open_time, trade_open_price, trade_quantity, trade_instrument, trade_type):
        self.trade_id = trade_id
        self.trade_open_time = trade_open_time
        self.trade_open_price = trade_open_price
        self.trade_quantity = trade_quantity
        self.trade_instrument = trade_instrument
        self.trade_type = trade_type
    
    def close_trade(self, trade_close_time, trade_close_price):
        self.trade_close_time = trade_close_time
        self.trade_close_price = trade_close_price
        self.trade_profit = self.trade_close_price - self.trade_open_price if self.trade_type == "long" else self.trade_open_price - self.trade_close_price