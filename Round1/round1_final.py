import numpy as np
import json
from datamodel import Listing, Observation, Order, OrderDepth, ProsperityEncoder, Symbol, Trade, TradingState
from typing import Any, List


class Trader:

    def __init__(self):
        self.position_limits = {'STARFRUIT': 20, 'AMETHYSTS': 20}
        self.target_prices = {'STARFRUIT': 50, 'AMETHYSTS': 10000}
        self.std_dev = {
            'STARFRUIT': [11.717, 13.575, 32.751],
            'AMETHYSTS': [1.496, 1.479, 1.513]
        }

    def run(self, state: TradingState):
        print("traderData: " + state.traderData)
        print("Observations: " + str(state.observations))
        result = {}
        for product in state.order_depths:
            order_depth: OrderDepth = state.order_depths[product]
            orders: List[Order] = []
            net_position_change = 0
            # Calculate acceptable price based on standard deviation and target price
            acceptable_buy_price = self.target_prices[product] - \
                self.std_dev[product][0]
            acceptable_sell_price = self.target_prices[product] + \
                self.std_dev[product][0]

            print("Acceptable buy price for",
                  product, ":", acceptable_buy_price)
            print("Acceptable sell price for",
                  product, ":", acceptable_sell_price)

            current_position = state.position.get(product, 0)
            available_buy_limit = self.position_limits[product] - \
                current_position
            available_sell_limit = self.position_limits[product] + \
                current_position

            for price, amount in sorted(order_depth.sell_orders.items()):
                if price <= acceptable_buy_price:
                    # Calculate potential trade amount without exceeding the position limit
                    trade_amount = min(-amount, available_buy_limit -
                                       net_position_change)
                    if trade_amount > 0:
                        print("BUY", product, "at", price, "for", trade_amount)
                        orders.append(Order(product, price, trade_amount))
                        net_position_change += trade_amount

            for price, amount in sorted(order_depth.buy_orders.items(), reverse=True):
                if price >= acceptable_sell_price:
                    # Calculate potential trade amount without exceeding the position limit
                    trade_amount = min(amount, available_sell_limit -
                                       abs(net_position_change))
                    if trade_amount > 0:
                        print("SELL", product, "at",
                              price, "for", trade_amount)
                        orders.append(Order(product, price, -trade_amount))
                        net_position_change -= trade_amount

            result[product] = orders

        # The Trader state is a simple string in this example.
        # In a full implementation, you might serialize the current Trader state
        # including any pending orders, positions, etc.
        traderData = "SAMPLE"

        # The number of conversions to make. This is a placeholder value.
        conversions = 1
        return result, conversions, traderData
