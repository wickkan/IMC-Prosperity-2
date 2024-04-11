import numpy as np
import json
from datamodel import Listing, Observation, Order, OrderDepth, ProsperityEncoder, Symbol, Trade, TradingState
from typing import Any, List


class Trader:

    def __init__(self):
        # starfruit target price unused
        self.target_prices = {'STARFRUIT': 5039.5, 'AMETHYSTS': 10000}
        self.position_limits = {'STARFRUIT': 20, 'AMETHYSTS': 20}
        self.memory_length = 20  # to modify
        self.price_memory = {"AMETHYSTS": [
            0]*self.memory_length, "STARFRUIT": [0]*self.memory_length}
        self.std_dev = {
            'STARFRUIT': 1.5,  # to modify
            'AMETHYSTS': 1.51
        }
        self.trend = None

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
            for x in range(self.memory_length-1):
                self.price_memory[product][x] = self.price_memory[product][x+1]
            self.price_memory[product][-1] = mid_price

    def train_model(self, product):
        # Prepare data for training
        prices = np.array(self.price_memory[product])
        times = np.array(range(len(prices)))

        # Calculate the mean of the times and prices
        mean_time = np.mean(times)
        mean_price = np.mean(prices)

        # Calculate the terms needed for the numator and denominator of beta
        times_diff = times - mean_time
        prices_diff = prices - mean_price

        # Calculate beta and alpha
        beta = np.sum(times_diff * prices_diff) / np.sum(times_diff**2)
        alpha = mean_price - (beta * mean_time)

        return alpha, beta

    def calc_starfruit_orders(self, state, product="STARFRUIT"):
        order_depth = state.order_depths[product]
        orders = []
        current_position = state.position.get(product, 0)
        available_buy_limit = self.position_limits[product] - current_position
        available_sell_limit = self.position_limits[product] + current_position
        self.update_price_memory(product, order_depth)

        # Train the model and predict the future price
        alpha, beta = self.train_model(product)
        future_price = alpha + beta * len(self.price_memory[product])

        # Decide on buy orders based on the sell side of the order book
        for price, amount in sorted(order_depth.sell_orders.items()):
            if price <= future_price:
                trade_amount = min(-amount, available_buy_limit)
                if trade_amount > 0:
                    orders.append(Order(product, price, trade_amount))
                    available_buy_limit -= trade_amount

        # Decide on sell orders based on the buy side of the order book
        for price, amount in sorted(order_depth.buy_orders.items(), reverse=True):
            if price >= future_price:
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

        traderData = "SAMPLE"  # Replace with actual trader state serialization logic
        conversions = 1  # Replace with actual conversion logic
        # Make sure to pass the correct orders structure to the logger
        return result, conversions, traderData
