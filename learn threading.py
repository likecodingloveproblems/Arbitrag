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
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        # Start the load operations and mark each future with its URL
        datas = []
        future_to_url = {executor.submit(load_url, exc): exc for exc in EXCS}
        for future in concurrent.futures.as_completed(future_to_url):
            exc = future_to_url[future]
            try:
                data = future.result()
                datas.append(data.content)
            except Exception as e:
                print('%r generated an exception: %s' % (exc, e))
            # else:
            #     print('%r page is %d bytes' % (url, len(data)))
    print('end of parallel...')
    print(datas)
# parallel()
print(timeit.timeit(parallel, number=1))
print('done...')