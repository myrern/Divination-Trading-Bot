import numpy as np
import pandas as pd

from TechnicalIndicators import TechnicalIndicators


class Strategies:
    def get_signal(self, strategy, candles):
        if strategy["strategy_name"] == "IBS":
            return self.IBS(strategy, candles)
        elif strategy.strategy_name == "RSI":
            return self.RSI()

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
