from abc import ABC, abstractmethod
from datetime import datetime
import csv

class Logger(ABC):
    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def write(self, data):
        pass

class Excel_log(Logger):

    def __init__(self, filename) -> None:
        self.filename = filename
        print("start logging...")

    def start(self):
        pass 

    def write(self, data):
        try:
            now = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
            data["date"] = now
            print(f'{data["count"]}\t{now}\t{data["side"].upper()}\t{data["close"]}\t{data["price"]}\t{data["t_qty"]}\t{data["t_commission"]}\t{data["balance"]}')

            with open(self.filename, 'a') as csvfile:
                writer = csv.DictWriter(csvfile, ['count', 'date', 'side', 'close', 'price', 't_qty', 't_commission', 'balance'])
                writer.writerow(data)
        except Exception as e:
            print(f"error: {e}")
    
    def close(self):
        pass