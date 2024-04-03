from datamodel import TradingState, OrderDepth, Order, Listing
# Add Tuple and Dict to your imports
from typing import List, Tuple, Dict
# Import any other necessary classes or modules
import numpy as np


class Trader:

    def __init__(self):
        self.position_limits = {"AMETHYSTS": 20, "STARFRUIT": 20}
        self.position = {"AMETHYSTS": 0, "STARFRUIT": 0}
        self.price_memory = {"AMETHYSTS": [], "STARFRUIT": []}
        self.stop_loss_threshold = {"AMETHYSTS": -10, 
                                    "STARFRUIT": -10}  # Example values
        self.profit_target = {"AMETHYSTS": 10,
                              "STARFRUIT": 10}  # Example values

    def update_price_memory(self, product, order_depth):
        best_ask = min(
            order_depth.sell_orders) if order_depth.sell_orders else None
        best_bid = max(
            order_depth.buy_orders) if order_depth.buy_orders else None
        if best_ask and best_bid:
            mid_price = (best_ask + best_bid) / 2
            self.price_memory[product].append(mid_price)

    def calculate_acceptable_price(self, product):
        if self.price_memory[product]:
            recent_prices = self.price_memory[product][-5:]
            avg_price = sum(recent_prices) / len(recent_prices)
            price_variance = np.var(recent_prices)
            if price_variance > 1:
                # Adapt prices based on volatility
                return avg_price * (1 + np.sign(price_variance - 1) * 0.05)
            return avg_price
        return None

    def decide_order_for_product(self, product, order_depth):
        orders = []
        self.update_price_memory(product, order_depth)
        acceptable_price = self.calculate_acceptable_price(product)
        if not acceptable_price:
            return orders

        current_position = self.position[product]
        stop_loss_price = acceptable_price + self.stop_loss_threshold[product]
        profit_target_price = acceptable_price + self.profit_target[product]

        for ask, qty in order_depth.sell_orders.items():
            if ask < acceptable_price and current_position < self.position_limits[product]:
                order_qty = min(-qty,
                                self.position_limits[product] - current_position)
                if self.check_stop_loss(current_position, ask, stop_loss_price):
                    orders.append(Order(product, ask, order_qty))
                    self.position[product] += order_qty
                else:
                    print(f"Stop loss triggered for {
                          product}, not buying at {ask}")

        for bid, qty in order_depth.buy_orders.items():
            if bid > acceptable_price and current_position > -self.position_limits[product]:
                order_qty = -min(qty, current_position +
                                 self.position_limits[product])
                if self.check_profit_target(current_position, bid, profit_target_price):
                    orders.append(Order(product, bid, order_qty))
                    self.position[product] += order_qty
                else:
                    print(f"Profit target reached for {
                          product}, not selling at {bid}")

        return orders

    def check_stop_loss(self, position, current_price, stop_loss_price):
        return position > 0 or current_price > stop_loss_price

    def check_profit_target(self, position, current_price, profit_target_price):
        return position < 0 or current_price < profit_target_price

    def run(self, state: TradingState):
        print("traderData: " + state.traderData)
        print("Observations: " + str(state.observations))
        result = {}

        for product in state.order_depths:
            order_depth = state.order_depths[product]
            orders = self.decide_order_for_product(product, order_depth)
            result[product] = orders

        traderData = "Adaptive Strategy Based on Market Conditions"
        conversions = 1
        return result, conversions, traderData
