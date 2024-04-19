from datamodel import OrderDepth, UserId, TradingState, Order, ConversionObservation
from typing import List, Dict
import numpy as np


class Trader:

    def __init__(self):
        # Position limits and other configurations specific to Orchids
        self.target_prices = {'ORCHIDS': 1200}  # Example target price
        self.position_limits = {'ORCHIDS': 100}
        self.price_memory = {'ORCHIDS': []}
        self.memory_length = 20
        self.smoothing_factor = 0.2  # For exponential smoothing
        self.sunlight_threshold = 2500 * 7  # Example threshold for sunlight hours
        self.humidity_optimal_range = (60, 80)

    def update_price_memory(self, product, price):
        self.price_memory[product].append(price)
        if len(self.price_memory[product]) > self.memory_length:
            self.price_memory[product].pop(0)

    def predict_price(self, product):
        """ Simple exponential smoothing to predict the next price. """
        prices = self.price_memory[product]
        if not prices:
            return None
        smooth_price = prices[0]
        for price in prices[1:]:
            smooth_price = self.smoothing_factor * price + \
                (1 - self.smoothing_factor) * smooth_price
        return smooth_price

    def run(self, state: TradingState):
        print("traderData: " + state.traderData)
        print("Observations: " + str(state.observations))
        result = {}
        conversions = 0

        for product, order_depth in state.order_depths.items():
            if product == 'ORCHIDS':
                orders = self.trade_orchids(state, product, order_depth)
                result[product] = orders

        # Assuming traderData and conversions handling are needed
        traderData = "Updated state information"  # Modify as needed
        return result, conversions, traderData

    def trade_orchids(self, state, product, order_depth):
        # Get environmental factors
        conversion_observation = state.conversionObservations.get(product)
        sunlight = conversion_observation.sunlight if conversion_observation else 0
        humidity = conversion_observation.humidity if conversion_observation else 0

        # Adjust trading strategy based on environmental factors
        price_adjustment = self.calculate_environmental_impact(
            sunlight, humidity)
        target_price = self.target_prices[product] + price_adjustment

        # Make trading decisions
        best_ask = min(order_depth.sell_orders, default=None)
        best_bid = max(order_depth.buy_orders, default=None)
        self.update_price_memory(
            product, (best_ask + best_bid) / 2 if best_ask and best_bid else 0)
        predicted_price = self.predict_price(product)

        orders = []
        if best_ask and best_ask < target_price:
            quantity = min(
                self.position_limits[product], order_depth.sell_orders[best_ask])
            orders.append(Order(product, best_ask, quantity))

        if best_bid and best_bid > target_price:
            quantity = min(
                self.position_limits[product], order_depth.buy_orders[best_bid])
            orders.append(Order(product, best_bid, -quantity))

        return orders

    def calculate_environmental_impact(self, sunlight, humidity):
        """ Calculate price adjustments based on environmental factors. """
        price_adjustment = 0
        # Adjust for sunlight
        if sunlight < self.sunlight_threshold:
            price_adjustment -= 4 * \
                ((self.sunlight_threshold - sunlight) / (2500 * 10))
        # Adjust for humidity
        if humidity < self.humidity_optimal_range[0] or humidity > self.humidity_optimal_range[1]:
            deviation = min(abs(humidity - self.humidity_optimal_range[0]), abs(
                humidity - self.humidity_optimal_range[1]))
            price_adjustment -= 2 * (deviation / 5)
        return price_adjustment
