import requests
from abc import ABC, abstractmethod
from binance.client import Client
from binance.enums import *

class Exchange(ABC):
    @abstractmethod
    def order(self, side, quantity, close_price, order_type=ORDER_TYPE_MARKET):
        pass

    @abstractmethod
    def test_order(self, symbol, side, quantity):
        pass

    @abstractmethod
    def subscribe(self, coin, frame):
        pass

    @abstractmethod
    def get_balance(self, coin):
        pass
    
    @abstractmethod
    def calc_commission_of_order(self, order):
        pass
    
    @abstractmethod
    def cal_net_price_of_order(self, order):
        pass
    
    @abstractmethod
    def formated_order(self, order):
        pass
    
    @abstractmethod
    def order_side(self, order):
        pass
    
    @abstractmethod
    def order_fills_details(self, order):
        pass

    @abstractmethod
    def check_order(self, order):
        pass
    
    @abstractmethod
    def get_order(self, order):
        pass
    
    @abstractmethod
    def get_order_error(self, order):
        pass

    @abstractmethod
    def get_current_candle(self, data):
        pass

class Binance(Exchange):
    def __init__(self, api_key, api_secret):
        self.client = Client(api_key, api_secret)

    def order(self, side, quantity, close, order_type=ORDER_TYPE_MARKET):
        try:
            if order_type == ORDER_TYPE_MARKET:
                order = self.client.create_order(symbol=self.trade_symbol, side=side, type=order_type, quantity=quantity)
            else:
                order = self.client.create_order(symbol=self.trade_symbol, side=side, type=order_type, timeInForce=TIME_IN_FORCE_GTC, quantity=quantity, price=close)
            return {"e": None, "o":order}
        except Exception as e:
            return {"e": e, "o": None}
    
    def test_order(self, trade_symbol, side, quantity, close):
        self.trade_symbol = trade_symbol.upper()
        order = {
            "symbol": self.trade_symbol,
            "orderId":1023754853,
            "orderListId":-1,
            "clientOrderId":"h0NSKP8P0Nqazs4IIekwXK",
            "transactTime":1621157102293,
            "price":"0.00000000",
            "origQty":quantity,
            "executedQty":quantity,
            "cummulativeQuoteQty": quantity*close,
            "status":"FILLED",
            "timeInForce":"GTC",
            "type":"MARKET",
            "side":side,
            "fills":[
                {
                    "price": close,
                    "qty":quantity,
                    "commission":quantity*0.001,
                    "commissionAsset":trade_symbol[:-4].upper(),
                    "tradeId":219958049
                }
            ]
        }

        return {"e": None, "o": order} 

    def subscribe(self, symbol, frame):
        baseurl = "wss://stream.binance.com:9443/ws"
        self.socket = f"{baseurl}/{symbol.lower()}@kline_{frame}"
        self.trade_symbol = symbol.upper()

    def get_balance(self, coin):
        return self.client.get_asset_balance(asset=coin.upper())
    
    def get_price(self, symbol):
        url = f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1m'
        data = requests.get(url).json()
        return float(data[-1][4])
    
    def calc_commission_of_order(self, order):
        t_commission = 0
        p_com = self.get_price(self.trade_symbol)
        t_commission = (float(order["commission"])/p_com if "USD" not in order["commissionAsset"] else float(order["commission"])/float(order["price"]))
        return t_commission
    
    def cal_net_price_of_order(self, order):
        net_p = 0
        for o in order["fills"]:
            commission = self.calc_commission_of_order(o)
            net_p += float(o["price"]) * (float(o["qty"]) - commission)
        return net_p
    
    def formated_order(self, order):
        t_commission = sum(self.calc_commission_of_order(o) for o in order["fills"])
        t_qty = sum((float(i["qty"]) for i in order["fills"]))
        qty_net = t_qty - t_commission
        trade_p = float(order["cummulativeQuoteQty"])
        trade_q = float(order["origQty"])
        return {"p":float(trade_p), "q": float(trade_q), "q_net": qty_net}
    
    def order_side(self, order):
        return order["side"].upper()
    
    def order_fills_details(self, order, count, close, balance):
        orderFillsDetails = []
        
        for o in order["fills"]:
            orderFillsDetails.append({"date": order["transactTime"], "count": count, "side": order["side"], "close": close, "price": order["cummulativeQuoteQty"], "t_qty": o["qty"], "t_commission": self.calc_commission_of_order(o), "balance": balance})
        
        return orderFillsDetails

    def check_order(self, order):
        if not order["e"]:
            return True
        return False
    
    def get_order(self, order):
        return order["o"]
    
    def get_order_error(self, order):
        return order["e"]
    
    def get_current_candle(self, data):
        return data['k']