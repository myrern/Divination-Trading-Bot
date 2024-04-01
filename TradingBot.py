import logging
import pandas as pd
from Oanda import Oanda
from Strategies import Strategies
from Trade import Trade
import multiprocessing
import pytz
from datetime import datetime, timedelta, time, timezone  # Import the time class explicitly from datetime
import time as time_module

logging.basicConfig(level=logging.INFO)

class TradingBot:
    def __init__(self, practice, count, strategy):
            self.practice = practice
            self.count = count
            self.strategy = strategy
            self.strategies = Strategies()
            self.oanda = Oanda(practice)
            self.account_id = "101-004-25172303-001"
            self.oanda_authorization = "Bearer 355e3f854bfe5cd14c1ae71e71cb723e-b1bdecc6d4a9ac5023b66104c9f48863"
            self.oanda_base_url = "https://api-fxpractice.oanda.com/v3/"
            self.time_zone = pytz.timezone(strategy['time_zone'])
            self.market_open = strategy['market_open']
            self.market_close = strategy['market_close']

            self.run_bot()

    def run_bot(self):
        current_strategy = self.strategy
        self.instrument = current_strategy["asset"]
        self.granularity = current_strategy["granularity"]
        self.time_zone = current_strategy["time_zone"]
        self.check_for_open_trades(current_strategy)

        while True:
            if self.is_market_open():
                print("Fetching latest candle for " + self.instrument + "...")
                candles, status_code = self.get_candles(self.instrument, self.granularity, self.count)

                if status_code != 200 or candles.empty:
                    logging.error(f"Error getting candles: {status_code}")
                    time_module.sleep(60)  # Wait a minute before retrying
                    continue

                last_candle_time = candles.index[-1]
                wait_time = self.calculate_wait_time(last_candle_time)
                print(f"Waiting for {wait_time} seconds before starting constant checks for " + self.instrument + "...")
                time_module.sleep(wait_time)

                print("Entering constant checking phase. Checking for a new candle...")
                start_check_time = datetime.now(timezone.utc)
                check_counter = 0
                while (datetime.now(timezone.utc) - start_check_time).total_seconds() <= 30:
                    print("Checking for new candle now for " + self.instrument + "...")
                    last_complete_candle, status_code = self.get_candles(self.instrument, self.granularity, 1)
                    if status_code != 200 or last_complete_candle.empty:
                        time_module.sleep(1)
                        continue

                    new_candle_time = pd.to_datetime(last_complete_candle.index)
                    if new_candle_time != pd.to_datetime(last_candle_time):
                        closing_price = last_complete_candle["mid_c"]
                        print(f"New candle detected at {new_candle_time}! Closing Price: {closing_price} for " + self.instrument + "...")
                        candles = candles._append(last_complete_candle, ignore_index=False)
                        self.check_for_trade(candles)
                        break  # Exit the inner loop since a new candle is detected

                    check_counter += 1
                    if check_counter % 10 == 0:
                        time_module.sleep(2)  # Wait for 1 second after every 10 checks to avoid rate limiting
                        print("Waiting for new candle..." + self.instrument + "...")
            else:
                sleep_duration = self.calculate_sleep_duration()
                print(f"Market is closed. Sleeping for {sleep_duration} seconds until market opens.")
                time_module.sleep(sleep_duration)

            print("Processing complete. Waiting for next cycle...")
            # After processing the new candle, the outer loop continues, fetching the next set of candles after a wait.
    
    def is_market_open(self):
        ny_time_zone = pytz.timezone(self.time_zone)
        local_now = datetime.now(pytz.utc).astimezone(ny_time_zone)

        market_open_time = time(17, 5)  # 17:05 NY time
        market_close_time = time(16, 59)  # 16:59 NY time
        
        # Check if today is Sunday and time is past market open
        if local_now.weekday() == 6 and local_now.time() >= market_open_time:
            return True
        # Check if today is Friday and time is before market close
        elif local_now.weekday() == 4 and local_now.time() <= market_close_time:
            return True
        # From Monday to Thursday, market is considered always open
        elif 0 <= local_now.weekday() < 4:
            return True
        # Covers the case for Saturday and Friday post-market close
        return False

    def calculate_sleep_duration(self):
        ny_time_zone = pytz.timezone(self.time_zone)
        now = datetime.now(pytz.utc).astimezone(ny_time_zone)
        market_open_time = time(17, 5)  # Sunday 17:05 NY time
        
        if now.weekday() >= 5:  # It's Friday after market close or any time on Saturday
            next_open = now + timedelta(days=(6-now.weekday()) % 7)  # Next Sunday
            next_open = next_open.replace(hour=market_open_time.hour, minute=market_open_time.minute, second=0, microsecond=0)
            if next_open <= now:  # If it's already past the opening time, adjust to the next week
                next_open += timedelta(days=7)
        else:
            # It's Sunday before the market opens
            next_open = now.replace(hour=market_open_time.hour, minute=market_open_time.minute, second=0, microsecond=0)
            if next_open <= now:
                next_open += timedelta(days=1)  # Move to the next day
        
        sleep_duration = (next_open - now).total_seconds()
        return max(0, sleep_duration)

    def check_for_trade(self, candles):
        # Implement your trade logic here
        strategy = self.strategy
        signal = self.strategies.get_signal(strategy, candles)
        last_trade = strategy["last_trade"]
        if signal == 1:
            self.go_long(strategy)
        elif signal == -1:
            self.go_short(strategy)
        elif signal == 0:
            self.go_netrual(strategy)
        else:
            print(f"No trade signal for {strategy['asset']}")
            print("-----------------------------")

    def go_long(self, strategy):
        instrument = strategy["asset"]
        units = strategy["units"]
        last_trade = strategy["last_trade"]

        # Go netrual if current position is short
        if strategy["current_position"] == -1:
            self.go_netrual(strategy)

        status_code, trade = self.oanda.long_asset(instrument, units)
        if status_code != 201:
            print(f"Failed to open long trade, status code: {status_code}")
            return
        
        strategy["current_position"] = 1
        strategy["last_trade"] = trade

    def go_short(self, strategy):
        instrument = strategy["asset"]
        units = strategy["units"]
        last_trade = strategy["last_trade"]

        # Go netrual if current position is long
        if strategy["current_position"] == 1:
            self.go_netrual(strategy)

        status_code, trade = self.oanda.short_asset(instrument, units)
        if status_code != 201:
            print(f"Failed to open short trade, status code: {status_code}")
            return
        
        strategy["current_position"] = -1
        strategy["last_trade"] = trade

    def go_netrual(self, strategy):
        last_trade = strategy["last_trade"]
        status_code, trade = self.oanda.close_trade_fully(last_trade)
        if status_code != 200:
            print(f"Failed to close trade, status code: {status_code}")
            return
        strategy["current_position"] = 0
        strategy["last_trade"] = trade
        strategy["trade_history"].append(trade)

    def check_for_open_trades(self, strategy):
        print("-----------------------------")
        print("Checking for open trades...")
        response, status_code = self.oanda.get_open_trades()  # Unpack the tuple into response and status_code
        if status_code == 200:  # Check if the request was successful
            open_trades = response["trades"]  # Access 'trades' from the response dictionary
            for trade in open_trades:
                current_units = float(trade["currentUnits"])  # Convert currentUnits to float
                if trade["instrument"] == strategy["asset"]:
                    strategy["current_position"] = 1 if current_units > 0 else -1
                    strategy["last_trade"] = Trade(
                        trade["id"],
                        trade["price"],
                        current_units,
                        trade["instrument"],
                        "long" if current_units > 0 else "short",
                    )
                    
                    print(f"Found open trade: {strategy['last_trade'].to_string_opened()}")
                    print("-----------------------------")
                    return
            print("No open trades found.")
            print("-----------------------------")
        else:
            
            print(f"Failed to get open trades, status code: {status_code}")
            print("-----------------------------")


    def calculate_wait_time(self, last_candle, start_candle_fetch=2):
        last_candle_time = pd.to_datetime(last_candle)
        granularity_seconds = self.granularity_to_seconds(self.granularity)
        next_candle_time = last_candle_time + pd.Timedelta(seconds=granularity_seconds)
        current_time = pd.to_datetime("now", utc=True)  # Ensure current time is in UTC
        wait_time = (
            next_candle_time - current_time
        ).total_seconds() - start_candle_fetch
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
        candle_df = self.oanda.get_candles(instrument, granularity, count)

        if candle_df.empty:
            return pd.DataFrame(), 404
        return candle_df, 200

    def get_last_complete_candle(self, instrument, granularity):
        candle, status_code = self.get_candles(instrument, granularity, 1)
        if candle.shape == 0 or status_code != 200:
            return pd.DataFrame(), status_code
        else:
            return candle.iloc[-1], status_code


