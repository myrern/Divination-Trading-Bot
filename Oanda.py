import logging

import pandas as pd
import requests
import time

from Trade import Trade


class Oanda:

    def __init__(self, practice=True):
        self.account_id = "101-004-18657494-001" if practice else "101-004-18657494-001"
        self.oanda_authorization = (
            f"Bearer 02791443d8f10d0841376bfcb384553a-060328043185e16039e68b0738b42a96"
            if practice
            else f"Bearer 02791443d8f10d0841376bfcb384553a-060328043185e16039e68b0738b42a96"
        )
        self.oanda_base_url = (
            "https://api-fxpractice.oanda.com/v3/"
            if practice
            else "https://api-fxtrade.oanda.com/v3/"
        )

    def get_account_details(self):
        account_url = f"{self.oanda_base_url}accounts/{self.account_id}"
        headers = {"Authorization": self.oanda_authorization}

        try:
            response = requests.get(account_url, headers=headers)
        except Exception as e:
            logging.error(f"Error getting account details: {e}")
            return None, 500

        return response.json(), 200
    
    def get_open_trades(self):
        trades_url = f"{self.oanda_base_url}accounts/{self.account_id}/openTrades"
        headers = {"Authorization": self.oanda_authorization}

        try:
            response = requests.get(trades_url, headers=headers)
        except Exception as e:
            logging.error(f"Error getting open trades: {e}")
            return None, 500

        return response.json(), 200


    def close_trade_fully(self, last_trade):
        trade_id = last_trade.trade_id
        close_trade_url = (
            f"{self.oanda_base_url}accounts/{self.account_id}/trades/{trade_id}/close"
        )
        headers = {
            "Authorization": self.oanda_authorization,
            "Content-Type": "application/json",
        }

        try:
            print("----------------------------------------")
            print(f"Closing trade {trade_id}...")
            response = requests.put(
                close_trade_url,
                headers=headers,
            )
        except Exception as e:
            # check status code
            status_code = response.status_code
            if status_code == 400:
                print(f"Order specification was invalid: {response.json()}")
                print("----------------------------------------")
                return pd.DataFrame(), 400
            elif status_code == 404:
                print(f"Order specification does not exist: {response.json()}")
                print("----------------------------------------")
                return pd.DataFrame(), 404
            else:
                print(f"Error closing trade: {e}")
                print("----------------------------------------")
                return pd.DataFrame(), 500

        response = response.json()
        order_fill = response["orderFillTransaction"]

        # if order_fill is empty
        if not order_fill:
            logging.error(f"Order not filled")
            # wait for order to fill

        closed_time = order_fill["time"]
        closed_price = order_fill["price"]
        trade_closed = order_fill["tradesClosed"]
        realized_pl = trade_closed[0]["realizedPL"]

        last_trade.close_trade(closed_time, closed_time, realized_pl)
        print(f"Trade closed:\n{last_trade.to_string_closed()}")
        print("----------------------------------------")
        return 201, last_trade

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
                "positionFill": "DEFAULT",
            }
        }

        try:
            print("----------------------------------------")
            print(f"Going long {units} units of {instrument}...")
            response = requests.post(
                buy_order_url,
                headers=headers,
                json=data,
            )

        except Exception as e:
            # check status code
            status_code = response.status_code
            if status_code == 400:
                print(f"Order specification was invalid: {response.json()}")
                print("----------------------------------------")
                return 400, None
            elif status_code == 404:
                print(f"Order specification does not exist: {response.json()}")
                print("----------------------------------------")
                return 404, None
            elif status_code == 401:
                print(f"Unauthorized: {response.json()}")
                print("----------------------------------------")
                return 401, None
            elif status_code == 403:
                print(f"Forbidden: {response.json()}")
                print("----------------------------------------")
                return 403, None
            elif status_code == 405:
                print(f"Method not allowed: {response.json()}")
                print("----------------------------------------")
                return 405, None
            else:
                print(f"Error buying asset: {e}")
                print("----------------------------------------")
                return 500, None

        if response.status_code != 201:
            print(f"Error buying asset: {response.json()}")
            return response.status_code, None

        response = response.json()

        # Check if 'orderFillTransaction' is in the response
        if "orderFillTransaction" in response:
            order_fill = response["orderFillTransaction"]
            trade_opened = order_fill["tradeOpened"]
            trade_id = trade_opened["tradeID"]
            price = trade_opened["price"]
            actual_units = trade_opened["units"]

            trade = Trade(trade_id, price, actual_units, instrument, "long")
            print(f"Trade opened:\n{trade.to_string_opened()}")
            print("----------------------------------------")
            return 201, trade
        else:
            tries = 0
            while tries < 10:
                print("Waiting for order to fill...")
                orderCreateTransaction = response["orderCreateTransaction"]
                id = orderCreateTransaction["id"]
                # get order
                order = self.get_single_order(id)
                if order["order"]["state"] == "FILLED":
                    transaction_id = order["lastTransactionID"]
                    trade_opened = order["order"]["createTime"]
                    price = order["order"]["price"]
                    units = order["order"]["units"]
                    trade = Trade(
                        transaction_id, trade_opened, price, units, instrument, "long"
                    )
                    return 201, trade
                tries += 1
                time.sleep(1)

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
                "positionFill": "DEFAULT",
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

    def get_single_order(self, order_id):
        headers = {
            "Authorization": self.oanda_authorization,
            "Content-Type": "application/json",
        }
        order = requests.get(
            f"{self.oanda_base_url}accounts/{self.account_id}/orders/{order_id}",
            headers=headers,
        ).json()

        return order

    def get_candles(self, instrument, granularity, count):
        candles_url = f"{self.oanda_base_url}instruments/{instrument}/candles"
        headers = {"Authorization": self.oanda_authorization}
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
            return pd.DataFrame()

        for candle in candles:
            temp_candle_dict = {
                "time": candle["time"],
                "volume": candle["volume"],
                "bid_o": pd.to_numeric(candle["bid"]["o"]),
                "bid_h": pd.to_numeric(candle["bid"]["h"]),
                "bid_l": pd.to_numeric(candle["bid"]["l"]),
                "bid_c": pd.to_numeric(candle["bid"]["c"]),
                "ask_o": pd.to_numeric(candle["ask"]["o"]),
                "ask_h": pd.to_numeric(candle["ask"]["h"]),
                "ask_l": pd.to_numeric(candle["ask"]["l"]),
                "ask_c": pd.to_numeric(candle["ask"]["c"]),
                "mid_o": pd.to_numeric(candle["mid"]["o"]),
                "mid_h": pd.to_numeric(candle["mid"]["h"]),
                "mid_l": pd.to_numeric(candle["mid"]["l"]),
                "mid_c": pd.to_numeric(candle["mid"]["c"]),
            }

            candle_data.append(temp_candle_dict)

        candle_df = pd.DataFrame(candle_data, columns=candle_df_columns)
        candle_df.set_index("time", inplace=True)

        return candle_df
