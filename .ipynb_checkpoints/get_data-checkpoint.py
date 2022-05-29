import config, csv, json
from binance.client import Client

if __name__ == "__main__":
    with open ('setting.json', "r") as f:
        setting = json.load(f)

    client = Client(config.API_KEY, config.API_SECRET)

    csvfile = open(f'{setting["symbol"]}_{setting["frame"]}.csv', 'w', newline='') 
    candlestick_writer = csv.writer(csvfile, delimiter=',')

    candlesticks = client.get_historical_klines(setting["symbol"], setting["frame"], "10 May, 2022", "17 May, 2022")

    for candlestick in  candlesticks:
        candlestick[0] = candlestick[0] / 1000
        candlestick_writer.writerow(candlestick)

    csvfile.close()