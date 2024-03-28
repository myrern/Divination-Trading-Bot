import numpy as np
import pandas as pd


class TechnicalIndicators:
    def __init__(self, df):
        self.df = df

    def SMA(self, period=30, column="Close"):
        return self.df[column].rolling(window=period).mean()

    def EMA(self, period=20, column="Close"):
        return self.df[column].ewm(span=period, adjust=False).mean()

    def MACD(self, span1=26, span2=12, signal=9, column="Close"):
        ema1 = self.EMA(period=span1, column=column)
        ema2 = self.EMA(period=span2, column=column)
        macd = ema2 - ema1
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        return macd, signal_line

    def RSI(self, period=14, column="mid_c"):
        delta = self.df[column].diff(1)
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def BollingerBands(self, period=20, column="Close"):
        sma = self.SMA(period=period, column=column)
        std_dev = self.df[column].rolling(window=period).std()
        upper_band = sma + (std_dev * 2)
        lower_band = sma - (std_dev * 2)
        return upper_band, lower_band

    def StochasticOscillator(self, k_period=14, d_period=3):
        L14 = self.df["Low"].rolling(window=k_period).min()
        H14 = self.df["High"].rolling(window=k_period).max()
        K = 100 * ((self.df["Close"] - L14) / (H14 - L14))
        D = K.rolling(window=d_period).mean()
        return K, D

    def ATR(self, period=14):
        hl = self.df["mid_h"] - self.df["mid_l"]
        hc = np.abs(self.df["mid_h"] - self.df["mid_c"].shift())
        lc = np.abs(self.df["mid_l"] - self.df["mid_c"].shift())
        tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()
    
    def IBS(self):
        self.df['IBS'] = (self.df['mid_c'] - self.df['mid_l']) / (self.df['mid_h'] - self.df['mid_l'])
        return self.df['IBS']

    def roc(self, period=30):
        return (self.df["Close"] / self.df["Close"].shift(period)) - 1
