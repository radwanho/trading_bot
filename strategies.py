from abc import ABC, abstractmethod
from exchanges import Exchange
import websocket, json, math
from binance.enums import *
from logger import Logger

class TradingBot(ABC):

    def __init__(self, exchange: Exchange, log: Logger, conf):
        self.exchange = exchange
        self.logger = log
        self.live = conf["live"]
        self.symbol = conf["symbol"]
        self.coin = conf["coin"]
        self.frame = conf["frame"]
        self.arg_strategie = conf["strategie"]
        self.count = 1
        self.trades = []

    def strat(self):
        if self.live:
            self.exchange.subscribe(self.symbol, self.frame)
            self.connect()
        else:
            self.run_backtest_for_strategie()
        
    def connect(self):
        self.ws = websocket.WebSocketApp(self.exchange.socket, on_open=self.on_open, on_close=self.on_close, on_message=self.on_message)
        self.ws.run_forever()     
    
    def disconnect(self):
        self.ws.close()
      
    def buy(self, close, trade_qty):
        if self.live:
            return self.exchange.order(SIDE_BUY, trade_qty, close)
        return self.exchange.test_order(self.symbol, SIDE_BUY, trade_qty, close)

    def sell(self, close, qty):
        if self.live:
            return self.exchange.order(SIDE_SELL, qty, close)
        return self.exchange.test_order(self.symbol, SIDE_SELL, qty, close)
 
    def string_to_float(self, f, n):
        return math.floor(f * 10 ** n) / 10 ** n

    def update_info(self, order, close, balance):
        if self.exchange.order_side(order) == "BUY":
            self.trades.append(self.exchange.formated_order(order))
        else:
            del self.trades[-1]

        for o in self.exchange.order_fills_details(order, self.count, close, balance):
            self.log(o)

        total_investement = sum((float(i["p"]) for i in self.trades))
        total_quantity = sum((float(i["q_net"]) for i in self.trades))
        print(f'My BALANCE = ${str(balance)} / Total Invest = ${str(total_investement)} /  Total Quantity = {str(total_quantity)}\n')
        self.count += 1

    def on_open(self, ws):
        print('opened connection')

    def on_close(self, ws):
        print('closed connection')
        self.connect()
    
    def on_message(self, ws, message):     
        json_message = json.loads(message)
        self.run_strategie(json_message)
    
    def log(self, data):
        self.logger.write(data)
    
    @abstractmethod
    def should_buy(self, close) -> bool:
        pass
    
    @abstractmethod
    def should_sell(self, close) -> bool:
        pass
    
    @abstractmethod
    def run_strategie(self, data) -> None:
        pass
    
    @abstractmethod
    def run_backtest_for_strategie(self) -> None:
        pass

class MultiTrader(TradingBot):

    def __init__(self, exchange: Exchange, log: Logger, setting):
        TradingBot.__init__(self, exchange, log, setting)
        self.balance = float(self.arg_strategie["balance"])
        self.TRADE_TOTAL_PRICE = float(self.arg_strategie["each_buy_price"])
        self.PERCENTAGE_BUY = float(self.arg_strategie["next_buy"])  #0.992 >> 0.008 = $5
        self.PERCENTAGE_SELL = float(self.arg_strategie["sell_at"]) #0.992 >> 0.008 = $0.80

    def should_buy(self, close) -> bool:
        if self.balance < self.TRADE_TOTAL_PRICE:
            return False
        
        if len(self.trades) == 0:
            return True

        last_trade_q, last_trade_p = float(self.trades[-1]["q_net"]), self.trades[-1]["p"]
        if (close * last_trade_q) < (last_trade_p * self.PERCENTAGE_BUY):
            return True
        return False
    
    def should_sell(self, close) -> bool:
        trade_p = self.trades[-1]["p"]
        trade_q = self.trades[-1]["q_net"]
        last_trades_balance = close * trade_q
        diff = last_trades_balance - trade_p

        if diff > trade_p - (trade_p * self.PERCENTAGE_SELL):
            return True
        return False
 
    def run_strategie(self, data):
        candle = self.exchange.get_current_candle(data)
        close = float(candle['c'])

        trade_qty = round(self.TRADE_TOTAL_PRICE / close, self.arg_strategie["precision"])

        make_order = False

        if self.should_buy(close):
            resp_order = self.buy(close, trade_qty)
            make_order = True

        elif self.should_sell(close):
            qty = self.string_to_float(self.trades[-1]["q_net"], self.arg_strategie["precision"])
            resp_order = self.sell(close, qty)
            make_order = True

        if make_order:
            if self.exchange.check_order(resp_order):
                order = self.exchange.get_order(resp_order)
                self.update_info(order, close, self.balance)
                if self.exchange.order_side(order) == "BUY":
                    self.balance -= self.trades[-1]["p"]
                    if self.arg_strategie["allow_increase"]:
                        self.PERCENTAGE_BUY -= float(self.arg_strategie["increase_percenttage_by"])
                        self.PERCENTAGE_SELL -= float(self.arg_strategie["increase_percenttage_by"])
                else:
                    self.balance += self.exchange.cal_net_price_of_order(order)
                    if self.arg_strategie["allow_increase"]:
                        self.PERCENTAGE_BUY += float(self.arg_strategie["increase_percenttage_by"])
                        self.PERCENTAGE_SELL += float(self.arg_strategie["increase_percenttage_by"])
            else:
                print("an exception occured - {}".format(self.exchange.get_order_error(resp_order)))

    def run_backtest_for_strategie(self) -> None:
        try:
            with open(f'{self.symbol}_{self.frame}.csv', 'r') as f:
                for line in f:
                    row = line.split(',')  
                    data = {
                        "k":{
                            "o":row[1],
                            "h":row[2],
                            "l":row[3],
                            "c":row[4]
                        }
                    }
                    self.run_strategie(data)
        except FileNotFoundError:
            print("you need a data to backtest it, please use this cmd tou download same data : python get_data.py")
