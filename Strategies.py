import numpy as np
import pandas as pd

from TechnicalIndicators import TechnicalIndicators


class Strategies:
    def get_signal(self, strategy, candles):
        if strategy["strategy_name"] == "IBS":
            return self.IBS(strategy, candles)
        elif strategy["strategy_name"] == "RSI":
            return self.RSI(strategy, candles)
        elif strategy["strategy_name"] == "IBS_ATR":
            return self.IBS_ATR(strategy, candles)
        
    def IBS_ATR(self, strategy, candles):
        technical_indicators = TechnicalIndicators(candles)
        ibs_low_threshold = strategy["ibs_low_threshold"]
        ibs_high_threshold = strategy["ibs_high_threshold"]
        current_position = strategy["current_position"]

        # Calculate necessary indicators
        candles["IBS"] = technical_indicators.IBS()
        candles["SMA"] = technical_indicators.SMA(period=14, column="mid_c")
        candles["ATR"] = technical_indicators.ATR(period=14)
        candles["10DayReturn"] = candles["mid_c"].pct_change(7)
        long_term_atr = technical_indicators.ATR(period=21)
        atr_mean = candles["ATR"].rolling(window=50).mean()

        # Prolonged bear market detection
        is_prolonged_bear = (
            candles["10DayReturn"].iloc[-2] < -0.02 and
            long_term_atr.iloc[-2] > atr_mean.iloc[-2] * 1.5
        )

        # Cooldown logic
        if is_prolonged_bear:
            candles["cooldown_counter"] = 5  # Reset cooldown counter
        elif "cooldown_counter" in candles and candles["cooldown_counter"].iloc[-1] > 0:
            candles["cooldown_counter"] -= 1
            print("Cooldown active. No trades allowed.")
            return 0  # Hold position during cooldown

        # Determine position based on IBS and ATR
        candles["Position"] = 0  # Default to no position
        if not is_prolonged_bear:
            candles["Position"] = np.where(
                candles["IBS"] < ibs_low_threshold,
                1,  # Long entry signal
                np.where(candles["IBS"] > ibs_high_threshold, -1, 0)  # Exit or short signal
            )

        # Determine trailing stop for exiting long position
        if current_position == 1:
            trailing_stop = candles["mid_c"].iloc[-2] - (1.5 * candles["ATR"].iloc[-2])
            if candles["mid_l"].iloc[-1] < trailing_stop:
                candles["Position"].iloc[-1] = 0  # Exit signal for trailing stop

        # Determine new position
        new_position = candles["Position"].iloc[-1]
        print("-----------------------------")
        print("IBS_ATR Signal: ", new_position)
        print("-----------------------------")

        # Return the appropriate signal based on the change in position
        if new_position == 1 and current_position == 0:
            return 1  # Go long
        elif new_position == -1 and current_position == 0:
            return -1  # Go short (if you want short selling capability)
        elif new_position == 0 and current_position == 1:
            return 0  # Exit long position
        elif new_position == 0 and current_position == -1:
            return 0  # Exit short position
        else:
            return 99  # No action


    
    def RSI(self, strategy, candles):
        technical_indicators = TechnicalIndicators(candles)
        rsi_low_threshold = strategy["rsi_low_threshold"]
        rsi_high_threshold = strategy["rsi_high_threshold"]
        current_position = strategy["current_position"]

        candles["RSI"] = technical_indicators.RSI()

        # Calculate the RSI signal
        candles["Position"] = np.where(
            candles["RSI"] < rsi_low_threshold,
            1,
            np.where(candles["RSI"] > rsi_high_threshold, -1, 0),
        )
        new_position = candles["Position"].iloc[-1]
        print("-----------------------------")
        print("RSI Signal: ", new_position)
        print("-----------------------------")

        if new_position == 1 and current_position == 0:
            return 1
        elif new_position == 1 and current_position == -1:
            return 1
        elif new_position == -1 and current_position == 0:
            return -1
        elif new_position == -1 and current_position == 1:
            return -1
        elif new_position == 0 and current_position == 1:
            return 0
        elif new_position == 0 and current_position == -1:
            return 0
        else:
            99

    def IBS(self, strategy, candles):
        technical_indicators = TechnicalIndicators(candles)
        ibs_low_threshold = strategy["ibs_low_threshold"]
        ibs_high_threshold = strategy["ibs_high_threshold"]
        current_position = strategy["current_position"]

        candles["IBS"] = technical_indicators.IBS()

        # Calculate the IBS signal
        candles["Position"] = np.where(
            candles["IBS"] < ibs_low_threshold,
            1,
            np.where(candles["IBS"] > ibs_high_threshold, -1, 0),
        )
        new_position = candles["Position"].iloc[-1]
        print("-----------------------------")
        print("IBS Signal: ", new_position)
        print("-----------------------------")

        if new_position == 1 and current_position == 0:
            return 1
        elif new_position == 1 and current_position == -1:
            return 1
        elif new_position == -1 and current_position == 0:
            return -1
        elif new_position == -1 and current_position == 1:
            return -1
        elif new_position == 0 and current_position == 1:
            return 0
        elif new_position == 0 and current_position == -1:
            return 0
        else:
            99
