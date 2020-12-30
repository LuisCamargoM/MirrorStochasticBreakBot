from candlestick.patterns.candlestick_finder import CandlestickFinder


class CandleForce(CandlestickFinder):
    def __init__(self, target=None):
        super().__init__(self.get_class_name(), 2, target=target)

    def logic(self, idx):
        candle = self.data.iloc[idx]
        prev_candle = self.data.iloc[idx + 1 * self.multi_coeff]

        close = candle[self.close_column]        
        open = candle[self.open_column]
        #high = candle[self.high_column]
        #low = candle[self.low_column]

        prev_close = prev_candle[self.close_column]        
        prev_open = prev_candle[self.open_column]        
        #prev_high = prev_candle[self.high_column]
        #prev_low = prev_candle[self.low_column]
        
        
        dif = close - prev_open
        tamT = close - prev_close

        prev_tam = abs(prev_close-prev_open)
        actual_tam = abs(close-open)

        # force = abs(tamT/dif) * 100
        # if(force >= 75):
        #     print('Force',force)
        s = (prev_tam/actual_tam)*100
        return (s >= 70) 
    