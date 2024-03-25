import logging
import requests
import pandas as pd
import time
from datetime import datetime
from datetime import timezone
from Strategies import Strategies
from Oanda import Oanda

logging.basicConfig(level=logging.INFO)

class TradingBot: 
    def __init__(self, instrument, granularity, practice, count):
        self.instrument = instrument
        self.granularity = granularity
        self.practice = practice
        self.count = count
        self.strategies = Strategies()
        self.oanda = Oanda(practice)

        self.account_id = "101-004-25172303-001"
        self.oanda_authorization = "Bearer 355e3f854bfe5cd14c1ae71e71cb723e-b1bdecc6d4a9ac5023b66104c9f48863"
        self.oanda_base_url = "https://api-fxpractice.oanda.com/v3/"
        self.strategies_list = [{"strategy_name": "IBS", "current_position": 0, "asset": "JP225_USD", "units": 1, "last_trade" : None , "ibs_low_threshold": 0.2, "ibs_high_threshold": 0.8}]

        self.run_bot()        

    
    def run_bot(self):
        while True:
            print("Fetching latest candle...")
            candles, status_code = self.get_candles(self.instrument, self.granularity, self.count)
            #print(candles.info())
            print(candles.tail())
            if status_code != 200 or candles.empty:
                logging.error(f"Error getting candles: {status_code}")
                time.sleep(60)  # Wait a minute before retrying
                continue

            last_candle_time = candles.index[-1]
            wait_time = self.calculate_wait_time(last_candle_time)
            print(f"Waiting for {wait_time} seconds before starting constant checks.")
            time.sleep(wait_time)

            print("Entering constant checking phase. Checking for a new candle...")
            start_check_time = datetime.now(timezone.utc)
            while (datetime.now(timezone.utc) - start_check_time).total_seconds() <= 30:
                print("Checking for new candle now...")
                last_complete_candle, status_code = self.get_candles(self.instrument, self.granularity, 1)
                if status_code != 200 or last_complete_candle.empty:
                    time.sleep(1)  
                    continue

                new_candle_time = pd.to_datetime(last_complete_candle.index)
                if new_candle_time != pd.to_datetime(last_candle_time):
                    closing_price = last_complete_candle[
                        'mid_c']  # Assuming you're interested in the mid closing price
                    print(f"New candle detected at {new_candle_time}! Closing Price: {closing_price}")
                    #print(last_complete_candle)
                    candles = candles._append(last_complete_candle, ignore_index=False)
                    # check for trade
                    self.check_for_trade(candles)
                    # Process the new candle here (if any processing or decision-making is required)
                    break  # Exit the inner loop since a new candle is detected

            print("Processing complete. Waiting for next cycle...")
            # After processing the new candle, the outer loop continues, fetching the next set of candles after a wait.
    
    def check_for_trade(self, candles):
        # Implement your trade logic here
        for strategy in self.strategies_list:
            signal = self.strategies.get_signal(strategy, candles)
            last_trade = strategy["last_trade"]
            if signal == 1:
                self.go_long(strategy)
                print(f"Going long on {strategy['asset']}")
                strategy["current_position"] = 1
            elif signal == -1:
                self.go_short(strategy)
                print(f"Going short on {strategy['asset']}")
                strategy["current_position"] = -1
            elif signal == 0:
                self.go_netrual(strategy)
                print(f"Closing trade on {strategy['asset']}")
                strategy["current_position"] = 0
            else:
                print(f"No trade signal for {strategy['asset']}")
                continue

    def go_long(self, strategy):
        instrument = strategy["asset"]
        units = strategy["units"]
        status_code, trade = self.oanda.long_asset(instrument, units)
        strategy["last_trade"] = trade

    def go_short(self, strategy):
        instrument = strategy["asset"]
        units = strategy["units"]
        self.oanda.short_asset(instrument, units)

    def go_netrual(self, strategy):
        trade_id = strategy["last_trade"]
        self.oanda.close_trade_fully(trade_id)

    def calculate_wait_time(self, last_candle, start_candle_fetch=2):
        last_candle_time = pd.to_datetime(last_candle)
        granularity_seconds = self.granularity_to_seconds(self.granularity)
        next_candle_time = last_candle_time + pd.Timedelta(seconds=granularity_seconds)
        current_time = pd.to_datetime("now", utc=True)  # Ensure current time is in UTC
        wait_time = (next_candle_time - current_time).total_seconds() - start_candle_fetch
        return max(wait_time, 0)

    def granularity_to_seconds(self, granularity):
        granularity_to_seconds_dict = {
            "S5": 5,
            "S10": 10,
            "S15": 15,
            "S30": 30,
            "M1": 60,
            "M2": 120,
            "M3": 180,
            "M4": 240,
            "M5": 300,
            "M10": 600,
            "M15": 900,
            "M30": 1800,
            "H1": 3600,
            "H2": 7200,
            "H3": 10800,
            "H4": 14400,
            "H6": 21600,
            "H8": 28800,
            "H12": 43200,
            "D": 86400,
            "W": 604800,
            "M": 2592000,
        }
        return granularity_to_seconds_dict[granularity]
     
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

        return candle_df, 200

    def get_last_complete_candle(self, instrument, granularity):
        candle, status_code = self.get_candles(instrument, granularity, 1)
        if candle.shape == 0 or status_code != 200:
            return pd.DataFrame(), status_code
        else:
            return candle.iloc[-1], status_code
        
    def granularity_to_seconds(self, granularity):
        granularity_to_seconds_dict = {
            "S5": 5,
            "S10": 10,
            "S15": 15,
            "S30": 30,
            "M1": 60,
            "M2": 120,
            "M3": 180,
            "M4": 240,
            "M5": 300,
            "M10": 600,
            "M15": 900,
            "M30": 1800,
            "H1": 3600,
            "H2": 7200,
            "H3": 10800,
            "H4": 14400,
            "H6": 21600,
            "H8": 28800,
            "H12": 43200,
            "D": 86400,
            "W": 604800,
            "M": 2592000,
        }
        return granularity_to_seconds_dict[granularity]

bot = TradingBot("JP225_USD", "M1", True, 5)