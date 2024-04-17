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
                result[product] = self.price_action_strategy(state, product)
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

    def update_thresholds(self, product):
        # Dynamically adjust thresholds based on recent price movements
        std_dev = np.std(self.price_memory[product])
        mean_price = np.mean(self.price_memory[product])
        return mean_price, std_dev * 1.5  # Adjust multiplier based on market conditions

    def update_price_memory(self, product, price):
        self.price_memory[product].append(price)
        if len(self.price_memory[product]) > 50:  # Keep last 50 prices
            self.price_memory[product].pop(0)

    def price_action_strategy(self, state, product):
        order_depth = state.order_depths[product]
        if not order_depth.sell_orders or not order_depth.buy_orders:
            return []  # No available orders to trade

        best_ask, best_ask_amount = min(
            order_depth.sell_orders.items(), key=lambda x: x[0])
        best_bid, best_bid_amount = max(
            order_depth.buy_orders.items(), key=lambda x: x[0])
        mid_price = (best_ask + best_bid) / 2

        self.update_price_memory(product, mid_price)

        # Hypothetical breakout condition: significant price drop
        recent_prices = self.price_memory[product]
        if len(recent_prices) > 5 and recent_prices[-1] < min(recent_prices[:-1]) * 0.95:
            # Buy on breakout assumption
            # Confirming price is still below recent low
            if best_ask < recent_prices[-1]:
                return [Order(product, best_ask, min(-best_ask_amount, self.position_limits[product]))]

        return []

    def momentum_strategy(self, state, product):
        # Simple momentum based on the last two prices
        if len(self.price_memory[product]) < 2:
            return []
        momentum = self.price_memory[product][-1] - \
            self.price_memory[product][-2]
        order_depth = state.order_depths[product]
        best_ask, best_ask_amount = min(
            order_depth.sell_orders.items(), key=lambda x: x[0])
        best_bid, best_bid_amount = max(
            order_depth.buy_orders.items(), key=lambda x: x[0])

        orders = []
        if momentum > 0 and best_ask < self.price_memory[product][-1]:
            orders.append(
                Order(product, best_ask, min(-best_ask_amount, self.position_limits[product])))
        elif momentum < 0 and best_bid > self.price_memory[product][-1]:
            orders.append(Order(product, best_bid, -
                                min(best_bid_amount, self.position_limits[product])))

        return orders

    def safe_get_min_order(self, orders):
        try:
            return min(orders.items(), key=lambda x: x[0])
        except ValueError:
            return (float('inf'), 0)

    def safe_get_max_order(self, orders):
        try:
            return max(orders.items(), key=lambda x: x[0])
        except ValueError:
            return (0, 0)

    def adjust_thresholds_based_on_activity(self, product, base_threshold):
        # Reduce threshold if no trades were made recently
        if len(self.price_memory[product]) > 0 and all(x == self.price_memory[product][0] for x in self.price_memory[product]):
            return base_threshold * 0.5  # Reduce threshold by 50%
        return base_threshold

    def breakout_strategy(self, state, product):
        order_depth = state.order_depths[product]
        best_ask, best_ask_amount = self.safe_get_min_order(
            order_depth.sell_orders)
        best_bid, best_bid_amount = self.safe_get_max_order(
            order_depth.buy_orders)

        if best_ask == float('inf') or best_bid == 0:
            return []  # No valid orders to trade on

        mid_price = (best_ask + best_bid) / 2
        self.update_price_memory(product, mid_price)

        average_price = np.mean(self.price_memory[product])
        std_dev = np.std(self.price_memory[product])
        threshold = 2 * std_dev  # Adjustable based on backtest results

        orders = []
        if best_ask < average_price - threshold:
            orders.append(
                Order(product, best_ask, min(-best_ask_amount, self.position_limits[product])))
        if best_bid > average_price + threshold:
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
