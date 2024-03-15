import logging
import requests
import pandas as pd
import time
from datetime import datetime
from datetime import timezone


class TradingBot: 
    def __init__(self, instrument, granularity, practice, count):
        self.instrument = instrument
        self.granularity = granularity
        self.practice = practice
        self.count = count

        self.account_id = "101-004-25172303-001"
        self.oanda_authorization = "Bearer 355e3f854bfe5cd14c1ae71e71cb723e-b1bdecc6d4a9ac5023b66104c9f48863"
        self.oanda_base_url = "https://api-fxpractice.oanda.com/v3/"

        self.run_bot()

    
    def run_bot(self):
        while True:
            print("Fetching latest candle...")
            candles, status_code = self.get_candles(self.instrument, self.granularity, self.count)
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
                last_complete_candle, status_code = self.get_last_complete_candle(self.instrument, self.granularity)
                if status_code != 200 or last_complete_candle.empty:
                    time.sleep(1)  
                    continue

                new_candle_time = pd.to_datetime(last_complete_candle.name)
                if new_candle_time != pd.to_datetime(last_candle_time):
                    closing_price = last_complete_candle['mid_c']  # Assuming you're interested in the mid closing price
                    print(f"New candle detected at {new_candle_time}! Closing Price: {closing_price}")
                    # Process the new candle here (if any processing or decision-making is required)
                    break  # Exit the inner loop since a new candle is detected

            print("Processing complete. Waiting for next cycle...")
            # After processing the new candle, the outer loop continues, fetching the next set of candles after a wait.




    # def ref_run_bot(self):
    #     candles = self.get_candles(self.instrument, self.granularity, 5)
    #     last_candle = candles["candles"][-1].time
        
    #     wait_time = calculate_wait_time(last_candle)

    #     while True:
    #         time.sleep(wait_time)
    #         while True:
    #             last_complete_candle = self.get_candle()
    #             if last_complete_candle.time != last_candle:
    #                 # check for trade
    #                 #trade if trade
    #                 wait_time = calculate_wait_time(last_complete_candle)
    #                 break
    #             else:
    #                 pass


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

bot = TradingBot("ETH_USD", "M1", True, 5)
    

        



    









    