def start_bot_for_strategy(strategy):
    bot = TradingBot(True, 20, strategy)

if __name__ == '__main__':
    strategies_list = [
        {
            "strategy_name": "IBS",
            "current_position": 0,
            "asset": "AUD_USD",
            "units": 50,
            "last_trade": None,
            "trade_history": [],
            "ibs_low_threshold": 0.2,
            "ibs_high_threshold": 0.8,
            "granularity": "M5",
            "time_zone": "America/New_York",
            "market_open": {"day": 6, "hour": 17, "minute": 5},  # Sunday 17:05 NY time
            "market_close": {"day": 4, "hour": 16, "minute": 59},  # Friday 16:59 NY time
        },
        {
            "strategy_name": "RSI",
            "current_position": 0,
            "asset": "EUR_USD",
            "units": 50,
            "last_trade": None,
            "trade_history": [],
            "rsi_low_threshold": 30,
            "rsi_high_threshold": 70,
            "granularity": "M1",
            "time_zone": "America/New_York",
            "market_open": {"day": 6, "hour": 17, "minute": 5},  # Sunday 17:05 NY time
            "market_close": {"day": 4, "hour": 16, "minute": 59},  # Friday 16:59 NY time
        },
        {
            "strategy_name": "IBS",
            "current_position": 0,
            "asset": "NAS100_USD",
            "units": 0.1,
            "last_trade": None,
            "trade_history": [],
            "ibs_low_threshold": 0.2,
            "ibs_high_threshold": 0.8,
            "granularity": "H1",
            "time_zone": "America/Chicago",
            "market_open": {"day": 6, "hour": 17, "minute": 1},  # Sunday 17:01 Chicago time
            "market_close": {"day": 4, "hour": 15, "minute": 59},  # Friday 15:59 Chicago time

        }
        # Add more strategies here
    ]

    processes = []
    for strategy in strategies_list:
        p = multiprocessing.Process(target=start_bot_for_strategy, args=(strategy,))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()  # Wait for all processes to complete