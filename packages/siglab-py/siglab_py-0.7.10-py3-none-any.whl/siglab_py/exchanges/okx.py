from typing import Dict

import ccxt

if __name__ == '__main__':
    apiKey : str = None
    secret : str = None 
    passphrase : str = None
    subaccount : str = None
    
    params : Dict = {
        'apiKey' : apiKey,
        'secret' : secret,
        'password' : passphrase,
        'subaccount' : subaccount,
        'rateLimit' : 100,                    # In ms
        'options' : {
            'defaultType': 'swap', # 'funding', 'spot', 'margin', 'future', 'swap', 'option'
        }
    }
    exchange = ccxt.okx(params)
    markets = exchange.load_markets()

    if apiKey:
        balances = exchange.fetch_balance()
    
    xaut_perp_ticker = 'XAU/USDT:USDT'
    found = next(( market for market in markets if market == xaut_perp_ticker), None)
    if found:
        '''
        'id' = 'XAU-USDT-SWAP'
        'symbol' = 'XAU/USDT:USDT' <-- normalized symbol
        '''
        xaut_perp_market = markets[xaut_perp_ticker]
        print(xaut_perp_market)

        entry_order = exchange.create_order(
            symbol = xaut_perp_ticker,
            amount = 10, # buy 0.001 XAU means 10 XAUT/USDT:USDT contract (0.0001 multipler)
            type='market',
            side='sell'
        )

        print(entry_order)

        positions = exchange.fetch_positions()
        for pos in positions:
            '''
            For longs, 'side' = 'long', 'contracts' = 100.0 (positive integer)
            For shorts, 'side' = 'short', 'contracts' = 100.0 (positive integer)
            '''
            print(pos)

            exit_order = exchange.create_order(
                symbol = xaut_perp_ticker,
                amount = pos['contracts'],
                type='market',
                side='buy' if pos['side']=='short' else 'sell'
            )