from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List, Dict
import numpy as np


class Trader:

    def __init__(self):
        self.position_limits = {
            'CHOCOLATE': 250, 'STRAWBERRIES': 350, 'ROSES': 60, 'GIFT_BASKET': 60
        }
        self.price_memory = {product: [] for product in self.position_limits}
        self.moving_averages = {product: []
                                for product in self.position_limits}
        self.std_dev_threshold = {
            'CHOCOLATE': 10, 'STRAWBERRIES': 20, 'ROSES': 50, 'GIFT_BASKET': 100
        }

    def run(self, state: TradingState):
        result = {}
        for product in state.order_depths:
            if product == 'CHOCOLATE':
                result[product] = self.mean_reversion_strategy(state, product)
            elif product == 'STRAWBERRIES':
                result[product] = self.momentum_strategy(state, product)
            elif product == 'ROSES':
                result[product] = self.breakout_strategy(state, product)
            elif product == 'GIFT_BASKET':
                result[product] = self.arbitrage_and_trend_strategy(
                    state, product)
        traderData = "State info for next round"  # Example placeholder
        conversions = 1
        return result, conversions, traderData

    def update_price_memory(self, product, price):
        self.price_memory[product].append(price)
        if len(self.price_memory[product]) > 50:  # Keep last 50 prices
            self.price_memory[product].pop(0)

    def mean_reversion_strategy(self, state, product):
        order_depth = state.order_depths[product]
        best_ask, best_ask_amount = min(
            order_depth.sell_orders.items(), key=lambda x: x[0])
        best_bid, best_bid_amount = max(
            order_depth.buy_orders.items(), key=lambda x: x[0])
        mid_price = (best_ask + best_bid) / 2
        self.update_price_memory(product, mid_price)

        average_price = np.mean(self.price_memory[product])
        std_dev = np.std(self.price_memory[product])

        # Buy if the price is significantly lower than the average, sell if significantly higher
        orders = []
        if best_ask < average_price - std_dev * self.std_dev_threshold[product]:
            orders.append(
                Order(product, best_ask, min(-best_ask_amount, self.position_limits[product])))
        if best_bid > average_price + std_dev * self.std_dev_threshold[product]:
            orders.append(Order(product, best_bid, -
                          min(best_bid_amount, self.position_limits[product])))

        return orders

    def momentum_strategy(self, state, product):
        order_depth = state.order_depths[product]
        best_ask, best_ask_amount = min(
            order_depth.sell_orders.items(), key=lambda x: x[0])
        best_bid, best_bid_amount = max(
            order_depth.buy_orders.items(), key=lambda x: x[0])
        mid_price = (best_ask + best_bid) / 2
        self.update_price_memory(product, mid_price)

        if len(self.price_memory[product]) < 2:
            return []  # Not enough data to determine momentum

        # Calculate momentum as the difference between the last two mid prices
        momentum = self.price_memory[product][-1] - \
            self.price_memory[product][-2]
        orders = []
        # Price is rising
        if momentum > 0 and best_ask < self.price_memory[product][-1]:
            orders.append(
                Order(product, best_ask, min(-best_ask_amount, self.position_limits[product])))
        # Price is falling
        elif momentum < 0 and best_bid > self.price_memory[product][-1]:
            orders.append(Order(product, best_bid, -
                                min(best_bid_amount, self.position_limits[product])))

        return orders

    def breakout_strategy(self, state, product):
        order_depth = state.order_depths[product]
        best_ask, best_ask_amount = min(
            order_depth.sell_orders.items(), key=lambda x: x[0])
        best_bid, best_bid_amount = max(
            order_depth.buy_orders.items(), key=lambda x: x[0])
        mid_price = (best_ask + best_bid) / 2
        self.update_price_memory(product, mid_price)

        average_price = np.mean(self.price_memory[product])
        std_dev = np.std(self.price_memory[product])
        # Define how large a price move must be to consider it a breakout
        threshold = 2 * std_dev

        orders = []
        if best_ask < average_price - threshold:  # Breakdown
            orders.append(
                Order(product, best_ask, min(-best_ask_amount, self.position_limits[product])))
        elif best_bid > average_price + threshold:  # Breakout
            orders.append(Order(product, best_bid, -
                                min(best_bid_amount, self.position_limits[product])))

        return orders

    def arbitrage_and_trend_strategy(self, state, product):
        component_prices = {'CHOCOLATE': None,
                            'STRAWBERRIES': None, 'ROSES': None}
        for comp in component_prices:
            if comp in state.order_depths:
                comp_ask, _ = min(
                    state.order_depths[comp].sell_orders.items(), key=lambda x: x[0])
                component_prices[comp] = comp_ask

        if all(component_prices.values()):  # All components have valid prices
            sum_components = sum(component_prices.values())
            basket_ask, basket_ask_amount = min(
                state.order_depths[product].sell_orders.items(), key=lambda x: x[0])
            basket_bid, basket_bid_amount = max(
                state.order_depths[product].buy_orders.items(), key=lambda x: x[0])

            orders = []
            if basket_ask < sum_components:  # Arbitrage: Basket is cheaper than components
                orders.append(Order(
                    product, basket_ask, min(-basket_ask_amount, self.position_limits[product])))
            elif basket_bid > sum_components:  # Arbitrage: Basket is more expensive than components
                orders.append(Order(product, basket_bid, -
                                    min(basket_bid_amount, self.position_limits[product])))

            # Add trend following for additional safety
            mid_price = (basket_ask + basket_bid) / 2
            self.update_price_memory(product, mid_price)
            average_price = np.mean(self.price_memory[product])
            if basket_ask < average_price:
                orders.append(Order(
                    product, basket_ask, min(-basket_ask_amount, self.position_limits[product])))
            elif basket_bid > average_price:
                orders.append(Order(product, basket_bid, -
                                    min(basket_bid_amount, self.position_limits[product])))

        return orders
