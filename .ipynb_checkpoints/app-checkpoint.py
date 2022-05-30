import json, config, threading
from strategies import MultiTrader
from exchanges import Binance
from logger import Excel_log

if __name__ == "__main__":
    with open ('setting.json', "r") as f:
        setting = json.load(f)
    
    api_key = config.API_KEY
    api_secret = config.API_SECRET
    
    application = MultiTrader(Binance(api_key, api_secret), Excel_log("orders.xlsx"), setting)
    application.strat()
    