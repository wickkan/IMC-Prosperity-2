from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List
import numpy as np
import math


class PriceEstimator:
    def __init__(self, alpha=0.1):
        self.ema_prices = {}
        self.alpha = alpha  # Smoothing factor, adjustable based on responsiveness needs

    def update_price(self, product, new_price):
        if product in self.ema_prices:
            self.ema_prices[product] = (
                1 - self.alpha) * self.ema_prices[product] + self.alpha * new_price
        else:
            self.ema_prices[product] = new_price
        return self.ema_prices[product]


class Trader:
    def __init__(self):
        self.inventory = {
            "COCONUT": 0,
            "COCONUT_COUPON": 0
        }
        self.position_limits = {
            "COCONUT": 300,
            "COCONUT_COUPON": 600
        }
        # Smaller alpha values smooth out price volatility more
        self.price_estimator = PriceEstimator(alpha=0.1)

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

        for product in state.order_depths:
            order_depth: OrderDepth = state.order_depths[product]
            orders: List[Order] = []

            if len(order_depth.sell_orders) > 0:
                # Assume the lowest sell order as the latest price
                latest_price = float(list(order_depth.sell_orders.keys())[0])
                S = self.price_estimator.update_price(product, latest_price)
            else:
                # Default to 10000 if no sell orders are present
                S = self.price_estimator.ema_prices.get(product, 10000)

            K = 10000
            T = 250 / 365
            r = 0
            sigma = 0.20
            acceptable_price = self.black_scholes_call(
                S, K, T, r, sigma) if product == "COCONUT_COUPON" else S

            print("Acceptable price for " + product +
                  ": " + str(acceptable_price))
            print("Buy Order depth : " + str(len(order_depth.buy_orders)) +
                  ", Sell order depth : " + str(len(order_depth.sell_orders)))

            # Handle sell orders
            if len(order_depth.sell_orders) != 0:
                best_ask, best_ask_amount = list(
                    order_depth.sell_orders.items())[0]
                if float(best_ask) < acceptable_price:
                    # Ensure not buying more than position limit
                    max_buy = self.position_limits[product] - \
                        self.inventory[product]
                    buy_amount = min(-best_ask_amount, max_buy)
                    if buy_amount > 0:
                        print("BUY", str(buy_amount) + "x", best_ask)
                        orders.append(Order(product, best_ask, -buy_amount))
                        self.inventory[product] += buy_amount

            # Handle buy orders
            if len(order_depth.buy_orders) != 0:
                best_bid, best_bid_amount = list(
                    order_depth.buy_orders.items())[0]
                if float(best_bid) > acceptable_price:
                    # Ensure not selling more than what we have
                    sell_amount = min(best_bid_amount, self.inventory[product])
                    if sell_amount > 0:
                        print("SELL", str(sell_amount) + "x", best_bid)
                        orders.append(Order(product, best_bid, -sell_amount))
                        self.inventory[product] -= sell_amount

            result[product] = orders

        traderData = "UPDATED STATE DATA"  # Update trader state data as needed
        conversions = 1  # Update based on any conversions or adjustments needed
        return result, conversions, traderData
