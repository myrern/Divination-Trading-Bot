import requests
import pandas as pd
import logging
from Trade import Trade

class Oanda:

    def __init__(self, practice=True):
        self.account_id = "101-004-18657494-001" if practice else "101-004-18657494-001"
        self.oanda_authorization = f"Bearer 02791443d8f10d0841376bfcb384553a-060328043185e16039e68b0738b42a96" if practice else f"Bearer 02791443d8f10d0841376bfcb384553a-060328043185e16039e68b0738b42a96"
        self.oanda_base_url = "https://api-fxpractice.oanda.com/v3/" if practice else "https://api-fxtrade.oanda.com/v3/"
    
    def close_trade_fully(self, trade_id):
        close_trade_url = f"{self.oanda_base_url}accounts/{self.account_id}/trades/{trade_id}/close"
        headers = {
            "Authorization": self.oanda_authorization,
            "Content-Type": "application/json",
        }

        try:
            response = requests.put(
                close_trade_url,
                headers=headers,
            )
        except Exception as e:
            # check status code
            status_code = response.status_code
            if status_code == 400:
                logging.error(f"Order specification was invalid: {response.json()}")
                return pd.DataFrame(), 400
            elif status_code == 404:
                logging.error(f"Order specification does not exist: {response.json()}")
                return pd.DataFrame(), 404
            else:
                logging.error(f"Error closing trade: {e}")
                return pd.DataFrame(), 500
        
        return response.status_code, response.json()
    
    def long_asset(self, instrument, units):
        buy_order_url = f"{self.oanda_base_url}accounts/{self.account_id}/orders"
        headers = {
            "Authorization": self.oanda_authorization,
            "Content-Type": "application/json",
        }
        data = {
            "order": {
                "units": units,
                "instrument": instrument,
                "timeInForce": "FOK",
                "type": "MARKET",
                "positionFill": "DEFAULT"
            }
        }

        try:
            response = requests.post(
                buy_order_url,
                headers=headers,
                json=data,
            )

            print(response.json())

        except Exception as e:
            # check status code
            status_code = response.status_code
            if status_code == 400:
                logging.error(f"Order specification was invalid: {response.json()}")
                return pd.DataFrame(), 400
            elif status_code == 404:
                logging.error(f"Order specification does not exist: {response.json()}")
                return pd.DataFrame(), 404
            else:
                logging.error(f"Error buying asset: {e}")
                return pd.DataFrame(), 500
        
        if response.status_code != 201:
            logging.error(f"Error buying asset: {response.json()}")
            return pd.DataFrame(), response.status_code
        response = response.json()
        trade_opened = response["201"]["orderFillTransaction"]["tradeOpened"]
        trade_id = trade_opened["tradeID"]
        price = trade_opened["price"]
        actual_units = trade_opened["units"]

        trade = Trade(trade_id, price, actual_units, instrument, "long")
        print("Trade: ", trade.__dict__)
        return response.status_code, trade
    
    def short_asset(self, instrument, units):
        short_order_url = f"{self.oanda_base_url}accounts/{self.account_id}/orders"
        headers = {
            "Authorization": self.oanda_authorization,
            "Content-Type": "application/json",
        }
        data = {
            "order": {
                "units": -units,
                "instrument": instrument,
                "timeInForce": "FOK",
                "type": "MARKET",
                "positionFill": "DEFAULT"
            }
        }

        try:
            response = requests.post(
                short_order_url,
                headers=headers,
                json=data,
            )
        except Exception as e:
            # check status code
            status_code = response.status_code
            if status_code == 400:
                logging.error(f"Order specification was invalid: {response.json()}")
                return pd.DataFrame(), 400
            elif status_code == 404:
                logging.error(f"Order specification does not exist: {response.json()}")
                return pd.DataFrame(), 404
            else:
                logging.error(f"Error shorting asset: {e}")
                return pd.DataFrame(), 500
        
        return response.status_code, response.json()

    def get_candles(self, instrument, granularity, count):
        candles_url = f"{self.oanda_base_url}instruments/{instrument}/candles"
        headers = {
            "Authorization": self.oanda_authorization
        }
        params = {
            "granularity": granularity,
            "count": count,
            "price": "MBA",
        }

        candle_df_columns = [
            "time",
            "volume",
            "bid_o",
            "bid_h",
            "bid_l",
            "bid_c",
            "ask_o",
            "ask_h",
            "ask_l",
            "ask_c",
            "mid_o",
            "mid_h",
            "mid_l",
            "mid_c",
        ]

        candle_data = []

        try:
            candles = requests.get(
                candles_url,
                headers=headers,
                params=params,
            ).json()["candles"]
        except Exception as e:
            logging.error(f"Error getting candles: {e}")
            return pd.DataFrame(), 500
        
        for candle in candles:
            temp_candle_dict = {
                "time": candle["time"],
                "volume": candle["volume"],
                "bid_o": candle["bid"]["o"],
                "bid_h": candle["bid"]["h"],
                "bid_l": candle["bid"]["l"],
                "bid_c": candle["bid"]["c"],
                "ask_o": candle["ask"]["o"],
                "ask_h": candle["ask"]["h"],
                "ask_l": candle["ask"]["l"],
                "ask_c": candle["ask"]["c"],
                "mid_o": candle["mid"]["o"],
                "mid_h": candle["mid"]["h"],
                "mid_l": candle["mid"]["l"],
                "mid_c": candle["mid"]["c"],
            }

            candle_data.append(temp_candle_dict)

        candle_df = pd.DataFrame(candle_data, columns=candle_df_columns)
        candle_df.set_index("time", inplace=True)

        return candle_df, 200