import numpy as np
from datamodel import Order, Symbol, TradingState
from typing import Any, List


class Trader:

    def __init__(self):
        # Example target price for ORCHIDS
        self.target_prices = {'STARFRUIT': 5039.5,
                              'AMETHYSTS': 10000, 'ORCHIDS': 1200}
        # Position limit for ORCHIDS as per your description
        self.position_limits = {'STARFRUIT': 20,
                                'AMETHYSTS': 20, 'ORCHIDS': 100}
        self.memory_length = 20
        self.price_memory = {"AMETHYSTS": [0]*self.memory_length, "STARFRUIT": [
            0]*self.memory_length, "ORCHIDS": [0]*self.memory_length}
        # Standard deviation estimate for ORCHIDS
        self.std_dev = {'STARFRUIT': 1.5, 'AMETHYSTS': 1.51, 'ORCHIDS': 2.0}
        self.smoothing_factor = 0.2  # Alpha for exponential smoothing

    def calc_orchids_orders(self, state, product="ORCHIDS"):
        # Assume this contains ConversionObservation data
        conversion_observation = state.observations[product]
        orders = []
        current_position = state.position.get(product, 0)
        available_buy_limit = self.position_limits[product] - current_position
        available_sell_limit = self.position_limits[product] + current_position

        acceptable_buy_price = self.target_prices[product] - \
            self.std_dev[product]
        acceptable_sell_price = self.target_prices[product] + \
            self.std_dev[product]

        # Buy ORCHIDS if the ask price + fees is below the acceptable buy price
        total_buy_cost = conversion_observation.askPrice + \
            conversion_observation.transportFees + \
            max(conversion_observation.importTariff, 0)
        if total_buy_cost <= acceptable_buy_price and available_buy_limit > 0:
            orders.append(Order(product, total_buy_cost, 1))  # Buy 1 unit

        # Sell ORCHIDS if the bid price after deducting fees is above the acceptable sell price
        total_sell_price = conversion_observation.bidPrice - \
            conversion_observation.transportFees - \
            max(conversion_observation.exportTariff, 0)
        if total_sell_price >= acceptable_sell_price and available_sell_limit > 0:
            orders.append(Order(product, total_sell_price, -1))  # Sell 1 unit

        return orders

    def calc_amethysts_orders(self, state, product="AMETHYSTS"):
        order_depth = state.order_depths[product]
        orders = []
        current_position = state.position.get(product, 0)
        available_buy_limit = self.position_limits[product] - current_position
        available_sell_limit = self.position_limits[product] + current_position

        acceptable_buy_price = self.target_prices[product] - \
            self.std_dev[product]
        acceptable_sell_price = self.target_prices[product] + \
            self.std_dev[product]

        print("Acceptable buy price for", product, ":", acceptable_buy_price)
        print("Acceptable sell price for", product, ":", acceptable_sell_price)

        # Decide on buy orders based on the sell side of the order book
        for price, amount in sorted(order_depth.sell_orders.items()):
            if price <= acceptable_buy_price:
                trade_amount = min(-amount, available_buy_limit)
                if trade_amount > 0:
                    print("BUY", product, "at", price, "for", trade_amount)
                    orders.append(Order(product, price, trade_amount))
                    available_buy_limit -= trade_amount

        # Decide on sell orders based on the buy side of the order book
        for price, amount in sorted(order_depth.buy_orders.items(), reverse=True):
            if price >= acceptable_sell_price:
                trade_amount = min(amount, available_sell_limit)
                if trade_amount > 0:
                    print("SELL", product, "at", price, "for", trade_amount)
                    orders.append(Order(product, price, -trade_amount))
                    available_sell_limit -= trade_amount

        return orders

    def update_price_memory(self, product, order_depth):
        best_ask = min(
            order_depth.sell_orders) if order_depth.sell_orders else None
        best_bid = max(
            order_depth.buy_orders) if order_depth.buy_orders else None
        if best_ask and best_bid:
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

    def calc_starfruit_orders(self, state, product="STARFRUIT"):
        order_depth = state.order_depths[product]
        self.update_price_memory(product, order_depth)
        predicted_price = self.predict_price_exponential_smoothing(product)
        if predicted_price is None:
            return []

        orders = []
        current_position = state.position.get(product, 0)
        available_buy_limit = self.position_limits[product] - current_position
        available_sell_limit = self.position_limits[product] + current_position

        # Buy orders
        for price, amount in sorted(order_depth.sell_orders.items()):
            if price <= predicted_price:
                trade_amount = min(-amount, available_buy_limit)
                if trade_amount > 0:
                    orders.append(Order(product, price, trade_amount))
                    available_buy_limit -= trade_amount

        # Sell orders
        for price, amount in sorted(order_depth.buy_orders.items(), reverse=True):
            if price >= predicted_price:
                trade_amount = min(amount, available_sell_limit)
                if trade_amount > 0:
                    orders.append(Order(product, price, -trade_amount))
                    available_sell_limit -= trade_amount

        return orders

    def run(self, state: TradingState):
        print("traderData: " + state.traderData)
        print("Observations: " + str(state.observations))
        result = {}
        result["AMETHYSTS"] = self.calc_amethysts_orders(state)
        result["STARFRUIT"] = self.calc_starfruit_orders(state)
        result["ORCHIDS"] = self.calc_orchids_orders(state)

        traderData = "SAMPLE"  # Replace with actual trader state serialization logic
        conversions = 1  # Modify this based on position and trading strategy for ORCHIDS
        # Make sure to pass the correct orders structure to the logger
        return result, conversions, traderData
