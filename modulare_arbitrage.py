import requests as rq
import time
import datetime
import json
from decimal import Context, setcontext, Decimal, ROUND_DOWN
import concurrent.futures

username = 'am.civil71@gmail.com'
password = 'QL@BkkScCYE5X3g'


class Arbitrage:
    # config Decimal
    myContext = Context(prec=15, rounding=ROUND_DOWN)
    setcontext(myContext)
    price = 'price'
    amount = 'amount'
    buy = 'buy'
    sell = 'sell'
    usdt = 'USDT'
    irt = 'IRT'
    month_sec = Decimal(30*24*60*60)
    four_hour_sec = Decimal(4*60*60)

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.token = None
        self.headers = {}
        self.remember = 'yes'
        self.auth_time = 0.0
        self._base_coin = lambda x: self.irt if x.endswith(
            self.irt) else self.usdt
        self.rls_balance = Decimal(0.0)

    def log(self, text):
        with open('log.txt', 'a') as log_file:
            log_file.write(str(datetime.datetime.now())+': '+text+'\n')

    def auth(self, username, password):
        address = 'https://api.nobitex.ir/auth/login/'
        data = {'username': username,
                'password': password,
                'remember': self.remember}
        token = rq.post(address, data=data)
        return json.loads(token.content)

    def check_auth(self):
        tol = 20*60  # 5 min before expiration of token
        now = time.time()
        dt = now - self.auth_time
        acceptable_dt = self.month_sec if self.remember else self.four_hour_sec
        if dt + tol > acceptable_dt:
            while True:
                auth_key = self.auth(username=self.username,
                                     password=self.password)
                self.log('auth, status: {}'.format(auth_key['status']))
                if auth_key['status'] == 'success':
                    break
            self.auth_time = time.time()
            self.token = auth_key['key']
            self.headers['Authorization'] = 'Token '+self.token

    def get_order(self, symbol):
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

    # this will create a loop over all combination of coins
    def create_loops(self):
        coins = ['BTC', 'ETH', 'LTC', 'XRP', 'BCH',
                 'BNB', 'EOS', 'XLM', 'ETC', 'TRX']
        irt = 'IRT'
        usdt = 'USDT'
        buy = 'buy'
        sell = 'sell'
        loops = []
        for coin in coins:
            loop_irt = [[coin+irt, buy], [coin+usdt, sell], [usdt+irt, sell]]
            loop_usdt = [[usdt+irt, buy], [coin+usdt, buy], [coin+irt, sell]]
            loops.append(loop_irt)
            loops.append(loop_usdt)
        return loops

    def transaction_fee(self, base_coin):
        if base_coin == self.irt:
            return Decimal('0.9965')
        elif base_coin == self.usdt:
            return Decimal('0.998')

    # check profitablity of loop
    def check_profit(self, loop):
        # first get_orders async
        # then calculate profit
        orders = [0,0,0]
        EXCS = list(map(lambda x: x[0], loop))
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            excutes = {executor.submit(self.get_order, exc): exc for exc in EXCS}
            for exc_thread in concurrent.futures.as_completed(excutes):
                exc = excutes[exc_thread]
                try:
                    order = exc_thread.result()
                    orders[EXCS.index(exc)] = order
                except Exception as e:
                    self.log('get order data!!! {}'.format(e))

        # now we have orders for one loop of arbitrage
        # we can calculate profit
        profit = Decimal('1.0')
        for n, (exc, order_type) in enumerate(loop):
            base_coin = self._base_coin(exc)
            order = orders[n]
            if order_type == self.buy:
                profit = profit/order[order_type][self.price]
            else:
                profit = profit*order[order_type][self.price]
            loop[n].append(order[order_type][self.amount])
            loop[n].append(order[order_type][self.price])
            fee = self.transaction_fee(base_coin)
            profit = profit*fee
        return profit, loop

    def get_wallets(self):
        url = 'https://api.nobitex.ir/users/wallets/list'
        r = rq.post(url, headers=self.headers)
        return r

    def get_balance(self, coin):
        url = 'https://api.nobitex.ir/users/wallets/balance'
        data = {"currency": coin}
        r = rq.post(url, data, headers=self.headers)
        return Decimal(json.loads(r.content)['balance'])

    def update_rls_balance(self, coin='rls'):
        self.rls_balance = self.get_balance(coin)

    def set_order(self, type, base_coin, coin, amount):
        url = 'https://api.nobitex.ir/market/orders/add'
        base_coin = 'rls' if base_coin == self.irt else 'usdt'
        data = {"type": type, "execution":"market", "srcCurrency": coin,
                "dstCurrency": base_coin, "amount": amount}
        r = rq.post(url, data=data, headers=self.headers)
        content = json.loads(r.content)
        return content

    def order_status(self, order_content):
        url = 'https://api.nobitex.ir/market/orders/status'
        data = {'id': order_content['order']['id']}
        r = rq.post(url, data=data, headers=self.headers)
        return json.loads(r.content)

    def cal_amounts(self, loop):
        balance = self.rls_balance
        if loop[0][0] == 'USDTIRT':
            # forward
            balance = min(balance, loop[0][2]*loop[0][3])
            loop[0][2] = balance/loop[0][3]
            fee = self.transaction_fee(self.irt)
            balance = min(loop[0][2]*fee, loop[1][2]*loop[1][3])
            loop[1][2] = balance/loop[1][3]
            fee = self.transaction_fee(self.usdt)
            balance = min(loop[1][2]*fee, loop[2][2])
            loop[2][2] = balance

            # backward
            balance = loop[2][2]
            fee = self.transaction_fee(self.usdt)
            loop[1][2] = loop[2][2]/fee
            fee = self.transaction_fee(self.irt)
            loop[0][2] = loop[1][2]*loop[1][3]/fee

        else:
            # forward
            balance = min(balance, loop[0][2]*loop[0][3])
            loop[0][2] = balance/loop[0][3]
            fee = self.transaction_fee(self._base_coin(loop[0][0]))
            balance = min(loop[0][2]*fee, loop[1][2])
            loop[1][2] = balance
            fee = self.transaction_fee(self._base_coin(loop[1][0]))
            balance = min(loop[1][2]*loop[1][3]*fee, loop[2][2])
            loop[2][2] = balance

            # backward
            balance = loop[2][2]
            fee = self.transaction_fee(self.usdt)
            loop[1][2] = loop[2][2]/(fee*loop[1][3])
            fee = self.transaction_fee(self.irt)
            loop[0][2] = loop[1][2]/fee

        return loop

    def overValueOrder_check(self, order_type, base_coin, coin, amount, price):
        if order_type==self.buy:
            base_coin = 'rls' if base_coin==self.irt else 'usdt'
            base_coin_balance = self.get_balance(base_coin)
            return base_coin_balance/price
        elif order_type==self.sell:
            return self.get_balance(coin)
        else:
            self.log('order type is not defined!!! order_type:{}'.format(order_type)) 


    def excute_loop(self, loop):
        loop = self.cal_amounts(loop)
        # check smallOrder Error
        IRT_amount = loop[0][2]*loop[0][3]
        USDT_amount = list(filter(lambda x: x[0] == 'USDTIRT', loop))[0][2]
        if IRT_amount < 1050000.0:
            self.log('the amount of loop is lower than 1050000 IRT')
            return None
        if USDT_amount < 11.1:
            self.log('the amount of excution is lower than 11.1 USDT')
            return None 
        # check duplicateOrder 
        # check marketClosed 
        # check tradingUnavailable
        # check tradeLimitation
        for n, (exc, order_type, amount, price) in enumerate(loop):
            base_coin = self._base_coin(exc)
            coin = exc.replace(base_coin, '').lower()
            # check overValueOrder Error
            amount = self.overValueOrder_check(order_type, base_coin, coin, amount, price)
            content = self.set_order(
                order_type, base_coin, coin, amount)
            self.log('setOrder, {}, {}, {}, {}, {}, status: {}\n content: {}'.format(
                order_type, base_coin, coin, amount, price, content['status'], content))
            if content['status'] == 'failed':
                if content['code']=='OverValueOrder':
                    self.log('order failed: content:{}\namount:{}'.format(
                        content, amount))
                else:
                    self.log(content)

            # wait until the order is done
            while True:
                r = self.order_status(content)
                # check status
                status = r['order']['status']
                # because we use market execution we don't need unmatchedAmount
                # # check unmatchedAmount
                # unmatchedAmount_condition = float(
                #     r['order']['unmatchedAmount']) == 0.0
                if status=='Done':
                    break
                if status=='Cancel':
                    self.log(content)
                    self.excute_loop(loop[n:])


    def main(self):
        # check auth
        self.check_auth()
        self.update_rls_balance()
        loops = self.create_loops()
        for loop in loops:
            # check profittability
            profit, loop = self.check_profit(loop)
            print(loop, profit)
            if profit > 1.0:
                self.excute_loop(loop)
                self.update_rls_balance()


# if __name__ == '__main__':
a = Arbitrage(username, password)
while True:
    a.main()
