from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List
import numpy as np
import math


class Trader:

    def norm_cdf(self, x):
        """Use the error function to calculate the cumulative distribution function for the standard normal distribution."""
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))

    def black_scholes_call(self, S, K, T, r, sigma):
        """ Calculate the Black-Scholes option price for a call option. """
        d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / \
            (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        call_price = S * self.norm_cdf(d1) - K * \
            math.exp(-r * T) * self.norm_cdf(d2)
        return call_price

    def run(self, state: TradingState):
        print("traderData: " + state.traderData)
        print("Observations: " + str(state.observations))
        result = {}
        # Example market parameters (adjust based on actual market data or observations)
        S = 10000  # Current price of COCONUT, needs dynamic update based on market
        K = 10000  # Strike price as given in problem statement
        T = 250 / 365  # Time to expiry in years
        r = 0.01  # Risk-free rate, should be based on market or assumed
        sigma = 0.20  # Volatility, should be calculated from market data

        for product in state.order_depths:
            order_depth: OrderDepth = state.order_depths[product]
            orders: List[Order] = []

            # Calculate acceptable price using Black-Scholes for COCONUT_COUPON
            if product == "COCONUT_COUPON":
                acceptable_price = self.black_scholes_call(S, K, T, r, sigma)
            else:
                acceptable_price = S  # For COCONUT, might use another strategy

            print("Acceptable price for " + product +
                  ": " + str(acceptable_price))
            print("Buy Order depth : " + str(len(order_depth.buy_orders)) +
                  ", Sell order depth : " + str(len(order_depth.sell_orders)))

            if len(order_depth.sell_orders) != 0:
                best_ask, best_ask_amount = list(
                    order_depth.sell_orders.items())[0]
                if float(best_ask) < acceptable_price:
                    print("BUY", str(-best_ask_amount) + "x", best_ask)
                    orders.append(Order(product, best_ask, -best_ask_amount))

            if len(order_depth.buy_orders) != 0:
                best_bid, best_bid_amount = list(
                    order_depth.buy_orders.items())[0]
                if float(best_bid) > acceptable_price:
                    print("SELL", str(best_bid_amount) + "x", best_bid)
                    orders.append(Order(product, best_bid, -best_bid_amount))

            result[product] = orders

        traderData = "UPDATED STATE DATA"  # Update trader state data as needed
        conversions = 1  # Update based on any conversions or adjustments needed
        return result, conversions, traderData
