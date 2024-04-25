from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List
import numpy as np
import math


class Trader:
    def __init__(self):
        self.target_prices = {
            'COCONUT': 9500, 'COCONUT_COUPON': 500
        }
        self.position_limits = {
            'COCONUT': 300, 'COCONUT_COUPON': 600
        }
        self.memory_length = 20
        self.price_memory = {
            product: [0] * self.memory_length for product in self.target_prices}
        # Adjust based on volatility
        self.std_dev = {product: 50 for product in self.target_prices}
        self.smoothing_factor = 0.2

    def update_price_memory(self, product, order_depth):
        best_ask = min(
            order_depth.sell_orders) if order_depth.sell_orders else None
        best_bid = max(
            order_depth.buy_orders) if order_depth.buy_orders else None
        if best_ask is not None and best_bid is not None:
            mid_price = (best_ask + best_bid) / 2
            self.price_memory[product].append(mid_price)
            if len(self.price_memory[product]) > self.memory_length:
                self.price_memory[product].pop(0)

    def predict_price_exponential_smoothing(self, product):
        prices = self.price_memory[product]
        if not prices:
            return None
        smooth_price = prices[0]
        for price in prices[1:]:
            smooth_price = self.smoothing_factor * price + \
                (1 - self.smoothing_factor) * smooth_price
        return smooth_price

    def calculate_trading_limits(self, product, current_position, price, direction):
        if direction == 'buy':
            available_limit = self.position_limits[product] - current_position
            acceptable_price = self.target_prices[product] - \
                self.std_dev[product]
            return price <= acceptable_price, min(available_limit, int(self.position_limits[product] / price))
        else:
            available_limit = self.position_limits[product] + current_position
            acceptable_price = self.target_prices[product] + \
                self.std_dev[product]
            return price >= acceptable_price, available_limit

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

    def calc_coconut_orders(self, state, product):
        # Define market parameters for COCONUT_COUPON
        S = 10000  # Example current price, dynamically update based on actual data
        K = 10000  # Example strike price
        T = 250 / 365  # Time to expiry in years
        r = 0  # Risk-free rate
        sigma = 0.20  # Volatility

        orders = []
        acceptable_price = self.black_scholes_call(
            S, K, T, r, sigma) if product == "COCONUT_COUPON" else S
        order_depth = state.order_depths[product]
        current_position = state.position.get(product, 0)

        if order_depth.sell_orders:
            best_ask = min(order_depth.sell_orders)
            if float(best_ask) < acceptable_price:
                available_limit = self.position_limits[product] - \
                    current_position
                amount = min(
                    order_depth.sell_orders[best_ask], available_limit)
                if amount > 0:
                    orders.append(Order(product, best_ask, amount))

        if order_depth.buy_orders:
            best_bid = max(order_depth.buy_orders)
            if float(best_bid) > acceptable_price:
                available_limit = self.position_limits[product] + \
                    current_position
                amount = min(order_depth.buy_orders[best_bid], available_limit)
                if amount > 0:
                    orders.append(Order(product, best_bid, -amount))

        return orders

    def run(self, state: TradingState):
        print("traderData: " + state.traderData)
        print("Observations: " + str(state.observations))
        result = {}
        result["COCONUT"] = self.calc_coconut_orders(state, "COCONUT")
        result["COCONUT_COUPON"] = self.calc_coconut_orders(
            state, "COCONUT_COUPON")

        traderData = "SAMPLE"  # Replace with actual trader state serialization logic
        conversions = 1  # Replace with actual conversion logic
        return result, conversions, traderData
