import numpy as np
from datamodel import Order, Symbol, TradingState
from typing import Any, List


class Trader:

    def __init__(self):
        # target prices are initially set for demonstration and will be adjusted dynamically based on environmental factors
        self.target_prices = {'STARFRUIT': 5039.5,
                              'AMETHYSTS': 10000, 'ORCHIDS': 5000}
        self.position_limits = {'STARFRUIT': 20,
                                'AMETHYSTS': 20, 'ORCHIDS': 100}
        self.memory_length = 20  # Memory length for price memory
        self.price_memory = {"AMETHYSTS": [0]*self.memory_length, "STARFRUIT": [
            0]*self.memory_length, "ORCHIDS": [0]*self.memory_length}
        self.std_dev = {'STARFRUIT': 1.5, 'AMETHYSTS': 1.51, 'ORCHIDS': 1.5}
        self.trend = None
        self.smoothing_factor = 0.2  # Alpha for exponential smoothing

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

    def calc_orchids_orders(self, state, product="ORCHIDS"):
        conversion_obs = state.observations.conversionObservations.get(
            product, None)
        if not conversion_obs:
            return [], 0  # No conversions if no data available

        # Calculate sunlight and humidity impacts
        sunlight_hours = conversion_obs.sunlight / \
            2500  # Convert sunlight units to hours
        production_decrease = 0 if sunlight_hours >= 7 else (
            7 - sunlight_hours) * 24 * 0.04  # 4% decrease per 10 minutes below 7 hours
        humidity_effect = 1 - 0.02 * \
            (abs(conversion_obs.humidity - 70) // 5) if not (60 <=
                                                             conversion_obs.humidity <= 80) else 1

        # Adjust import and export prices based on environmental impacts
        import_cost = (conversion_obs.askPrice + conversion_obs.transportFees + max(
            conversion_obs.importTariff, 0)) * (1 - production_decrease) * humidity_effect
        export_revenue = (conversion_obs.bidPrice - conversion_obs.transportFees - max(
            conversion_obs.exportTariff, 0)) * (1 - production_decrease) * humidity_effect

        current_position = state.position.get(product, 0)
        conversions = 0

        # Decide on conversions based on adjusted costs and revenues
        if import_cost < export_revenue:
            # Buy if the adjusted import cost is less than the adjusted export revenue
            # Buy up to 10 units, not exceeding position limits
            conversions = min(
                10, self.position_limits[product] - current_position)
        elif current_position > 0 and export_revenue > import_cost:
            # Sell if there's an existing position and the adjusted export revenue is greater than the import cost
            # Sell up to the amount in current position, maximum of 10 units
            conversions = -min(10, current_position)

        return [], conversions  # Returns no orders, only conversions

    def run(self, state: TradingState):
        result = {}
        # Handle other products
        result["AMETHYSTS"] = self.calc_amethysts_orders(state)
        result["STARFRUIT"] = self.calc_starfruit_orders(state)

        # Handle ORCHIDS conversions
        _, orchids_conversions = self.calc_orchids_orders(state)

        traderData = "Updated State Information"
        # This returns the result, the total number of conversions, and updated trader data
        return result, orchids_conversions, traderData
