# Crypto trading bot

This app is a template for who are interested in creating their own trading strategies.

    -in exchanges.py file you will find an example of an implimentation of an exchange, you can add others just follow the Binance example
    -in strategies.py file you can impliment here your own strategy by following the current example
    -to back test your strategy :
        1- in the setting.py file the argument live must be false
        2- modify the setting.py file with the Symbol and the frame and the info you need for your strategie 
        3- download the data using this cmd "python get_data.py" 
        4- run the test by this cmd "python app.py"
 
    