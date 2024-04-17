import numpy as np
from datamodel import Order, TradingState
from typing import List, Dict


class Trader:
    def __init__(self):
        self.target_prices = {'STARFRUIT': 5039.5, 'AMETHYSTS': 10000}
        self.position_limits = {'STARFRUIT': 20, 'AMETHYSTS': 20}
        self.memory_length = 20
        self.price_memory = {
            product: [0]*self.memory_length for product in self.target_prices}
        self.std_dev = {'STARFRUIT': 1.5, 'AMETHYSTS': 1.51}
        self.smoothing_factor = 0.2  # Alpha for exponential smoothing

    def calc_orders(self, state, product):
        order_depth = state.order_depths[product]
        orders = []
        current_position = state.position.get(product, 0)
        available_buy_limit = self.position_limits[product] - current_position
        available_sell_limit = self.position_limits[product] + current_position
        price_adjustment = self.std_dev[product] if product == 'AMETHYSTS' else self.predict_price_exponential_smoothing(
            product)
        if price_adjustment is None:
            return []

        acceptable_buy_price = self.target_prices[product] - price_adjustment
        acceptable_sell_price = self.target_prices[product] + price_adjustment
        print(f"Acceptable buy price for {product}: {acceptable_buy_price}")
        print(f"Acceptable sell price for {product}: {acceptable_sell_price}")

        orders += self.generate_orders(order_depth.sell_orders,
                                       acceptable_buy_price, available_buy_limit, 'BUY', product)
        orders += self.generate_orders(order_depth.buy_orders, acceptable_sell_price,
                                       available_sell_limit, 'SELL', product, reverse=True)

        return orders

    def generate_orders(self, orders_dict, price_limit, available_limit, order_type, product, reverse=False):
        result_orders = []
        sorted_orders = sorted(orders_dict.items(), reverse=reverse)
        for price, amount in sorted_orders:
            if (price <= price_limit and order_type == 'BUY') or (price >= price_limit and order_type == 'SELL'):
                trade_amount = min(abs(amount), available_limit) * \
                    (-1 if order_type == 'SELL' else 1)
                if trade_amount != 0:
                    result_orders.append(Order(product, price, trade_amount))
                    available_limit -= abs(trade_amount)
        return result_orders

    def update_price_memory(self, product, order_depth):
        best_ask = min(
            order_depth.sell_orders) if order_depth.sell_orders else None
        best_bid = max(
            order_depth.buy_orders) if order_depth.buy_orders else None
        if best_ask and best_bid:
            mid_price = (best_ask + best_bid) / 2
            self.price_memory[product].append(mid_price)
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

    def run(self, state: TradingState):
        print(f"traderData: {state.traderData}")
        print(f"Observations: {str(state.observations)}")
        result = {product: self.calc_orders(
            state, product) for product in self.target_prices}
        traderData = "SAMPLE"  # Replace with actual trader state serialization logic
        conversions = 1  # Replace with actual conversion logic
        return result, conversions, traderData
