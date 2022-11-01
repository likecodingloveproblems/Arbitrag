# Arbitrage Trading
this is my first attempt to create an algorithmic trader based on the arbitrage strategy in cryptocurrency market, I uses the [Nobitex API](https://apidocs.nobitex.ir/#api) to get the market data and set order.


**It has too many problems, so don't use it, I just want to share it with you.**

I understood that arbitrage strategy is very sensitive to network latency, so I use threading but it also failed, because market changed in milliseconds. Also this projects hasn't a good logging framework with an exception handler strategy.