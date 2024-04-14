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
        orders = []

        if not conversion_obs:
            return []  # If there is no conversion data, we cannot trade

        # Calculate total costs and revenues for importing and exporting ORCHIDS
        import_cost = conversion_obs.askPrice + \
            conversion_obs.transportFees + max(conversion_obs.importTariff, 0)
        export_revenue = conversion_obs.bidPrice - \
            conversion_obs.transportFees - max(conversion_obs.exportTariff, 0)

        # Simplified decision: Buy if import cost is less than export revenue, Sell if position and export revenue is greater than import cost
        current_position = state.position.get(product, 0)

        if import_cost < export_revenue:
            # Simplified buy decision: Always buy one unit if profitable
            # Assuming '1' is a valid order quantity
            orders.append(Order(product, import_cost, 1))

        if current_position > 0 and export_revenue > import_cost:
            # Simplified sell decision: Sell one unit if profitable and position is non-zero
            orders.append(Order(product, export_revenue, -1))  # Sell one unit

        return orders

    def run(self, state: TradingState):
        result = {}
        # Process AMETHYSTS and STARFRUIT orders
        result["AMETHYSTS"] = self.calc_amethysts_orders(state)
        result["STARFRUIT"] = self.calc_starfruit_orders(state)

        # Process ORCHIDS orders
        orchids_orders = self.calc_orchids_orders(state)
        if orchids_orders:
            result["ORCHIDS"] = orchids_orders
            # Here you would handle how these orders are submitted to the market or conversion process

        # Update trader state data and conversion tracking
        traderData = "Updated State"  # Replace with your state management logic
        # Example: Counting the orders as conversions
        conversions = len(orchids_orders)

        return result, conversions, traderData
