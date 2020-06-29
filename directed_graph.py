import networkx as nx

# buying crypto by IRT

# transfer from exchange to wallet

# transfer from wallet to exchange

# Binance excahgne excution 

# NOBITEX symbols
#             'TRXIRT',
n_symbols = ['BTCIRT',
             'ETHIRT',
             'LTCIRT',
             'XRPIRT',
             'BCHIRT',
             'BNBIRT',
             'EOSIRT',
             'XLMIRT',
             'ETCIRT',
             'TRXIRT',
             'USDTIRT',
             'BTCUSDT',
             'ETHUSDT',
             'LTCUSDT',
             'XRPUSDT',
             'BCHUSDT',
             'BNBUSDT',
             'EOSUSDT',
             'XLMUSDT',
             'ETCUSDT',
             'TRXUSDT']



G = nx.DiGraph()
data = [
    ['IRT','BTCN',1/],
    ['IRT','USDTN',1/],
    ['IRT','XRPN',1/],
    ['BTCN','BTCB',1],
    ['USDTN','USDTB',1],
    ['BTCN','BTCB',1],
    ['BTCB',]
    ]
G.add_weighted_edges_from([])