class Trade:
    def __init__(
        self, trade_id, trade_open_price, trade_quantity, trade_instrument, trade_type
    ):
        self.trade_id = trade_id
        self.trade_open_price = trade_open_price
        self.trade_quantity = trade_quantity
        self.trade_instrument = trade_instrument
        self.trade_type = trade_type

    def close_trade(self, trade_close_time, trade_close_price, pl):
        self.trade_close_time = trade_close_time
        self.trade_close_price = trade_close_price
        self.trade_profit = pl

    def to_string_closed(self):
        return f"Trade ID: {self.trade_id}\nInstrument: {self.trade_instrument}\nType: {self.trade_type}\nQuantity: {self.trade_quantity}\nOpen Price: {self.trade_open_price}\nClose Price: {self.trade_close_price}\nProfit: {self.trade_profit}"

    def to_string_opened(self):
        return f"Trade ID: {self.trade_id}\nInstrument: {self.trade_instrument}\nType: {self.trade_type}\nQuantity: {self.trade_quantity}\nOpen Price: {self.trade_open_price}"
