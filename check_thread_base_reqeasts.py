import time
import requests as rq
import json
from decimal import Context, setcontext, Decimal, ROUND_DOWN
import threading
import timeit
def get_order(symbol):
    orders = rq.post('https://api.nobitex.ir/v2/orderbook',
                        data={'symbol': symbol})
    if not orders.ok:
        print('status code: {}'.format(orders.status_code))
    content = json.loads(orders.content)
    last_order = {
        'buy': {'price': Decimal(content['bids'][0][0]), 'amount': Decimal(content['bids'][0][1])},
        'sell': {'price': Decimal(content['asks'][0][0]), 'amount': Decimal(content['asks'][0][1])}
    }
    return last_order

loop = [['USDTIRT', 'buy'], ['BTCUSDT', 'buy'], ['BTCIRT', 'sell']]
def series():
    for exc, _ in loop:
        get_order(exc)

def thread_base():
    t = []
    for n,(exc, _) in enumerate(loop):
        t.append(threading.Thread(target=get_order, args=(exc,)))
        t[n].start()
    while t[0].is_alive() and t[1].is_alive() and t[2].is_alive():
        pass
print(timeit.timeit(series, number=10))
print(timeit.timeit(thread_base, number=10))



import concurrent.futures
import requests as rq
import timeit

EXCS = ['BTCIRT', 'BTCUSDT', 'USDTIRT']
URL = 'https://api.nobitex.ir/v2/orderbook'
# Retrieve a single page and report the URL and contents
def load_url(symbol):
    return rq.post(URL, data={'symbol':symbol})

# We can use a with statement to ensure threads are cleaned up promptly
def parallel():
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        # Start the load operations and mark each future with its URL
        future_to_url = {executor.submit(load_url, exc): exc for exc in EXCS}
        for future in concurrent.futures.as_completed(future_to_url):
            exc = future_to_url[future]
            try:
                data = future.result()
            except Exception as e:
                print('%r generated an exception: %s' % (exc, e))
            # else:
            #     print('%r page is %d bytes' % (url, len(data)))
        
    print('end of function...')

print(timeit.timeit(parallel, number=10))
print('done...')